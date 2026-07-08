# SQL 方言转换器 — 第三阶段重构设计（AST Parser + Emitter）

## 目标

用 sqlglot AST 替代 839 行正则解析器（`sql_parser.py`），AST 遍历改写替代大部分正则规则。保留 5 步骤结构化输出格式。

### 设计目标

- sqlglot 解析 SQL 为 AST，替代正则提取
- AST 节点遍历改写类型/函数/修饰符，替代正则规则
- Phase 2 的 Canonical 映射表完全保留，应用方式从"正则替换"变为"AST 节点属性修改"
- 现有 TableBlock 数据结构和 `format_structured_output()` 不变
- 规则数从 25 降至 ~8（仅保留文本预处理和后处理）

---

## 架构

```
当前 Pipeline：
  正则规则引擎 → sql_parser(正则解析) → format_structured_output → write_output

新 Pipeline：
  sqlglot 解析 AST
    → cleanup_rules（文本预处理，仅7条正则规则保留）
    → ast_rewriter（AST 遍历：类型/函数/修饰符改写）
    → ast_collector（AST → TableBlock 列表）
    → sort_tables_by_fk（保留）
    → format_structured_output（保留）
    → write_output（保留）
```

---

## 模块设计

### 1. AST Rewriter（`converter/ast_rewriter.py`）

遍历 sqlglot AST，用 Phase 2 的 Canonical 映射表改写节点。

```python
"""AST 遍历改写引擎 — 类型/函数/修饰符替换。"""
import sqlglot.expressions as exp


def rewrite_type(type_str: str, source_dialect, target_dialect) -> str:
    """列类型名 → Canonical → 目标类型名。
    复用 Phase 2 的 type_to_canonical / canonical_to_type 映射表。"""
    # 提取基础类型名（去除 NOT NULL、DEFAULT 等修饰）
    base_type = type_str.split()[0].split("(")[0].lower()
    canonical = source_dialect.type_to_canonical.get(base_type)
    if canonical:
        target_type = target_dialect.canonical_to_type.get(canonical)
        if target_type:
            # 保留精度和约束
            return type_str.replace(base_type, target_type, 1)
    return type_str


def rewrite_function(func_name: str, source_dialect, target_dialect) -> str:
    """函数名 → Canonical → 目标函数名。
    复用 Phase 2 的 function_to_canonical / canonical_to_function 映射表。"""
    canonical = source_dialect.function_to_canonical.get(func_name.upper())
    if canonical:
        target_func = target_dialect.canonical_to_function.get(canonical)
        if target_func:
            return target_func
    return func_name


# 应删除的 MySQL 表选项
_MYSQL_TABLE_OPTIONS = {"ENGINE", "AUTO_INCREMENT", "DEFAULT CHARSET",
                        "ROW_FORMAT", "KEY_BLOCK_SIZE", "PACK_KEYS"}

# 应删除的列修饰符
_MYSQL_COL_MODIFIERS = {"UNSIGNED", "ZEROFILL", "CHARACTER SET",
                        "COLLATE", "ON UPDATE"}


def walk_and_rewrite(ast, source_dialect, target_dialect) -> exp.Expression:
    """遍历 AST，改写类型、函数、删除不兼容修饰符。"""
    for node in ast.walk():
        # 列定义：替换类型名
        if isinstance(node, exp.ColumnDef):
            for child in node.find_all(exp.DataType):
                child.this = exp.DataType.Type(
                    rewrite_type(str(child.this), source_dialect, target_dialect))
            # 删除列级修饰符
            _strip_column_modifiers(node)

        # 函数调用：替换函数名
        if isinstance(node, exp.Anonymous) or isinstance(node, exp.Func):
            new_name = rewrite_function(node.name, source_dialect, target_dialect)
            if new_name != node.name:
                node.set("this", new_name)

        # 表选项：删除 ENGINE=, CHARSET= 等
        if isinstance(node, exp.TableOption):
            for opt_name in _MYSQL_TABLE_OPTIONS:
                if opt_name.upper() in str(node).upper():
                    node.pop()

        # USING BTREE：删除
        if isinstance(node, exp.IndexColumnConstraint):
            if "BTREE" in str(node).upper():
                node.pop()

    return ast


def _strip_column_modifiers(column_def):
    """删除列定义中的 UNSIGNED/ZEROFILL/CHARACTER SET 修饰符。"""
    for child in list(column_def.find_all(exp.ColumnConstraint)):
        constraint_str = str(child).upper()
        for modifier in _MYSQL_COL_MODIFIERS:
            if modifier in constraint_str:
                child.pop()
```

### 2. AST Collector（`converter/ast_collector.py`）

从 sqlglot AST 中提取结构化信息，输出与现有 `format_structured_output()` 完全兼容的 `TableBlock` 列表。

```python
"""AST 收集器 — sqlglot AST → TableBlock 列表。"""
import sqlglot.expressions as exp
from sql_parser import TableBlock, ColumnDef, IndexDef, ForeignKeyDef, InsertBlock


def collect(ast, database: str | None = None) -> list[TableBlock]:
    """从 AST 中收集所有表定义和数据。"""
    tables: dict[str, TableBlock] = {}

    for statement in ast:
        if isinstance(statement, exp.Create):
            _collect_create(statement, tables, database)
        elif isinstance(statement, exp.Insert):
            _collect_insert(statement, tables, database)

    return list(tables.values())


def _collect_create(node, tables, database):
    """从 CREATE TABLE 节点提取 TableBlock。"""
    table_name = node.this.sql() if node.this else None
    if not table_name:
        return

    db = node.this.args.get("db") or database
    tb = TableBlock(database=db, name=table_name, comment=None)

    # 提取列
    for col in node.find_all(exp.ColumnDef):
        name = col.this.sql()
        type_ = str(col.kind) if col.kind else ""
        comment = None
        for constraint in col.find_all(exp.ColumnConstraint):
            constraint_str = str(constraint).upper()
            if "COMMENT" in constraint_str:
                comment = _extract_comment(constraint)
        tb.columns.append(ColumnDef(name=name, type_=type_, comment=comment))

    # 提取主键
    for pk in node.find_all(exp.PrimaryKey):
        for col in pk.expressions:
            tb.primary_key.append(col.sql())

    # 提取索引
    for idx in node.find_all(exp.Index):
        idx_name = idx.this.sql() if idx.this else None
        unique = "UNIQUE" in str(idx).upper()
        cols = [col.sql() for col in idx.expressions]
        tb.indexes.append(IndexDef(name=idx_name, columns=cols, unique=unique, comment=None))

    # 提取外键
    for fk in node.find_all(exp.ForeignKey):
        fk_name = fk.this.sql() if fk.this else None
        cols = [c.sql() for c in fk.expressions]
        ref_table = fk.args.get("reference").this.sql() if fk.args.get("reference") else None
        ref_cols = [c.sql() for c in fk.args.get("reference").expressions] if fk.args.get("reference") else []
        on_delete = fk.args.get("on_delete")
        on_update = fk.args.get("on_update")
        tb.foreign_keys.append(ForeignKeyDef(
            name=fk_name, columns=cols, ref_table=ref_table,
            ref_columns=ref_cols, on_delete=on_delete, on_update=on_update))

    tables[table_name] = tb


def _collect_insert(node, tables, database):
    """从 INSERT 节点提取 InsertBlock。"""
    table_name = node.this.sql() if node.this else None
    if not table_name or table_name not in tables:
        return

    tb = tables[table_name]
    insert_block = InsertBlock()
    if node.expressions:
        insert_block.columns = [col.sql() for col in node.expressions]
    for row in node.find_all(exp.Tuple):
        insert_block.values.append([val.sql() for val in row.expressions])
    tb.inserts.append(insert_block)
```

### 3. Pipeline 集成

```python
# convert.py convert() 函数
def convert(text, source_mode, target_mode, database=None):
    source_dialect = get_dialect(source_mode, database)
    target_dialect = get_dialect(target_mode, database)

    # 阶段1: 文本预处理（cleanup 正则规则，不变）
    text, counters = _pipeline.run_cleanup(text, source_dialect, target_dialect)

    # 阶段2: sqlglot 解析
    asts = sqlglot.parse(text, read=source_mode)

    # 阶段3: AST 改写
    for ast in asts:
        walk_and_rewrite(ast, source_dialect, target_dialect)

    # 阶段4: AST 收集
    tables = collect_from_asts(asts, database)

    # 阶段5-7: 保留
    tables = sort_tables_by_fk(tables)
    text = format_structured_output(tables, target_dialect)
    return text, counters
```

---

## 文件变化

```
新建:
  converter/ast_rewriter.py       # AST 遍历改写引擎
  converter/ast_collector.py      # AST → TableBlock 收集器

修改:
  convert.py                      # 更新 convert() 调用链
  sql_parser.py                   # 删除 parse_tables() 和所有正则常量，
                                   # 仅保留 sort_tables_by_fk() 和数据结构

删除:
  converter/rules/identifier.py   # 引号处理 → sqlglot 原生
  converter/rules/modifier.py     # 修饰符清理 → AST 改写
  converter/rules/constraint.py   # 约束适配 → AST 改写

保留:
  converter/rules/cleanup.py      # 7条文本预处理规则
  converter/rules/postprocess.py  # 1条后处理规则
  converter/mappings/types.py     # Canonical 类型映射表（AST 改写使用）
  converter/mappings/functions.py # Canonical 函数映射表（AST 改写使用）
  converter/dialects/*.py         # 方言策略类（不变）
  converter/pipeline.py           # 保留（run_cleanup 部分）
  converter/registry.py           # 不变
```

---

## 规则数变化

| | Phase 2 | Phase 3 | 变化 |
|---|---|---|---|
| cleanup.py | 7 | 7 | 保留 |
| identifier.py | 2 | **0** | 删除 |
| modifier.py | 12 | **0** | 删除 |
| constraint.py | 3 | **0** | 删除 |
| postprocess.py | 1 | 1 | 保留 |
| **总计** | **25** | **8** | |

---

## 依赖

- `sqlglot`：纯 Python，无 C 依赖，`pip install sqlglot`

---

## 验证标准

- 所有现有测试通过
- MySQL→Kingbase、MySQL→PGSQL、Oracle→PGSQL、MySQL→SQLite 端到端与 Phase 2 一致
- 能正确解析和改写含子查询、CTE、窗口函数的 SQL
- `sql_parser.py` 从 839 行大幅缩减