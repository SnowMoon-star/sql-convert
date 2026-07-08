# SQL 方言转换器 — 第一阶段重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前基于 `source_mode/target_mode` 规则组合的转换器重构为 Dialect + Capability + Rule Engine 架构

**Architecture:** 每个方言声明自身 capabilities（能力标签），规则通过 capability 判断"源有、目标无 → 执行"。规则按 6 个 Pipeline 阶段拆分到独立文件。新增数据库只需新增 Dialect 并声明 capabilities，无需改规则。

**Tech Stack:** Python 3.10+, dataclasses, re, sqlite3, pathlib, unittest

## Global Constraints

- 保留 Regex 作为规则执行引擎，不引入 AST
- 所有现有测试必须通过
- 端到端转换输出与重构前一致
- 新增数据库时规则文件无需修改（仅新增 Dialect）

---

## File Structure

创建或修改的文件一览：

```
Create: converter/__init__.py
Create: converter/capabilities.py
Create: converter/registry.py
Create: converter/pipeline.py
Create: converter/dialects/__init__.py
Create: converter/dialects/base.py         (从 dialects/base.py 迁移)
Create: converter/dialects/mysql.py        (从 dialects/mysql.py 迁移)
Create: converter/dialects/kingbase.py     (从 dialects/kingbase.py 迁移)
Create: converter/dialects/pgsql.py        (从 dialects/pgsql.py 迁移)
Create: converter/dialects/sqlite.py       (从 dialects/sqlite.py 迁移)
Create: converter/rules/__init__.py
Create: converter/rules/cleanup.py
Create: converter/rules/identifier.py
Create: converter/rules/type_mapping.py
Create: converter/rules/modifier.py
Create: converter/rules/constraint.py
Create: converter/rules/postprocess.py
Create: converter/mappings/__init__.py     (第二阶段预留，空文件)
Modify: convert.py                         (更新导入和调用链)
Delete: dialects/                          (迁移后删除旧目录)
Delete: rules.py                           (拆分后删除旧文件)
Modify: tests/test_sniff.py                (更新导入路径)
```

---

### Task 1: 创建目录结构和空包文件

**Files:**
- Create: `converter/__init__.py`
- Create: `converter/mappings/__init__.py`
- Create: `converter/rules/__init__.py`
- Create: `converter/dialects/__init__.py`

- [ ] **Step 1: 创建 converter 目录和空包**

```bash
mkdir -p converter/dialects converter/rules converter/mappings
```

- [ ] **Step 2: 创建空 __init__.py 文件**

```bash
touch converter/__init__.py converter/mappings/__init__.py converter/rules/__init__.py converter/dialects/__init__.py
```

- [ ] **Step 3: 验证 Python 可以导入新包**

```bash
python -c "import converter; print('converter imported OK')"
python -c "from converter import dialects; print('dialects imported OK')"
python -c "from converter import rules; print('rules imported OK')"
python -c "from converter import mappings; print('mappings imported OK')"
```

- [ ] **Step 4: 提交**

```bash
git add converter/
git commit -m "feat: create converter/ directory structure"
```

---

### Task 2: 创建 converter/capabilities.py

**Files:**
- Create: `converter/capabilities.py`

**Interfaces:**
- Produces: 所有 Capability 字符串常量，供 Dialect 和 Rule 引用

- [ ] **Step 1: 编写 capabilities.py**

```python
"""数据库能力标签常量。

每个能力代表一个数据库特性。Dialect 声明自己支持哪些能力，
Rule 通过能力匹配决定是否执行（源有、目标无 → 执行）。
"""

# ── 语法 / 语句能力 ──
CAP_ENGINE = "engine"
CAP_CHARSET = "charset"
CAP_COLLATE = "collate"
CAP_UNSIGNED = "unsigned"
CAP_ZEROFILL = "zerofill"
CAP_AUTO_INCREMENT = "auto_increment"
CAP_ENUM = "enum"
CAP_SET = "set"
CAP_CASCADE = "cascade"
CAP_DELIMITER = "delimiter"
CAP_LOCK_TABLES = "lock_tables"
CAP_SESSION_VARS = "session_vars"
CAP_FOREIGN_KEY_CHECKS = "foreign_key_checks"
CAP_USING_BTREE = "using_btree"
CAP_ROW_FORMAT = "row_format"
CAP_ON_UPDATE_TIMESTAMP = "on_update_current_timestamp"
CAP_VERSION_COMMENT = "version_comment"
CAP_ORACLE_HINTS = "oracle_hints"

# ── 标识符能力 ──
CAP_BACKTICK_QUOTE = "backtick_quote"       # MySQL 反引号
CAP_DOUBLE_QUOTE = "double_quote"           # PG/Kingbase/SQLite 双引号

# ── 类型能力 ──
CAP_TYPE_TINYINT = "type_tinyint"
CAP_TYPE_MEDIUMINT = "type_mediumint"
CAP_TYPE_INT_DISPLAY_WIDTH = "type_int_display_width"
CAP_TYPE_BIGINT_DISPLAY_WIDTH = "type_bigint_display_width"
CAP_TYPE_SMALLINT_DISPLAY_WIDTH = "type_smallint_display_width"
CAP_TYPE_INTEGER_DISPLAY_WIDTH = "type_integer_display_width"
CAP_TYPE_TINYTEXT = "type_tinytext"
CAP_TYPE_MEDIUMTEXT = "type_mediumtext"
CAP_TYPE_LONGTEXT = "type_longtext"
CAP_TYPE_TEXT = "type_text"
CAP_TYPE_BLOB = "type_blob"
CAP_TYPE_DATETIME = "type_datetime"
CAP_TYPE_TIMESTAMP = "type_timestamp"
CAP_TYPE_YEAR = "type_year"
CAP_TYPE_DOUBLE = "type_double"
CAP_TYPE_FLOAT = "type_float"
CAP_TYPE_ENUM = "type_enum"
CAP_TYPE_SET = "type_set"
CAP_TYPE_BIT = "type_bit"
CAP_TYPE_BIT_LITERAL = "type_bit_literal"
CAP_TYPE_VARCHAR2 = "type_varchar2"
CAP_TYPE_NVARCHAR2 = "type_nvarchar2"
CAP_TYPE_NUMBER = "type_number"
CAP_TYPE_CLOB = "type_clob"
CAP_TYPE_NCLOB = "type_nclob"
CAP_TYPE_BLOB_ORACLE = "type_blob_oracle"
CAP_TYPE_LONG = "type_long"
CAP_TYPE_LONG_RAW = "type_long_raw"
CAP_TYPE_RAW = "type_raw"
CAP_TYPE_NCHAR = "type_nchar"
CAP_TYPE_ORACLE_DATE = "type_oracle_date"
CAP_TYPE_SERIAL = "type_serial"
CAP_TYPE_BIGSERIAL = "type_bigserial"
CAP_TYPE_BOOLEAN = "type_boolean"
CAP_TYPE_BYTEA = "type_bytea"
CAP_TYPE_DOUBLE_PRECISION = "type_double_precision"
CAP_TYPE_PG_TYPE_CAST = "type_pg_type_cast"
CAP_TYPE_EXTENSION = "type_extension"
CAP_TYPE_AUTOINCREMENT = "type_autoincrement"
```

- [ ] **Step 2: 验证导入**

```bash
python -c "from converter.capabilities import CAP_ENGINE, CAP_UNSIGNED; print(CAP_ENGINE, CAP_UNSIGNED)"
```

- [ ] **Step 3: 提交**

```bash
git add converter/capabilities.py
git commit -m "feat: add Capability constants for all database features"
```

---

### Task 3: 创建 converter/registry.py

**Files:**
- Create: `converter/registry.py`

**Interfaces:**
- Produces: `register(dialect_cls)` 函数, `get_dialect(mode, database=None) -> BaseDialect` 函数

- [ ] **Step 1: 编写 registry.py**

```python
"""方言注册表 — 工厂函数 + 别名映射。"""
from __future__ import annotations
from converter.dialects.base import BaseDialect

# 方言名 → 类
_REGISTRY: dict[str, type[BaseDialect]] = {}
# 别名 → 方言名
_ALIASES: dict[str, str] = {}


def register(dialect_cls: type[BaseDialect]) -> type[BaseDialect]:
    """装饰器：注册方言类。"""
    name = dialect_cls.__name__.replace("Dialect", "").lower()
    _REGISTRY[name] = dialect_cls
    return dialect_cls


def register_alias(alias: str, target: str) -> None:
    """注册别名，如 pgsql → postgresql。"""
    _ALIASES[alias] = target


def get_dialect(mode: str, database: str | None = None) -> BaseDialect:
    """根据模式名获取方言实例。"""
    key = mode.lower()
    key = _ALIASES.get(key, key)
    if key not in _REGISTRY:
        raise ValueError(f"Unsupported dialect mode: {mode}")
    return _REGISTRY[key](database)


# 别名注册
register_alias("pgsql", "pgsql")
register_alias("postgresql", "pgsql")
register_alias("postgres", "pgsql")
register_alias("sqlite3", "sqlite")
register_alias("pg", "pgsql")
```

- [ ] **Step 2: 验证导入（此时 dialect 类尚未迁移，预期报错）**

```bash
python -c "from converter.registry import register, get_dialect; print('registry imported OK')"
```

- [ ] **Step 3: 提交**

```bash
git add converter/registry.py
git commit -m "feat: add dialect registry with alias support"
```

---

### Task 4: 迁移方言到 converter/dialects/，添加 family + capabilities

**Files:**
- Create: `converter/dialects/base.py` (从 `dialects/base.py` 迁移)
- Create: `converter/dialects/mysql.py` (从 `dialects/mysql.py` 迁移)
- Create: `converter/dialects/kingbase.py` (从 `dialects/kingbase.py` 迁移)
- Create: `converter/dialects/pgsql.py` (从 `dialects/pgsql.py` 迁移)
- Create: `converter/dialects/sqlite.py` (从 `dialects/sqlite.py` 迁移)

**Interfaces:**
- Produces: `BaseDialect` 基类（含 `family`, `identifier_quote`, `capabilities` 属性），4 个方言子类

- [ ] **Step 1: 迁移 base.py，添加 family + identifier_quote 属性**

复制 `dialects/base.py` → `converter/dialects/base.py`，在 `__init__` 上方添加类属性：

```python
from __future__ import annotations
from sql_parser import TableBlock


class BaseDialect:
    """SQL 方言抽象策略基类。"""

    # 子类必须覆盖
    family: str = ""              # 家族: mysql, pg, oracle, sqlite
    identifier_quote: str = '"'   # 标识符包围符
    capabilities: set[str] = set()  # 该方言支持的能力标签

    def __init__(self, database: str | None = None):
        self.database = database

    # ... 其余方法保持不变 ...
    # (quote_identifier, format_table_label, escape_comment,
    #  format_drop_table, format_create_table, format_indexes,
    #  format_foreign_keys, format_inserts, write_output)
```

> 注：将 `dialects/base.py` 的完整内容复制到新文件，在 `class BaseDialect:` 下添加 `family`, `identifier_quote`, `capabilities` 三个类属性。

- [ ] **Step 2: 迁移 mysql.py，添加 capabilities**

```python
from __future__ import annotations
from converter.dialects.base import BaseDialect
from converter.capabilities import (
    CAP_ENGINE, CAP_CHARSET, CAP_COLLATE, CAP_UNSIGNED, CAP_ZEROFILL,
    CAP_AUTO_INCREMENT, CAP_ENUM, CAP_SET,
    CAP_ON_UPDATE_TIMESTAMP, CAP_DELIMITER, CAP_LOCK_TABLES,
    CAP_SESSION_VARS, CAP_FOREIGN_KEY_CHECKS, CAP_USING_BTREE,
    CAP_ROW_FORMAT, CAP_VERSION_COMMENT, CAP_BACKTICK_QUOTE,
    CAP_TYPE_TINYINT, CAP_TYPE_MEDIUMINT, CAP_TYPE_INT_DISPLAY_WIDTH,
    CAP_TYPE_BIGINT_DISPLAY_WIDTH, CAP_TYPE_SMALLINT_DISPLAY_WIDTH,
    CAP_TYPE_INTEGER_DISPLAY_WIDTH, CAP_TYPE_TINYTEXT, CAP_TYPE_MEDIUMTEXT,
    CAP_TYPE_LONGTEXT, CAP_TYPE_BLOB, CAP_TYPE_DATETIME, CAP_TYPE_YEAR,
    CAP_TYPE_DOUBLE, CAP_TYPE_FLOAT, CAP_TYPE_ENUM, CAP_TYPE_SET,
    CAP_TYPE_BIT, CAP_TYPE_BIT_LITERAL,
)
from converter.registry import register
from sql_parser import TableBlock


@register
class MysqlDialect(BaseDialect):
    """MySQL 方言策略实现。"""

    family = "mysql"
    identifier_quote = "`"
    capabilities = {
        CAP_ENGINE, CAP_CHARSET, CAP_COLLATE, CAP_UNSIGNED, CAP_ZEROFILL,
        CAP_AUTO_INCREMENT, CAP_ENUM, CAP_SET,
        CAP_ON_UPDATE_TIMESTAMP, CAP_DELIMITER, CAP_LOCK_TABLES,
        CAP_SESSION_VARS, CAP_FOREIGN_KEY_CHECKS, CAP_USING_BTREE,
        CAP_ROW_FORMAT, CAP_VERSION_COMMENT, CAP_BACKTICK_QUOTE,
        CAP_TYPE_TINYINT, CAP_TYPE_MEDIUMINT, CAP_TYPE_INT_DISPLAY_WIDTH,
        CAP_TYPE_BIGINT_DISPLAY_WIDTH, CAP_TYPE_SMALLINT_DISPLAY_WIDTH,
        CAP_TYPE_INTEGER_DISPLAY_WIDTH, CAP_TYPE_TINYTEXT, CAP_TYPE_MEDIUMTEXT,
        CAP_TYPE_LONGTEXT, CAP_TYPE_BLOB, CAP_TYPE_DATETIME, CAP_TYPE_YEAR,
        CAP_TYPE_DOUBLE, CAP_TYPE_FLOAT, CAP_TYPE_ENUM, CAP_TYPE_SET,
        CAP_TYPE_BIT, CAP_TYPE_BIT_LITERAL,
    }

    def quote_identifier(self, name: str) -> str:
        return f"`{name}`"

    # ... 其余方法完全不变，从 dialects/mysql.py 复制 ...
```

- [ ] **Step 3: 迁移 kingbase.py，添加 capabilities**

```python
from __future__ import annotations
from converter.dialects.base import BaseDialect
from converter.capabilities import (
    CAP_CASCADE, CAP_DOUBLE_QUOTE,
    CAP_TYPE_SERIAL, CAP_TYPE_BIGSERIAL, CAP_TYPE_BOOLEAN, CAP_TYPE_BYTEA,
    CAP_TYPE_TIMESTAMP, CAP_TYPE_TEXT, CAP_TYPE_DOUBLE_PRECISION,
    CAP_TYPE_EXTENSION, CAP_TYPE_PG_TYPE_CAST,
)
from converter.registry import register
from sql_parser import TableBlock


@register
class KingbaseDialect(BaseDialect):
    """Kingbase (金仓数据库) 方言策略实现。"""

    family = "pg"
    identifier_quote = '"'
    capabilities = {
        CAP_CASCADE, CAP_DOUBLE_QUOTE,
        CAP_TYPE_SERIAL, CAP_TYPE_BIGSERIAL, CAP_TYPE_BOOLEAN, CAP_TYPE_BYTEA,
        CAP_TYPE_TIMESTAMP, CAP_TYPE_TEXT, CAP_TYPE_DOUBLE_PRECISION,
        CAP_TYPE_EXTENSION, CAP_TYPE_PG_TYPE_CAST,
    }

    # ... 其余方法完全不变，从 dialects/kingbase.py 复制 ...
```

- [ ] **Step 4: 迁移 pgsql.py，添加 capabilities**

```python
from __future__ import annotations
from converter.dialects.base import BaseDialect
from converter.capabilities import (
    CAP_CASCADE, CAP_DOUBLE_QUOTE,
    CAP_TYPE_SERIAL, CAP_TYPE_BIGSERIAL, CAP_TYPE_BOOLEAN, CAP_TYPE_BYTEA,
    CAP_TYPE_TIMESTAMP, CAP_TYPE_TEXT, CAP_TYPE_DOUBLE_PRECISION,
    CAP_TYPE_EXTENSION, CAP_TYPE_PG_TYPE_CAST,
)
from converter.registry import register
from sql_parser import TableBlock


@register
class PgsqlDialect(BaseDialect):
    """PostgreSQL 方言策略实现。"""

    family = "pg"
    identifier_quote = '"'
    capabilities = {
        CAP_CASCADE, CAP_DOUBLE_QUOTE,
        CAP_TYPE_SERIAL, CAP_TYPE_BIGSERIAL, CAP_TYPE_BOOLEAN, CAP_TYPE_BYTEA,
        CAP_TYPE_TIMESTAMP, CAP_TYPE_TEXT, CAP_TYPE_DOUBLE_PRECISION,
        CAP_TYPE_EXTENSION, CAP_TYPE_PG_TYPE_CAST,
    }

    # ... 其余方法完全不变，从 dialects/pgsql.py 复制 ...
```

- [ ] **Step 5: 迁移 sqlite.py，添加 capabilities**

```python
from __future__ import annotations
from converter.dialects.base import BaseDialect
from converter.capabilities import (
    CAP_DOUBLE_QUOTE, CAP_TYPE_AUTOINCREMENT, CAP_TYPE_BLOB,
)
from converter.registry import register
from sql_parser import TableBlock


@register
class SqliteDialect(BaseDialect):
    """SQLite 方言策略实现。"""

    family = "sqlite"
    identifier_quote = '"'
    capabilities = {
        CAP_DOUBLE_QUOTE, CAP_TYPE_AUTOINCREMENT, CAP_TYPE_BLOB,
    }

    # ... 其余方法完全不变，从 dialects/sqlite.py 复制 ...
```

- [ ] **Step 6: 更新 converter/dialects/__init__.py 为兼容导出**

```python
"""方言包 — 导入所有方言以触发 @register 装饰器。"""
from converter.dialects.base import BaseDialect
from converter.dialects.mysql import MysqlDialect
from converter.dialects.kingbase import KingbaseDialect
from converter.dialects.pgsql import PgsqlDialect
from converter.dialects.sqlite import SqliteDialect
```

- [ ] **Step 7: 验证方言注册**

```bash
python -c "
from converter.dialects import *  # 触发注册
from converter.registry import get_dialect
for m in ['mysql','kingbase','pgsql','sqlite','postgresql','sqlite3']:
    d = get_dialect(m)
    print(f'{m}: family={d.family}, quote={d.identifier_quote}, caps={len(d.capabilities)}')
"
```

预期输出：
```
mysql: family=mysql, quote=`, caps=37
kingbase: family=pg, quote=", caps=11
pgsql: family=pg, quote=", caps=11
sqlite: family=sqlite, quote=", caps=3
postgresql: family=pg, quote=", caps=11
sqlite3: family=sqlite, quote=", caps=3
```

- [ ] **Step 8: 提交**

```bash
git add converter/dialects/
git commit -m "feat: migrate dialects to converter/dialects/ with family + capabilities"
```

---

### Task 5: 创建 Rule 数据类和 Pipeline 引擎

**Files:**
- Create: `converter/pipeline.py`

**Interfaces:**
- Produces: `Rule` dataclass, `rule_applies(rule, source, target) -> bool`, `Pipeline` class

- [ ] **Step 1: 编写 pipeline.py**

```python
"""规则引擎 — Rule 数据类 + Pipeline 编排器。"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from converter.dialects.base import BaseDialect


@dataclass
class Rule:
    """一条转换规则。"""
    name: str
    capability: str            # 依赖的能力标签
    pattern: re.Pattern
    replacement: str = ""      # remove/replace 时使用
    scope: str = "line"        # "global" | "line"
    skip_insert: bool = True
    desc: str = ""


def rule_applies(rule: Rule, source: BaseDialect, target: BaseDialect) -> bool:
    """源有该能力，目标没有 → 规则生效。"""
    return (
        rule.capability in source.capabilities
        and rule.capability not in target.capabilities
    )


def _is_insert_line(line: str) -> bool:
    """判断一行是否为 INSERT 数据行。"""
    return line.lstrip()[:11].upper().startswith("INSERT INTO")


def _apply_global(text: str, rule: Rule) -> tuple[str, int]:
    """对整段文本应用 global 规则。"""
    new_text, n = rule.pattern.subn(rule.replacement, text)
    return new_text, n


def _apply_line(text: str, rule: Rule) -> tuple[str, int]:
    """逐行应用规则，skip_insert 时跳过 INSERT 行。"""
    total = 0
    has_skip = rule.skip_insert
    out_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if has_skip and _is_insert_line(line):
            out_lines.append(line)
            continue
        new_line, n = rule.pattern.subn(rule.replacement, line)
        total += n
        out_lines.append(new_line)
    return "".join(out_lines), total


class Pipeline:
    """规则管线 — 按阶段顺序执行规则。"""

    def __init__(self, stages: list[list[Rule]]):
        self.stages = stages

    def run(self, text: str, source: BaseDialect, target: BaseDialect
            ) -> tuple[str, dict[str, int]]:
        """执行所有阶段，返回 (转换后文本, 命中计数)。"""
        counters: dict[str, int] = {}
        for stage in self.stages:
            for rule in stage:
                if rule_applies(rule, source, target):
                    if rule.scope == "global":
                        text, n = _apply_global(text, rule)
                    else:
                        text, n = _apply_line(text, rule)
                    counters[rule.name] = counters.get(rule.name, 0) + n
        return text, counters


# 标识符转换规则（特殊处理：需要目标方言的 identifier_quote）
def make_identifier_rule(source_quote: str) -> Rule:
    """生成标识符转换规则：将源引号风格转为目标引号风格。"""
    import re
    if source_quote == "`":
        pat = re.compile(r"`(\w+)`")
    else:
        pat = re.compile(r'"(\w+)"')
    return Rule(
        name="convert_identifier_quote",
        capability="backtick_quote" if source_quote == "`" else "double_quote",
        pattern=pat,
        replacement="",  # 运行时填充目标引号
        scope="line",
        skip_insert=False,
        desc=f"将标识符从 {source_quote} 转换为目标引号风格",
    )
```

- [ ] **Step 2: 验证导入**

```bash
python -c "from converter.pipeline import Rule, Pipeline, rule_applies; print('pipeline imported OK')"
```

- [ ] **Step 3: 提交**

```bash
git add converter/pipeline.py
git commit -m "feat: add Rule dataclass and Pipeline engine"
```

---

### Task 6: 迁移规则到 converter/rules/，改用 Capability

**Files:**
- Create: `converter/rules/cleanup.py`
- Create: `converter/rules/identifier.py`
- Create: `converter/rules/type_mapping.py`
- Create: `converter/rules/modifier.py`
- Create: `converter/rules/constraint.py`
- Create: `converter/rules/postprocess.py`
- Modify: `converter/rules/__init__.py`

**Interfaces:**
- Produces: 6 个 `list[Rule]`，`converter/rules/__init__.py` 汇总为 `ALL_STAGES: list[list[Rule]]`

- [ ] **Step 1: 编写 rules/cleanup.py**（阶段1：预处理清理）

```python
"""阶段1: 预处理清理 — 删除源方言特有的注释/锁表/会话变量/DELIMITER。"""
import re
from converter.pipeline import Rule
from converter.capabilities import (
    CAP_VERSION_COMMENT, CAP_LOCK_TABLES, CAP_DELIMITER,
    CAP_SESSION_VARS, CAP_FOREIGN_KEY_CHECKS,
)

CLEANUP_RULES: list[Rule] = [
    Rule(
        name="strip_version_comment",
        capability=CAP_VERSION_COMMENT,
        pattern=re.compile(r"/\*!\d+\s.*?\*/;?", re.DOTALL),
        replacement="",
        scope="global",
        skip_insert=True,
        desc="剔除 mysqldump 的版本条件注释 /*!40101 ... */",
    ),
    Rule(
        name="strip_lock_tables",
        capability=CAP_LOCK_TABLES,
        pattern=re.compile(
            r"^\s*(LOCK\s+TABLES\s.*?;|UNLOCK\s+TABLES\s*;)\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        replacement="",
        scope="global",
        skip_insert=True,
        desc="删除 LOCK TABLES / UNLOCK TABLES 行",
    ),
    Rule(
        name="normalize_delimiter",
        capability=CAP_DELIMITER,
        pattern=re.compile(
            r"^\s*DELIMITER\s+(\S+)\s*$(.*?)\1\s*$\s*^\s*DELIMITER\s*;\s*$",
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        ),
        replacement="",  # 特殊处理：lambda 在 Rule 中不支持，用空字符串占位，Pipeline 特殊处理
        scope="global",
        skip_insert=True,
        desc="处理 DELIMITER $$ ... $$ DELIMITER ; 块，把 $$ 换回 ;",
    ),
    Rule(
        name="strip_session_vars",
        capability=CAP_SESSION_VARS,
        pattern=re.compile(
            r"^\s*SET\s+(@OLD_\w+|@@[\w.]+|@\w+)\s*=.*?;\s*$",
            re.IGNORECASE,
        ),
        replacement="",
        scope="line",
        skip_insert=True,
        desc="删除 SET @OLD_... / SET @@... 会话变量行",
    ),
    Rule(
        name="strip_foreign_key_checks",
        capability=CAP_FOREIGN_KEY_CHECKS,
        pattern=re.compile(
            r"^\s*SET\s+FOREIGN_KEY_CHECKS\s*=\s*\d+\s*;\s*$",
            re.IGNORECASE,
        ),
        replacement="",
        scope="line",
        skip_insert=True,
        desc="删除 SET FOREIGN_KEY_CHECKS = 0/1 行",
    ),
    Rule(
        name="strip_set_names",
        capability=CAP_CHARSET,
        pattern=re.compile(
            r"^\s*SET\s+NAMES\s+'?\w+'?(\s+COLLATE\s+'?\w+'?)?\s*;\s*$",
            re.IGNORECASE,
        ),
        replacement="",
        scope="line",
        skip_insert=True,
        desc="删除 SET NAMES xxx 字符集设置行",
    ),
    Rule(
        name="strip_oracle_hints",
        capability=CAP_ORACLE_HINTS,
        pattern=re.compile(r"/\*\+.*?\*/", re.DOTALL),
        replacement="",
        scope="global",
        skip_insert=True,
        desc="删除 Oracle 优化器提示 /*+ ... */",
    ),
]
```

- [ ] **Step 2: 编写 rules/identifier.py**（阶段2：标识符转换）

```python
"""阶段2: 标识符转换 — 引号风格转换。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_BACKTICK_QUOTE, CAP_DOUBLE_QUOTE

IDENTIFIER_RULES: list[Rule] = [
    Rule(
        name="convert_backtick_quote",
        capability=CAP_BACKTICK_QUOTE,
        pattern=re.compile(r"`(\w+)`"),
        replacement="",  # 运行时由 Pipeline 用目标 quote 填充
        scope="line",
        skip_insert=False,
        desc="将反引号标识符转为目标引号风格",
    ),
    Rule(
        name="convert_double_quote",
        capability=CAP_DOUBLE_QUOTE,
        pattern=re.compile(r'"(\w+)"'),
        replacement="",  # 运行时由 Pipeline 用目标 quote 填充
        scope="line",
        skip_insert=False,
        desc="将双引号标识符转为目标引号风格",
    ),
]
```

- [ ] **Step 3: 编写 rules/type_mapping.py**（阶段3：类型映射）

```python
"""阶段3: 类型映射 — 源方言特有类型 → 目标方言兼容类型。"""
import re
from converter.pipeline import Rule
from converter.capabilities import (
    CAP_TYPE_TINYINT, CAP_TYPE_MEDIUMINT, CAP_TYPE_INT_DISPLAY_WIDTH,
    CAP_TYPE_BIGINT_DISPLAY_WIDTH, CAP_TYPE_SMALLINT_DISPLAY_WIDTH,
    CAP_TYPE_INTEGER_DISPLAY_WIDTH, CAP_TYPE_TINYTEXT, CAP_TYPE_MEDIUMTEXT,
    CAP_TYPE_LONGTEXT, CAP_TYPE_BLOB, CAP_TYPE_DATETIME, CAP_TYPE_TIMESTAMP,
    CAP_TYPE_YEAR, CAP_TYPE_DOUBLE, CAP_TYPE_FLOAT, CAP_TYPE_ENUM,
    CAP_TYPE_SET, CAP_TYPE_BIT, CAP_TYPE_BIT_LITERAL,
    CAP_TYPE_VARCHAR2, CAP_TYPE_NVARCHAR2, CAP_TYPE_NUMBER,
    CAP_TYPE_CLOB, CAP_TYPE_NCLOB, CAP_TYPE_BLOB_ORACLE,
    CAP_TYPE_LONG, CAP_TYPE_LONG_RAW, CAP_TYPE_RAW, CAP_TYPE_NCHAR,
    CAP_TYPE_ORACLE_DATE, CAP_TYPE_SERIAL, CAP_TYPE_BIGSERIAL,
    CAP_TYPE_BOOLEAN, CAP_TYPE_BYTEA, CAP_TYPE_DOUBLE_PRECISION,
    CAP_TYPE_AUTOINCREMENT, CAP_TYPE_TEXT, CAP_TYPE_PG_TYPE_CAST,
    CAP_TYPE_EXTENSION,
    CAP_AUTO_INCREMENT,
)

# ======================== MySQL 类型 → 其他 ========================

TYPE_MAPPING_RULES: list[Rule] = [

    # MySQL 整数类型
    Rule(
        name="convert_tinyint_type",
        capability=CAP_TYPE_TINYINT,
        pattern=re.compile(r"\btinyint\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="SMALLINT",
        scope="line", skip_insert=True,
        desc="将 MySQL TINYINT(N) 转为 SMALLINT",
    ),
    Rule(
        name="convert_mediumint_type",
        capability=CAP_TYPE_MEDIUMINT,
        pattern=re.compile(r"\bmediumint\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="INTEGER",
        scope="line", skip_insert=True,
        desc="将 MySQL MEDIUMINT(N) 转为 INTEGER",
    ),
    Rule(
        name="convert_int_display_width",
        capability=CAP_TYPE_INT_DISPLAY_WIDTH,
        pattern=re.compile(r"\bint\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="INTEGER",
        scope="line", skip_insert=True,
        desc="将 MySQL INT(N) 转为 INTEGER",
    ),
    Rule(
        name="convert_integer_display_width",
        capability=CAP_TYPE_INTEGER_DISPLAY_WIDTH,
        pattern=re.compile(r"\binteger\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="INTEGER",
        scope="line", skip_insert=True,
        desc="将 MySQL INTEGER(N) 转为 INTEGER",
    ),
    Rule(
        name="convert_bigint_display_width",
        capability=CAP_TYPE_BIGINT_DISPLAY_WIDTH,
        pattern=re.compile(r"\bbigint\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="BIGINT",
        scope="line", skip_insert=True,
        desc="将 MySQL BIGINT(N) 转为 BIGINT",
    ),
    Rule(
        name="convert_smallint_display_width",
        capability=CAP_TYPE_SMALLINT_DISPLAY_WIDTH,
        pattern=re.compile(r"\bsmallint\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="SMALLINT",
        scope="line", skip_insert=True,
        desc="将 MySQL SMALLINT(N) 转为 SMALLINT",
    ),

    # MySQL 日期时间类型
    Rule(
        name="convert_datetime_type",
        capability=CAP_TYPE_DATETIME,
        pattern=re.compile(r"\bdatetime\b", re.IGNORECASE),
        replacement="TIMESTAMP",
        scope="line", skip_insert=True,
        desc="将 MySQL datetime 转为 TIMESTAMP",
    ),
    Rule(
        name="convert_year_type",
        capability=CAP_TYPE_YEAR,
        pattern=re.compile(r"\byear\b(\s*\(\s*4\s*\))?", re.IGNORECASE),
        replacement="SMALLINT",
        scope="line", skip_insert=True,
        desc="将 MySQL YEAR 转为 SMALLINT",
    ),

    # MySQL 文本类型
    Rule(
        name="convert_text_types",
        capability=CAP_TYPE_TINYTEXT,
        pattern=re.compile(r"\b(tinytext|mediumtext|longtext)\b", re.IGNORECASE),
        replacement="TEXT",
        scope="line", skip_insert=True,
        desc="将 MySQL TINYTEXT/MEDIUMTEXT/LONGTEXT 统一转为 TEXT",
    ),

    # MySQL 二进制类型
    Rule(
        name="convert_blob_types",
        capability=CAP_TYPE_BLOB,
        pattern=re.compile(r"\b(tinyblob|mediumblob|longblob|blob)\b", re.IGNORECASE),
        replacement="BYTEA",
        scope="line", skip_insert=True,
        desc="将 MySQL BLOB 系列转为 BYTEA",
    ),

    # MySQL ENUM / SET
    Rule(
        name="convert_enum_type",
        capability=CAP_TYPE_ENUM,
        pattern=re.compile(r"\benum\s*\([^)]*\)", re.IGNORECASE),
        replacement="VARCHAR(255)",
        scope="line", skip_insert=True,
        desc="将 MySQL ENUM(...) 转为 VARCHAR(255)",
    ),
    Rule(
        name="convert_set_type",
        capability=CAP_TYPE_SET,
        pattern=re.compile(r"\bset\s*\([^)]*\)", re.IGNORECASE),
        replacement="VARCHAR(255)",
        scope="line", skip_insert=True,
        desc="将 MySQL SET(...) 转为 VARCHAR(255)",
    ),

    # MySQL 浮点类型
    Rule(
        name="convert_double_type",
        capability=CAP_TYPE_DOUBLE,
        pattern=re.compile(r"\bdouble\b(?!\s+precision)", re.IGNORECASE),
        replacement="DOUBLE PRECISION",
        scope="line", skip_insert=True,
        desc="将 MySQL DOUBLE 转为 DOUBLE PRECISION",
    ),
    Rule(
        name="convert_float_type",
        capability=CAP_TYPE_FLOAT,
        pattern=re.compile(r"\bfloat\b(\s*\(\d+,\d+\))?", re.IGNORECASE),
        replacement="REAL",
        scope="line", skip_insert=True,
        desc="将 MySQL FLOAT 转为 REAL",
    ),

    # MySQL BIT 类型和字面量
    Rule(
        name="convert_bit_type",
        capability=CAP_TYPE_BIT,
        pattern=re.compile(r"\bbit\s*\(\s*1\s*\)", re.IGNORECASE),
        replacement="SMALLINT",
        scope="line", skip_insert=False,
        desc="将 MySQL bit(1) 转为 SMALLINT",
    ),
    Rule(
        name="convert_bit_literal",
        capability=CAP_TYPE_BIT_LITERAL,
        pattern=re.compile(r"\bb'(0|1)'", re.IGNORECASE),
        replacement=r"'\1'",
        scope="line", skip_insert=False,
        desc="将 b'0'/b'1' 二进制字面量转为普通整数",
    ),

    # MySQL AUTO_INCREMENT → SQLite AUTOINCREMENT
    Rule(
        name="convert_auto_increment",
        capability=CAP_AUTO_INCREMENT,
        pattern=re.compile(r"\bAUTO_INCREMENT\b", re.IGNORECASE),
        replacement="AUTOINCREMENT",
        scope="line", skip_insert=True,
        desc="将 MySQL AUTO_INCREMENT 转为 AUTOINCREMENT",
    ),

    # ======================== Oracle 类型 → 其他 ========================

    Rule(
        name="convert_long_raw_type",
        capability=CAP_TYPE_LONG_RAW,
        pattern=re.compile(r"\blong\s+raw\b", re.IGNORECASE),
        replacement="BYTEA",
        scope="line", skip_insert=True,
        desc="将 Oracle LONG RAW 转为 BYTEA",
    ),
    Rule(
        name="convert_varchar2_type",
        capability=CAP_TYPE_VARCHAR2,
        pattern=re.compile(r"\b(varchar2|nvarchar2|varchar|nvarchar|char|nchar|clob|nclob|long)\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="TEXT",
        scope="line", skip_insert=True,
        desc="将 Oracle 字符串类型统一转为 TEXT",
    ),
    Rule(
        name="convert_oracle_number_precision",
        capability=CAP_TYPE_NUMBER,
        pattern=re.compile(r"\bnumber\b(\s*\(\d+,\d+\))", re.IGNORECASE),
        replacement=r"REAL",
        scope="line", skip_insert=True,
        desc="将 Oracle NUMBER(N,M) 转为 REAL",
    ),
    Rule(
        name="convert_oracle_number",
        capability=CAP_TYPE_NUMBER,
        pattern=re.compile(r"\bnumber\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="INTEGER",
        scope="line", skip_insert=True,
        desc="将 Oracle NUMBER(N) 转为 INTEGER",
    ),
    Rule(
        name="convert_oracle_date_type",
        capability=CAP_TYPE_ORACLE_DATE,
        pattern=re.compile(r"\bdate\b", re.IGNORECASE),
        replacement="TIMESTAMP",
        scope="line", skip_insert=True,
        desc="将 Oracle DATE 转为 TIMESTAMP",
    ),
    Rule(
        name="convert_raw_type",
        capability=CAP_TYPE_RAW,
        pattern=re.compile(r"\b(raw|blob)\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="BLOB",
        scope="line", skip_insert=True,
        desc="将 Oracle RAW/BLOB 转为 BLOB",
    ),

    # ======================== PG 类型 → 其他 ========================

    Rule(
        name="convert_serial_type",
        capability=CAP_TYPE_SERIAL,
        pattern=re.compile(r"\b(serial|bigserial|smallserial)\b", re.IGNORECASE),
        replacement="INTEGER",
        scope="line", skip_insert=True,
        desc="将 PG SERIAL 转为 INTEGER",
    ),
    Rule(
        name="convert_boolean_type",
        capability=CAP_TYPE_BOOLEAN,
        pattern=re.compile(r"\bboolean\b", re.IGNORECASE),
        replacement="INTEGER",
        scope="line", skip_insert=True,
        desc="将 PG BOOLEAN 转为 INTEGER",
    ),
    Rule(
        name="convert_bytea_type",
        capability=CAP_TYPE_BYTEA,
        pattern=re.compile(r"\bbytea\b", re.IGNORECASE),
        replacement="BLOB",
        scope="line", skip_insert=True,
        desc="将 PG BYTEA 转为 BLOB",
    ),
    Rule(
        name="convert_timestamp_type",
        capability=CAP_TYPE_TIMESTAMP,
        pattern=re.compile(r"\btimestamp\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="TEXT",
        scope="line", skip_insert=True,
        desc="将 PG TIMESTAMP 转为 TEXT",
    ),
    Rule(
        name="convert_double_precision",
        capability=CAP_TYPE_DOUBLE_PRECISION,
        pattern=re.compile(r"\bdouble\s+precision\b", re.IGNORECASE),
        replacement="REAL",
        scope="line", skip_insert=True,
        desc="将 PG DOUBLE PRECISION 转为 REAL",
    ),
    Rule(
        name="convert_pg_text_types",
        capability=CAP_TYPE_TEXT,
        pattern=re.compile(r"\b(varchar|char|text)\b(\s*\(\d+\))?", re.IGNORECASE),
        replacement="TEXT",
        scope="line", skip_insert=True,
        desc="将 PG 字符串类型统一转为 TEXT",
    ),
    Rule(
        name="convert_pg_integer_types",
        capability=CAP_TYPE_SERIAL,
        pattern=re.compile(r"\b(smallint|integer|int|bigint|int2|int4|int8)\b", re.IGNORECASE),
        replacement="INTEGER",
        scope="line", skip_insert=True,
        desc="将 PG 整数类型统一转为 INTEGER",
    ),
]
```

> 注意：Oracle 类型转换有两条 `CAP_TYPE_NUMBER` 规则，Pipeline 按顺序执行，`NUMBER(N,M)` 先匹配 → `REAL`，再 `NUMBER(N)` → `INTEGER`。需要在 Pipeline 中注意规则顺序。

- [ ] **Step 4: 编写 rules/modifier.py**（阶段4：修饰符清理）

```python
"""阶段4: 修饰符清理 — 删除/替换源方言特有的修饰符和子句。"""
import re
from converter.pipeline import Rule
from converter.capabilities import (
    CAP_UNSIGNED, CAP_ZEROFILL, CAP_ENGINE, CAP_CHARSET, CAP_COLLATE,
    CAP_CASCADE, CAP_ON_UPDATE_TIMESTAMP, CAP_ROW_FORMAT,
    CAP_AUTO_INCREMENT, CAP_TYPE_PG_TYPE_CAST, CAP_TYPE_EXTENSION,
)

MODIFIER_RULES: list[Rule] = [
    Rule(
        name="strip_unsigned",
        capability=CAP_UNSIGNED,
        pattern=re.compile(r"\s+unsigned\b", re.IGNORECASE),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除 UNSIGNED 修饰符",
    ),
    Rule(
        name="strip_zerofill",
        capability=CAP_ZEROFILL,
        pattern=re.compile(r"\s+zerofill\b", re.IGNORECASE),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除 ZEROFILL 修饰符",
    ),
    Rule(
        name="strip_engine_clause",
        capability=CAP_ENGINE,
        pattern=re.compile(r"\s*ENGINE\s*=\s*\w+", re.IGNORECASE),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除表级 ENGINE=xxx 子句",
    ),
    Rule(
        name="strip_default_charset",
        capability=CAP_CHARSET,
        pattern=re.compile(
            r"\s*(DEFAULT\s+)?(CHARACTER\s+SET|CHARSET)\s*=?\s*\w+"
            r"(\s+COLLATE\s*=?\s*\w+)?",
            re.IGNORECASE,
        ),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除表级 DEFAULT CHARSET / CHARACTER SET / COLLATE 子句",
    ),
    Rule(
        name="strip_collate_standalone",
        capability=CAP_COLLATE,
        pattern=re.compile(r"\s+COLLATE\s+\w+", re.IGNORECASE),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除独立 COLLATE 子句",
    ),
    Rule(
        name="strip_column_charset",
        capability=CAP_CHARSET,
        pattern=re.compile(
            r"\s+(CHARACTER\s+SET|CHARSET)\s+\w+(\s+COLLATE\s+\w+)?",
            re.IGNORECASE,
        ),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除列定义中的 CHARACTER SET / COLLATE 子句",
    ),
    Rule(
        name="strip_cascade",
        capability=CAP_CASCADE,
        pattern=re.compile(r"\s+CASCADE\b", re.IGNORECASE),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除 CASCADE",
    ),
    Rule(
        name="strip_on_update_timestamp",
        capability=CAP_ON_UPDATE_TIMESTAMP,
        pattern=re.compile(
            r"\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP(\s*\(\d+\))?",
            re.IGNORECASE,
        ),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除 ON UPDATE CURRENT_TIMESTAMP",
    ),
    Rule(
        name="strip_table_auto_increment",
        capability=CAP_AUTO_INCREMENT,
        pattern=re.compile(r"\s*AUTO_INCREMENT\s*=\s*\d+", re.IGNORECASE),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除表级 AUTO_INCREMENT=N 起始值",
    ),
    Rule(
        name="strip_row_format",
        capability=CAP_ROW_FORMAT,
        pattern=re.compile(
            r"\s*(ROW_FORMAT|KEY_BLOCK_SIZE|PACK_KEYS|STATS_PERSISTENT|"
            r"STATS_AUTO_RECALC|DELAY_KEY_WRITE)\s*=\s*\w+",
            re.IGNORECASE,
        ),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除 ROW_FORMAT / KEY_BLOCK_SIZE 等表选项",
    ),
    Rule(
        name="strip_pg_type_cast",
        capability=CAP_TYPE_PG_TYPE_CAST,
        pattern=re.compile(r"::\w+"),
        replacement="",
        scope="line", skip_insert=False,
        desc="删除 PG ::type 类型转换语法",
    ),
    Rule(
        name="strip_pg_extension",
        capability=CAP_TYPE_EXTENSION,
        pattern=re.compile(
            r"^\s*CREATE\s+EXTENSION\s+.*?;\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        replacement="",
        scope="global", skip_insert=True,
        desc="删除 CREATE EXTENSION 语句",
    ),
]
```

- [ ] **Step 5: 编写 rules/constraint.py**（阶段5：约束适配）

```python
"""阶段5: 约束/索引适配 — 删除或转换源方言特有的约束语法。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_USING_BTREE

CONSTRAINT_RULES: list[Rule] = [
    Rule(
        name="strip_using_btree",
        capability=CAP_USING_BTREE,
        pattern=re.compile(r"\s*USING\s+BTREE", re.IGNORECASE),
        replacement="",
        scope="line", skip_insert=True,
        desc="删除索引中的 USING BTREE",
    ),
]
```

- [ ] **Step 6: 编写 rules/postprocess.py**（阶段6：后处理）

```python
"""阶段6: 后处理 — 最终语法修正。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_AUTO_INCREMENT

POSTPROCESS_RULES: list[Rule] = [
    Rule(
        name="fix_autoincrement_syntax",
        capability=CAP_AUTO_INCREMENT,
        pattern=re.compile(r"\bNOT\s+NULL\s+AUTOINCREMENT\b", re.IGNORECASE),
        replacement="AUTOINCREMENT",
        scope="line", skip_insert=True,
        desc="去除 AUTOINCREMENT 前的 NOT NULL",
    ),
]
```

- [ ] **Step 7: 更新 rules/__init__.py 汇总导出**

```python
"""规则包 — 汇总所有阶段规则，导出为 Pipeline 可用的 stages 列表。"""
from converter.rules.cleanup import CLEANUP_RULES
from converter.rules.identifier import IDENTIFIER_RULES
from converter.rules.type_mapping import TYPE_MAPPING_RULES
from converter.rules.modifier import MODIFIER_RULES
from converter.rules.constraint import CONSTRAINT_RULES
from converter.rules.postprocess import POSTPROCESS_RULES

ALL_STAGES: list[list] = [
    CLEANUP_RULES,
    IDENTIFIER_RULES,
    TYPE_MAPPING_RULES,
    MODIFIER_RULES,
    CONSTRAINT_RULES,
    POSTPROCESS_RULES,
]
```

- [ ] **Step 8: 验证规则导入和计数**

```bash
python -c "
from converter.rules import ALL_STAGES
total = sum(len(s) for s in ALL_STAGES)
print(f'阶段数: {len(ALL_STAGES)}')
for i, s in enumerate(ALL_STAGES, 1):
    print(f'  阶段{i}: {len(s)} 条规则')
print(f'总规则数: {total}')
"
```

预期：6 阶段，约 50 条规则（从 86 条压缩）。

- [ ] **Step 9: 提交**

```bash
git add converter/rules/
git commit -m "feat: migrate rules to capability-based, split by pipeline stage"
```

---

### Task 7: 处理 Pipeline 中的特殊规则

**Files:**
- Modify: `converter/pipeline.py`

**Interfaces:**
- 更新 Pipeline 以支持：`normalize_delimiter` 的 lambda replacement、`identifier` 阶段的目标引号替换

- [ ] **Step 1: 更新 Pipeline.run 处理特殊规则**

在 `Pipeline.run` 方法中，在执行 `normalize_delimiter` 规则时使用 lambda replacement，在 `identifier` 阶段用目标 dialect 的 `identifier_quote` 填充 replacement。

```python
class Pipeline:
    """规则管线。"""

    def __init__(self, stages: list[list[Rule]]):
        self.stages = stages

    def run(self, text: str, source: BaseDialect, target: BaseDialect
            ) -> tuple[str, dict[str, int]]:
        counters: dict[str, int] = {}
        for stage in self.stages:
            for rule in stage:
                if not rule_applies(rule, source, target):
                    continue

                # 特殊处理：normalize_delimiter 使用 lambda
                if rule.name == "normalize_delimiter":
                    text, n = rule.pattern.subn(
                        lambda m: m.group(2).replace(m.group(1), ";").strip() + ";\n",
                        text,
                    )
                    counters[rule.name] = counters.get(rule.name, 0) + n
                    continue

                # 特殊处理：identifier 规则用目标引号
                if rule.name in ("convert_backtick_quote", "convert_double_quote"):
                    repl = target.identifier_quote + r"\1" + target.identifier_quote
                    if rule.scope == "global":
                        text, n = rule.pattern.subn(repl, text)
                    else:
                        text, n = _apply_line_with_repl(text, rule, repl)
                    counters[rule.name] = counters.get(rule.name, 0) + n
                    continue

                # 标准规则
                if rule.scope == "global":
                    text, n = _apply_global(text, rule)
                else:
                    text, n = _apply_line(text, rule)
                counters[rule.name] = counters.get(rule.name, 0) + n
        return text, counters


def _apply_line_with_repl(text: str, rule: Rule, repl: str) -> tuple[str, int]:
    """逐行应用规则，使用指定的 replacement。"""
    total = 0
    has_skip = rule.skip_insert
    out_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if has_skip and _is_insert_line(line):
            out_lines.append(line)
            continue
        new_line, n = rule.pattern.subn(repl, line)
        total += n
        out_lines.append(new_line)
    return "".join(out_lines), total
```

- [ ] **Step 2: 提交**

```bash
git add converter/pipeline.py
git commit -m "feat: handle special rules in Pipeline (delimiter lambda, identifier quote)"
```

---

### Task 8: 更新 convert.py 使用新架构

**Files:**
- Modify: `convert.py`

- [ ] **Step 1: 更新导入和 convert() 函数**

修改 `convert.py` 的导入部分（第11-19行）和 `convert()` 函数（第312-322行）：

```python
# 替换旧导入
from converter.registry import get_dialect
from converter.pipeline import Pipeline
from converter.rules import ALL_STAGES

# 构建全局 Pipeline 实例（单例）
_pipeline = Pipeline(ALL_STAGES)


def convert(text: str, source_mode: str, target_mode: str,
            database: str | None = None) -> tuple[str, dict[str, int]]:
    """转换主入口：Pipeline → 解析表结构 → FK排序 → 格式化输出。"""
    source_dialect = get_dialect(source_mode, database)
    target_dialect = get_dialect(target_mode, database)
    text, counters = _pipeline.run(text, source_dialect, target_dialect)
    tables = parse_tables(text, database)
    tables = sort_tables_by_fk(tables)
    text = format_structured_output(tables, target_dialect)
    return text, counters
```

- [ ] **Step 2: 更新 main() 中 verbose 输出**

修改 `main()` 末尾（第388-392行），`filter_rules` 不再可用，改为直接从 counters 输出：

```python
if args.verbose:
    print("Rule hit counts:")
    for name, n in sorted(counters.items()):
        if n > 0:
            print(f"  {name:<32} {n:>6}")
```

- [ ] **Step 3: 删除旧函数**

删除 `convert.py` 中不再需要的函数：
- `filter_rules()` (第171-182行)
- `apply_global_rules()` (第190-200行)
- `apply_line_rules()` (第203-224行)
- 删除 `from rules import RULES` 导入

- [ ] **Step 4: 验证 convert.py 无语法错误**

```bash
python -c "from convert import convert; print('convert.py imported OK')"
```

- [ ] **Step 5: 提交**

```bash
git add convert.py
git commit -m "feat: update convert.py to use new Pipeline + Dialect architecture"
```

---

### Task 9: 更新测试文件

**Files:**
- Modify: `tests/test_sniff.py`

- [ ] **Step 1: 更新导入路径**

```python
# 替换旧导入
from converter.registry import get_dialect
from converter.dialects.pgsql import PgsqlDialect
```

- [ ] **Step 2: 运行现有测试**

```bash
python -m unittest tests.test_sniff -v
```

预期：全部通过。

- [ ] **Step 3: 提交**

```bash
git add tests/test_sniff.py
git commit -m "test: update test imports to use converter/ package"
```

---

### Task 10: 删除旧文件并验证端到端

**Files:**
- Delete: `dialects/` 目录
- Delete: `rules.py`

- [ ] **Step 1: 删除旧文件**

```bash
rm -rf dialects/ rules.py
```

- [ ] **Step 2: 验证导入无残留引用**

```bash
python -c "from convert import convert; print('OK')"
```

- [ ] **Step 3: 运行全部测试**

```bash
python -m unittest tests.test_sniff -v
```

- [ ] **Step 4: 端到端验证 MySQL → Kingbase**

```bash
python convert.py tests/sample_input.sql --target-mode kingbase -o tests/_verify_kb.sql --overwrite
# 检查输出与 tests/sample_output.sql 一致
diff tests/sample_output.sql tests/_verify_kb.sql && echo "MATCH" || echo "DIFF"
rm -f tests/_verify_kb.sql
```

- [ ] **Step 5: 端到端验证 MySQL → PGSQL**

```bash
python convert.py tests/sample_input.sql --target-mode pgsql -o tests/_verify_pg.sql --overwrite
rm -f tests/_verify_pg.sql
```

- [ ] **Step 6: 端到端验证 MySQL → SQLite**

```bash
python -c "
import tempfile, os
# 创建最小测试 SQL
sql = '''CREATE TABLE t (id INT AUTO_INCREMENT, name VARCHAR(64), PRIMARY KEY (id)) ENGINE=InnoDB;
INSERT INTO t VALUES (1,'test');'''
f = tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8')
f.write(sql); f.close()
os.system(f'python convert.py {f.name} --target-mode sqlite -o {f.name}_out --overwrite')
# 验证 .db 文件
import sqlite3
db = sqlite3.connect(f.name + '_out.db')
print('tables:', db.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())
print('rows:', db.execute('SELECT * FROM t').fetchall())
db.close()
# 清理
for ext in ['', '.sql', '.db']:
    try: os.unlink(f.name + '_out' + ext)
    except: pass
os.unlink(f.name)
"
```

- [ ] **Step 7: 端到端验证 Oracle → PGSQL**

```bash
python convert.py tests/sniff_oracle_input.sql --target-mode pgsql -o tests/_verify_ora.sql --overwrite
diff tests/actual_sniff_oracle.sql tests/_verify_ora.sql && echo "MATCH" || echo "DIFF"
rm -f tests/_verify_ora.sql
```

- [ ] **Step 8: 提交**

```bash
git rm -r dialects/ rules.py
git commit -m "refactor: remove old dialects/ and rules.py, replaced by converter/ package"
```

---

### Task 11: 最终验证

- [ ] **Step 1: 运行全量测试**

```bash
python -m unittest tests.test_sniff -v
```

- [ ] **Step 2: 确认代码行数减少**

```bash
find converter -name "*.py" | xargs wc -l | tail -1
wc -l convert.py
```

- [ ] **Step 3: 确认规则数**

```bash
python -c "from converter.rules import ALL_STAGES; print('总规则:', sum(len(s) for s in ALL_STAGES))"
```

- [ ] **Step 4: 验证新增方言（模拟）只需声明 capabilities**

```bash
python -c "
# 模拟新增一个 PG 家族方言：只需声明 capabilities，规则自动生效
from converter.dialects.base import BaseDialect
from converter.capabilities import CAP_CASCADE, CAP_DOUBLE_QUOTE
from converter.registry import register

@register
class OpenGaussDialect(BaseDialect):
    family = 'pg'
    identifier_quote = '\"'
    capabilities = {CAP_CASCADE, CAP_DOUBLE_QUOTE}

from converter.registry import get_dialect
d = get_dialect('opengauss')
print(f'family={d.family}, caps={len(d.capabilities)}')
print('新增方言无需修改规则文件 ✓')
"
```

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "chore: final verification of Phase 1 refactor"
```