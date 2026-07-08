# SQL 方言转换器 — 第一阶段重构设计

## 目标

将当前基于 `source_mode / target_mode` 规则组合的转换器，重构为 **Dialect + Capability + Rule Engine** 架构（第一阶段）。

### 设计目标

- 新增数据库时，规则无需修改（仅新增 Dialect）
- 规则从 O(N²) 降低到接近 O(N)
- 规则按 Pipeline 阶段拆分，避免冲突
- 保留 Regex 作为规则执行引擎，不引入 AST

### 当前状态

| 指标 | 数值 |
|---|---|
| 文件数 | 10 个 .py |
| 代码行数 | ~2963 行 |
| 规则数 | 86 条（`rules.py` 991 行） |
| 方言数 | 4 个（mysql, kingbase, pgsql, sqlite） |
| 痛点 | 同一条规则因 target 不同重复 2-3 份 |

---

## 架构

```
                SQL Input
                    │
              SQL Parser（不变）
                    │
             Pipeline Engine（新增）
                    │
     ┌──────────────┼──────────────┐
     │              │              │
  Dialect       Capability       Rules
  自我描述       能力标签         按阶段拆分
     │              │              │
     └──────────────┼──────────────┘
                    │
               SQL Output
```

### 核心概念

**Dialect**：每个数据库只描述自身能力，不关心其他数据库。

**Capability**：数据库特性标签（如 `engine`、`unsigned`、`enum`）。规则通过 Capability 判断是否需要执行。

**Rule**：源方言有某 Capability，目标方言没有 → 执行规则。不再需要 `source_mode` / `target_mode` 列表。

**Pipeline**：规则按阶段顺序执行，避免阶段间冲突。

---

## 目录结构

```
d:\plugin\sql_convert\
  convert.py              # CLI 入口（不变，调用链更新）
  sql_parser.py           # SQL 解析器（不变）
  tests/                  # 测试（不变）

  converter/              # 新建子包
    __init__.py
    registry.py           # 方言注册表 + 工厂函数
    capabilities.py       # Capability 枚举定义
    pipeline.py           # Pipeline 编排器

    dialects/             # 从 ../dialects/ 迁移
      __init__.py
      base.py
      mysql.py
      kingbase.py
      pgsql.py
      sqlite.py

    rules/                # 从 ../rules.py 拆分
      __init__.py         # 汇总导出
      cleanup.py          # 阶段1: 预处理清理
      identifier.py       # 阶段2: 标识符转换
      type_mapping.py     # 阶段3: 类型映射
      modifier.py         # 阶段4: 修饰符清理
      constraint.py       # 阶段5: 约束/索引适配
      postprocess.py      # 阶段6: 后处理

    mappings/             # 第二阶段预留（Canonical Type）
      __init__.py
```

### 删除的文件

- `dialects/` → 迁移到 `converter/dialects/`
- `rules.py` → 拆分为 `converter/rules/*.py`

---

## 模块设计

### 1. Dialect（`converter/dialects/`）

每个方言继承 `BaseDialect`，声明 `family` 和 `capabilities`。

```python
class BaseDialect:
    family: str = ""         # 家族标识: mysql, pg, oracle, sqlite
    identifier_quote: str    # 标识符包围符
    capabilities: set[str]   # 该方言支持的能力

    # 格式化方法（不变）
    def format_drop_table(self, table) -> str
    def format_create_table(self, table) -> str
    def format_indexes(self, table) -> list[str]
    def format_foreign_keys(self, table) -> list[str]
    def format_inserts(self, table) -> list[str]
    def write_output(self, sql_text, output_path) -> str
```

#### 方言能力声明示例

```python
# MysqlDialect
class MysqlDialect(BaseDialect):
    family = "mysql"
    identifier_quote = "`"
    capabilities = {
        "engine", "charset", "collate", "unsigned", "zerofill",
        "auto_increment", "enum", "set", "bit_type",
        "on_update_current_timestamp", "delimiter",
        "lock_tables", "session_vars", "foreign_key_checks",
        "using_btree", "row_format",
        "type_tinyint", "type_mediumint", "type_int_display_width",
        "type_bigint_display_width", "type_tinytext", "type_mediumtext",
        "type_longtext", "type_blob", "type_datetime", "type_year",
        "type_double", "type_float", "type_enum", "type_set",
    }

# PgsqlDialect
class PgsqlDialect(BaseDialect):
    family = "pg"
    identifier_quote = '"'
    capabilities = {
        "serial", "bigserial", "boolean", "bytea",
        "timestamp", "text", "double_precision",
        "cascade", "pg_type_cast", "extension",
        "comment_on", "returning", "ilike",
    }

# SqliteDialect
class SqliteDialect(BaseDialect):
    family = "sqlite"
    identifier_quote = '"'
    capabilities = {
        "autoincrement",  # 注意：连写，非 auto_increment
        "blob",
    }
```

### 2. Capability（`converter/capabilities.py`）

Capability 是纯字符串标签，枚举所有已知的数据库能力。不做逻辑判断，只做标签匹配。

```python
# 语法能力
CAP_ENGINE = "engine"
CAP_CHARSET = "charset"
CAP_COLLATE = "collate"
CAP_UNSIGNED = "unsigned"
CAP_ZEROFILL = "zerofill"
CAP_AUTO_INCREMENT = "auto_increment"
CAP_ENUM = "enum"
CAP_SET = "set"
CAP_CASCADE = "cascade"
# ... 等
```

### 3. Rule Engine（`converter/pipeline.py` + `converter/rules/`）

#### 规则定义

```python
@dataclass
class Rule:
    name: str
    capability: str           # 依赖的能力标签
    action: str               # "remove" | "replace" | "transform"
    pattern: re.Pattern
    replacement: str = ""     # remove/replace 时使用
    scope: str = "line"       # "global" | "line"
    skip_insert: bool = True
    desc: str = ""
```

#### 规则匹配逻辑

```python
def rule_applies(rule: Rule, source: BaseDialect, target: BaseDialect) -> bool:
    """源有该能力，目标没有 → 规则生效"""
    return (
        rule.capability in source.capabilities
        and rule.capability not in target.capabilities
    )
```

#### Pipeline 执行

```python
class Pipeline:
    stages: list[list[Rule]]  # 按阶段组织的规则列表

    def run(self, text: str, source: BaseDialect, target: BaseDialect):
        for stage in self.stages:
            for rule in stage:
                if rule_applies(rule, source, target):
                    text = apply_rule(text, rule)
        return text
```

#### 规则按阶段拆分

| 阶段 | 文件 | 典型规则 |
|---|---|---|
| 1. cleanup | `rules/cleanup.py` | strip_version_comment, strip_lock_tables, normalize_delimiter, strip_session_vars, strip_set_names, strip_foreign_key_checks |
| 2. identifier | `rules/identifier.py` | convert_backtick_quote, convert_double_quote_to_backtick |
| 3. type_mapping | `rules/type_mapping.py` | convert_tinyint_type, convert_mediumint_type, convert_datetime_type, convert_blob_types, convert_enum_type, convert_varchar2_type, convert_serial_type... |
| 4. modifier | `rules/modifier.py` | strip_unsigned, strip_zerofill, strip_engine_clause, strip_default_charset, strip_collate_standalone, strip_on_update_timestamp, strip_cascade, strip_table_auto_increment, strip_row_format, strip_column_charset |
| 5. constraint | `rules/constraint.py` | strip_using_btree, convert_bit_type, convert_bit_literal, strip_pg_extension, convert_pg_type_cast |
| 6. postprocess | `rules/postprocess.py` | strip_oracle_hints, fix_autoincrement_syntax |

### 4. Registry（`converter/registry.py`）

```python
# 方言注册表
_REGISTRY: dict[str, type[BaseDialect]] = {}

def register(dialect_cls: type[BaseDialect]):
    _REGISTRY[dialect_cls.__name__.lower()] = dialect_cls

def get_dialect(mode: str, database: str | None = None) -> BaseDialect:
    # 支持别名: pgsql/postgresql/postgres → PgsqlDialect
    ...

# 各方言文件末尾自动注册
# dialects/mysql.py 末尾: register(MysqlDialect)
```

### 5. Pipeline 阶段（`converter/pipeline.py`）

顺序执行，前阶段输出是后阶段输入：

```
1. cleanup      → 删除源方言特有的注释/锁表/会话变量/DELIMITER
2. identifier   → 标识符引号转换（反引号 ↔ 双引号）
3. type_mapping → 类型名替换（依赖 Capability 判断）
4. modifier     → 修饰符删除（UNSIGNED, ENGINE, CHARSET...）
5. constraint   → 约束/索引语法适配（USING BTREE, b'0'...）
6. postprocess  → 最终清理（Oracle hints, AUTOINCREMENT 语法修正）
```

---

## 调用链变更

### 旧调用链

```python
convert.py main()
  → filter_rules(source_mode, target_mode)  # 按 source/target 列表过滤
  → apply_global_rules() / apply_line_rules()
  → parse_tables()
  → format_structured_output()
  → write_output()
```

### 新调用链

```python
convert.py main()
  → registry.get_dialect(source_mode)
  → registry.get_dialect(target_mode)
  → pipeline.run(text, source_dialect, target_dialect)
  → parse_tables()                          # 不变
  → format_structured_output()              # 不变
  → target_dialect.write_output()           # 不变
```

---

## 迁移计划

### 步骤

1. 创建 `converter/` 目录结构
2. 迁移 `dialects/` → `converter/dialects/`，添加 `family` + `capabilities`
3. 创建 `converter/capabilities.py`（Capability 常量）
4. 创建 `converter/registry.py`（方言注册表）
5. 拆分 `rules.py` → `converter/rules/*.py`，规则改用 Capability
6. 创建 `converter/pipeline.py`
7. 更新 `convert.py` 调用链
8. 删除旧 `dialects/`、`rules.py`
9. 更新测试，验证端到端无差异

### 验证标准

- 所有现有测试通过
- MySQL→Kingbase、MySQL→PGSQL、MySQL→SQLite、Oracle→PGSQL 端到端输出与重构前一致

---

## 收益

| 项目 | 旧方案 | 新方案 |
|---|---|---|
| 新增数据库 | 修改大量规则 + 可能重复 | 新增 Dialect，声明 capabilities |
| 规则数量 | 86 条，持续增长 | 预估 ~40 条，基本稳定 |
| 规则重复 | 同一规则按 target 重复 2-3 份 | 无重复，按 Capability 自动匹配 |
| 扩展性 | O(N²) | 接近 O(N) |
| 文件规模 | `rules.py` 991 行 | 6 个文件，每个 ~50-100 行 |