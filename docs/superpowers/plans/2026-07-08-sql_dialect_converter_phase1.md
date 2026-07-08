# SQL 方言转换器 — 第一阶段重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构为 Dialect + Capability + Rule Engine 架构

**Architecture:** 方言声明 capabilities，规则按 Capability 自动匹配，Pipeline 按阶段执行

**Tech Stack:** Python 3.10+, dataclasses, re, pathlib, unittest

## Global Constraints

- 保留 Regex 作为规则执行引擎
- 所有现有测试必须通过
- 端到端输出与重构前一致
- 新增数据库时规则文件无需修改

## 并行策略

| 层级 | 任务 | 可并行 |
|---|---|---|
| L1 | T1 目录 + T2 capabilities + T3 registry | ✅ 同时进行 |
| L2 | T4 迁移方言（5个文件） + T5 pipeline | ✅ 同时进行 |
| L3 | T6 迁移规则（6个文件） | ✅ 同时进行 |
| L4 | T7 更新 convert.py + T8 更新测试 | ✅ 同时进行 |
| L5 | T9 删除旧文件 + T10 验证提交 | 顺序执行 |

---

## L1: 基础设施（3 个任务并行）

### T1: 创建目录结构和空包

**Files:** Create `converter/__init__.py`, `converter/mappings/__init__.py`, `converter/rules/__init__.py`, `converter/dialects/__init__.py`

```bash
mkdir -p converter/dialects converter/rules converter/mappings
touch converter/__init__.py converter/mappings/__init__.py converter/rules/__init__.py converter/dialects/__init__.py
```

### T2: 创建 converter/capabilities.py

**Files:** Create `converter/capabilities.py`

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
CAP_BACKTICK_QUOTE = "backtick_quote"
CAP_DOUBLE_QUOTE = "double_quote"

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

### T3: 创建 converter/registry.py

**Files:** Create `converter/registry.py`

```python
"""方言注册表 — 工厂函数 + 别名映射。"""
from __future__ import annotations
from converter.dialects.base import BaseDialect

_REGISTRY: dict[str, type[BaseDialect]] = {}
_ALIASES: dict[str, str] = {}


def register(dialect_cls: type[BaseDialect]) -> type[BaseDialect]:
    """装饰器：注册方言类。"""
    name = dialect_cls.__name__.replace("Dialect", "").lower()
    _REGISTRY[name] = dialect_cls
    return dialect_cls


def register_alias(alias: str, target: str) -> None:
    """注册别名，如 pgsql → pgsql。"""
    _ALIASES[alias] = target


def get_dialect(mode: str, database: str | None = None) -> BaseDialect:
    """根据模式名获取方言实例。"""
    key = mode.lower()
    key = _ALIASES.get(key, key)
    if key not in _REGISTRY:
        raise ValueError(f"Unsupported dialect mode: {mode}")
    return _REGISTRY[key](database)


# 别名
register_alias("pgsql", "pgsql")
register_alias("postgresql", "pgsql")
register_alias("postgres", "pgsql")
register_alias("sqlite3", "sqlite")
register_alias("pg", "pgsql")
```

---

## L2: 方言 + 引擎（2 个任务并行）

### T4: 迁移方言到 converter/dialects/，添加 family + capabilities

**Files:** Create `converter/dialects/base.py`, `mysql.py`, `kingbase.py`, `pgsql.py`, `sqlite.py`

**核心变更：** 从 `dialects/` 复制现有代码，每个类添加 `family`, `identifier_quote`, `capabilities` 三个类属性，加 `@register` 装饰器。

#### T4a: base.py

从 `dialects/base.py` 复制，在 `class BaseDialect:` 下添加：

```python
class BaseDialect:
    family: str = ""
    identifier_quote: str = '"'
    capabilities: set[str] = set()
```

其余方法不变。

#### T4b: mysql.py

从 `dialects/mysql.py` 复制，添加：

```python
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

@register
class MysqlDialect(BaseDialect):
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
```

其余方法不变。

#### T4c: kingbase.py

从 `dialects/kingbase.py` 复制，添加：

```python
from converter.dialects.base import BaseDialect
from converter.capabilities import (
    CAP_CASCADE, CAP_DOUBLE_QUOTE,
    CAP_TYPE_SERIAL, CAP_TYPE_BIGSERIAL, CAP_TYPE_BOOLEAN, CAP_TYPE_BYTEA,
    CAP_TYPE_TIMESTAMP, CAP_TYPE_TEXT, CAP_TYPE_DOUBLE_PRECISION,
    CAP_TYPE_EXTENSION, CAP_TYPE_PG_TYPE_CAST,
)
from converter.registry import register

@register
class KingbaseDialect(BaseDialect):
    family = "pg"
    identifier_quote = '"'
    capabilities = {
        CAP_CASCADE, CAP_DOUBLE_QUOTE,
        CAP_TYPE_SERIAL, CAP_TYPE_BIGSERIAL, CAP_TYPE_BOOLEAN, CAP_TYPE_BYTEA,
        CAP_TYPE_TIMESTAMP, CAP_TYPE_TEXT, CAP_TYPE_DOUBLE_PRECISION,
        CAP_TYPE_EXTENSION, CAP_TYPE_PG_TYPE_CAST,
    }
```

其余方法不变。

#### T4d: pgsql.py

从 `dialects/pgsql.py` 复制，添加与 kingbase.py 相同的 capabilities。

#### T4e: sqlite.py

从 `dialects/sqlite.py` 复制，添加：

```python
from converter.dialects.base import BaseDialect
from converter.capabilities import (
    CAP_DOUBLE_QUOTE, CAP_TYPE_AUTOINCREMENT, CAP_TYPE_BLOB,
)
from converter.registry import register

@register
class SqliteDialect(BaseDialect):
    family = "sqlite"
    identifier_quote = '"'
    capabilities = {
        CAP_DOUBLE_QUOTE, CAP_TYPE_AUTOINCREMENT, CAP_TYPE_BLOB,
    }
```

其余方法不变。

#### T4f: 更新 converter/dialects/__init__.py

```python
"""方言包 — 导入所有方言以触发 @register 装饰器。"""
from converter.dialects.base import BaseDialect
from converter.dialects.mysql import MysqlDialect
from converter.dialects.kingbase import KingbaseDialect
from converter.dialects.pgsql import PgsqlDialect
from converter.dialects.sqlite import SqliteDialect
```

### T5: 创建 converter/pipeline.py

**Files:** Create `converter/pipeline.py`

```python
"""规则引擎 — Rule 数据类 + Pipeline 编排器。"""
from __future__ import annotations
import re
from dataclasses import dataclass
from converter.dialects.base import BaseDialect


@dataclass
class Rule:
    """一条转换规则。"""
    name: str
    capability: str
    pattern: re.Pattern
    replacement: str = ""
    scope: str = "line"
    skip_insert: bool = True
    desc: str = ""


def rule_applies(rule: Rule, source: BaseDialect, target: BaseDialect) -> bool:
    """源有该能力，目标没有 → 规则生效。"""
    return (
        rule.capability in source.capabilities
        and rule.capability not in target.capabilities
    )


def _is_insert_line(line: str) -> bool:
    return line.lstrip()[:11].upper().startswith("INSERT INTO")


def _apply_global(text: str, rule: Rule) -> tuple[str, int]:
    new_text, n = rule.pattern.subn(rule.replacement, text)
    return new_text, n


def _apply_line(text: str, rule: Rule, repl: str = "") -> tuple[str, int]:
    replacement = repl if repl else rule.replacement
    total = 0
    has_skip = rule.skip_insert
    out_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if has_skip and _is_insert_line(line):
            out_lines.append(line)
            continue
        new_line, n = rule.pattern.subn(replacement, line)
        total += n
        out_lines.append(new_line)
    return "".join(out_lines), total


class Pipeline:
    """规则管线 — 按阶段顺序执行规则。"""

    def __init__(self, stages: list[list[Rule]]):
        self.stages = stages

    def run(self, text: str, source: BaseDialect, target: BaseDialect
            ) -> tuple[str, dict[str, int]]:
        counters: dict[str, int] = {}
        for stage in self.stages:
            for rule in stage:
                if not rule_applies(rule, source, target):
                    continue

                # 特殊：normalize_delimiter 使用 lambda
                if rule.name == "normalize_delimiter":
                    text, n = rule.pattern.subn(
                        lambda m: m.group(2).replace(m.group(1), ";").strip() + ";\n",
                        text)
                    counters[rule.name] = counters.get(rule.name, 0) + n
                    continue

                # 特殊：identifier 规则用目标引号
                if rule.name in ("convert_backtick_quote", "convert_double_quote"):
                    repl = target.identifier_quote + r"\1" + target.identifier_quote
                    if rule.scope == "global":
                        text, n = rule.pattern.subn(repl, text)
                    else:
                        text, n = _apply_line(text, rule, repl)
                    counters[rule.name] = counters.get(rule.name, 0) + n
                    continue

                # 标准规则
                if rule.scope == "global":
                    text, n = _apply_global(text, rule)
                else:
                    text, n = _apply_line(text, rule)
                counters[rule.name] = counters.get(rule.name, 0) + n
        return text, counters
```

---

## L3: 规则迁移（6 个文件并行）

### T6: 迁移规则到 converter/rules/，改用 Capability

**Files:** Create 6 个规则文件 + 更新 `converter/rules/__init__.py`

#### T6a: rules/cleanup.py（阶段1：预处理清理）

```python
"""阶段1: 预处理清理 — 删除源方言特有的注释/锁表/会话变量/DELIMITER。"""
import re
from converter.pipeline import Rule
from converter.capabilities import (
    CAP_VERSION_COMMENT, CAP_LOCK_TABLES, CAP_DELIMITER,
    CAP_SESSION_VARS, CAP_CHARSET, CAP_FOREIGN_KEY_CHECKS, CAP_ORACLE_HINTS,
)

CLEANUP_RULES: list[Rule] = [
    Rule("strip_version_comment", CAP_VERSION_COMMENT,
         re.compile(r"/\*!\d+\s.*?\*/;?", re.DOTALL),
         replacement="", scope="global", skip_insert=True,
         desc="剔除 mysqldump 的版本条件注释"),
    Rule("strip_lock_tables", CAP_LOCK_TABLES,
         re.compile(r"^\s*(LOCK\s+TABLES\s.*?;|UNLOCK\s+TABLES\s*;)\s*$",
                    re.IGNORECASE | re.MULTILINE),
         replacement="", scope="global", skip_insert=True,
         desc="删除 LOCK TABLES / UNLOCK TABLES"),
    Rule("normalize_delimiter", CAP_DELIMITER,
         re.compile(r"^\s*DELIMITER\s+(\S+)\s*$(.*?)\1\s*$\s*^\s*DELIMITER\s*;\s*$",
                    re.IGNORECASE | re.MULTILINE | re.DOTALL),
         replacement="", scope="global", skip_insert=True,
         desc="处理 DELIMITER 块"),
    Rule("strip_session_vars", CAP_SESSION_VARS,
         re.compile(r"^\s*SET\s+(@OLD_\w+|@@[\w.]+|@\w+)\s*=.*?;\s*$", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 SET @OLD_... / SET @@... 会话变量"),
    Rule("strip_set_names", CAP_CHARSET,
         re.compile(r"^\s*SET\s+NAMES\s+'?\w+'?(\s+COLLATE\s+'?\w+'?)?\s*;\s*$", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 SET NAMES xxx"),
    Rule("strip_foreign_key_checks", CAP_FOREIGN_KEY_CHECKS,
         re.compile(r"^\s*SET\s+FOREIGN_KEY_CHECKS\s*=\s*\d+\s*;\s*$", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 SET FOREIGN_KEY_CHECKS"),
    Rule("strip_oracle_hints", CAP_ORACLE_HINTS,
         re.compile(r"/\*\+.*?\*/", re.DOTALL),
         replacement="", scope="global", skip_insert=True,
         desc="删除 Oracle 优化器提示"),
]
```

#### T6b: rules/identifier.py（阶段2：标识符转换）

```python
"""阶段2: 标识符转换 — 引号风格转换。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_BACKTICK_QUOTE, CAP_DOUBLE_QUOTE

IDENTIFIER_RULES: list[Rule] = [
    Rule("convert_backtick_quote", CAP_BACKTICK_QUOTE,
         re.compile(r"`(\w+)`"),
         replacement="", scope="line", skip_insert=False,
         desc="将反引号标识符转为目标引号风格"),
    Rule("convert_double_quote", CAP_DOUBLE_QUOTE,
         re.compile(r'"(\w+)"'),
         replacement="", scope="line", skip_insert=False,
         desc="将双引号标识符转为目标引号风格"),
]
```

#### T6c: rules/type_mapping.py（阶段3：类型映射）

```python
"""阶段3: 类型映射 — 源方言特有类型 → 目标方言兼容类型。"""
import re
from converter.pipeline import Rule
from converter.capabilities import (
    CAP_TYPE_TINYINT, CAP_TYPE_MEDIUMINT, CAP_TYPE_INT_DISPLAY_WIDTH,
    CAP_TYPE_BIGINT_DISPLAY_WIDTH, CAP_TYPE_SMALLINT_DISPLAY_WIDTH,
    CAP_TYPE_INTEGER_DISPLAY_WIDTH, CAP_TYPE_TINYTEXT,
    CAP_TYPE_BLOB, CAP_TYPE_DATETIME, CAP_TYPE_TIMESTAMP,
    CAP_TYPE_YEAR, CAP_TYPE_DOUBLE, CAP_TYPE_FLOAT, CAP_TYPE_ENUM,
    CAP_TYPE_SET, CAP_TYPE_BIT, CAP_TYPE_BIT_LITERAL,
    CAP_TYPE_VARCHAR2, CAP_TYPE_NUMBER, CAP_TYPE_ORACLE_DATE,
    CAP_TYPE_LONG_RAW, CAP_TYPE_RAW,
    CAP_TYPE_SERIAL, CAP_TYPE_BOOLEAN, CAP_TYPE_BYTEA,
    CAP_TYPE_DOUBLE_PRECISION, CAP_TYPE_TEXT,
    CAP_AUTO_INCREMENT,
)

TYPE_MAPPING_RULES: list[Rule] = [
    # ── MySQL 整数类型 ──
    Rule("convert_tinyint_type", CAP_TYPE_TINYINT,
         re.compile(r"\btinyint\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="SMALLINT", scope="line", skip_insert=True,
         desc="TINYINT → SMALLINT"),
    Rule("convert_mediumint_type", CAP_TYPE_MEDIUMINT,
         re.compile(r"\bmediumint\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="INTEGER", scope="line", skip_insert=True,
         desc="MEDIUMINT → INTEGER"),
    Rule("convert_int_display_width", CAP_TYPE_INT_DISPLAY_WIDTH,
         re.compile(r"\bint\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="INTEGER", scope="line", skip_insert=True,
         desc="INT(N) → INTEGER"),
    Rule("convert_integer_display_width", CAP_TYPE_INTEGER_DISPLAY_WIDTH,
         re.compile(r"\binteger\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="INTEGER", scope="line", skip_insert=True,
         desc="INTEGER(N) → INTEGER"),
    Rule("convert_bigint_display_width", CAP_TYPE_BIGINT_DISPLAY_WIDTH,
         re.compile(r"\bbigint\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="BIGINT", scope="line", skip_insert=True,
         desc="BIGINT(N) → BIGINT"),
    Rule("convert_smallint_display_width", CAP_TYPE_SMALLINT_DISPLAY_WIDTH,
         re.compile(r"\bsmallint\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="SMALLINT", scope="line", skip_insert=True,
         desc="SMALLINT(N) → SMALLINT"),

    # ── MySQL 日期时间 ──
    Rule("convert_datetime_type", CAP_TYPE_DATETIME,
         re.compile(r"\bdatetime\b", re.IGNORECASE),
         replacement="TIMESTAMP", scope="line", skip_insert=True,
         desc="datetime → TIMESTAMP"),
    Rule("convert_year_type", CAP_TYPE_YEAR,
         re.compile(r"\byear\b(\s*\(\s*4\s*\))?", re.IGNORECASE),
         replacement="SMALLINT", scope="line", skip_insert=True,
         desc="YEAR → SMALLINT"),

    # ── MySQL 文本/二进制 ──
    Rule("convert_text_types", CAP_TYPE_TINYTEXT,
         re.compile(r"\b(tinytext|mediumtext|longtext)\b", re.IGNORECASE),
         replacement="TEXT", scope="line", skip_insert=True,
         desc="TINYTEXT/MEDIUMTEXT/LONGTEXT → TEXT"),
    Rule("convert_blob_types", CAP_TYPE_BLOB,
         re.compile(r"\b(tinyblob|mediumblob|longblob|blob)\b", re.IGNORECASE),
         replacement="BYTEA", scope="line", skip_insert=True,
         desc="BLOB 系列 → BYTEA"),

    # ── MySQL ENUM/SET ──
    Rule("convert_enum_type", CAP_TYPE_ENUM,
         re.compile(r"\benum\s*\([^)]*\)", re.IGNORECASE),
         replacement="VARCHAR(255)", scope="line", skip_insert=True,
         desc="ENUM → VARCHAR(255)"),
    Rule("convert_set_type", CAP_TYPE_SET,
         re.compile(r"\bset\s*\([^)]*\)", re.IGNORECASE),
         replacement="VARCHAR(255)", scope="line", skip_insert=True,
         desc="SET → VARCHAR(255)"),

    # ── MySQL 浮点 ──
    Rule("convert_double_type", CAP_TYPE_DOUBLE,
         re.compile(r"\bdouble\b(?!\s+precision)", re.IGNORECASE),
         replacement="DOUBLE PRECISION", scope="line", skip_insert=True,
         desc="DOUBLE → DOUBLE PRECISION"),
    Rule("convert_float_type", CAP_TYPE_FLOAT,
         re.compile(r"\bfloat\b(\s*\(\d+,\d+\))?", re.IGNORECASE),
         replacement="REAL", scope="line", skip_insert=True,
         desc="FLOAT → REAL"),

    # ── MySQL BIT ──
    Rule("convert_bit_type", CAP_TYPE_BIT,
         re.compile(r"\bbit\s*\(\s*1\s*\)", re.IGNORECASE),
         replacement="SMALLINT", scope="line", skip_insert=False,
         desc="bit(1) → SMALLINT"),
    Rule("convert_bit_literal", CAP_TYPE_BIT_LITERAL,
         re.compile(r"\bb'(0|1)'", re.IGNORECASE),
         replacement=r"'\1'", scope="line", skip_insert=False,
         desc="b'0'/b'1' → 普通整数"),

    # ── MySQL AUTO_INCREMENT → SQLite AUTOINCREMENT ──
    Rule("convert_auto_increment", CAP_AUTO_INCREMENT,
         re.compile(r"\bAUTO_INCREMENT\b", re.IGNORECASE),
         replacement="AUTOINCREMENT", scope="line", skip_insert=True,
         desc="AUTO_INCREMENT → AUTOINCREMENT"),

    # ── Oracle 类型 ──
    Rule("convert_long_raw_type", CAP_TYPE_LONG_RAW,
         re.compile(r"\blong\s+raw\b", re.IGNORECASE),
         replacement="BYTEA", scope="line", skip_insert=True,
         desc="LONG RAW → BYTEA"),
    Rule("convert_varchar2_type", CAP_TYPE_VARCHAR2,
         re.compile(r"\b(varchar2|nvarchar2|varchar|nvarchar|char|nchar|clob|nclob|long)\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="TEXT", scope="line", skip_insert=True,
         desc="Oracle 字符串 → TEXT"),
    Rule("convert_oracle_number_precision", CAP_TYPE_NUMBER,
         re.compile(r"\bnumber\b(\s*\(\d+,\d+\))", re.IGNORECASE),
         replacement=r"REAL", scope="line", skip_insert=True,
         desc="NUMBER(N,M) → REAL"),
    Rule("convert_oracle_number", CAP_TYPE_NUMBER,
         re.compile(r"\bnumber\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="INTEGER", scope="line", skip_insert=True,
         desc="NUMBER(N) → INTEGER"),
    Rule("convert_oracle_date_type", CAP_TYPE_ORACLE_DATE,
         re.compile(r"\bdate\b", re.IGNORECASE),
         replacement="TIMESTAMP", scope="line", skip_insert=True,
         desc="Oracle DATE → TIMESTAMP"),
    Rule("convert_raw_type", CAP_TYPE_RAW,
         re.compile(r"\b(raw|blob)\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="BLOB", scope="line", skip_insert=True,
         desc="RAW/BLOB → BLOB"),

    # ── PG 类型 → 其他 ──
    Rule("convert_serial_type", CAP_TYPE_SERIAL,
         re.compile(r"\b(serial|bigserial|smallserial)\b", re.IGNORECASE),
         replacement="INTEGER", scope="line", skip_insert=True,
         desc="SERIAL → INTEGER"),
    Rule("convert_boolean_type", CAP_TYPE_BOOLEAN,
         re.compile(r"\bboolean\b", re.IGNORECASE),
         replacement="INTEGER", scope="line", skip_insert=True,
         desc="BOOLEAN → INTEGER"),
    Rule("convert_bytea_type", CAP_TYPE_BYTEA,
         re.compile(r"\bbytea\b", re.IGNORECASE),
         replacement="BLOB", scope="line", skip_insert=True,
         desc="BYTEA → BLOB"),
    Rule("convert_timestamp_type", CAP_TYPE_TIMESTAMP,
         re.compile(r"\btimestamp\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="TEXT", scope="line", skip_insert=True,
         desc="TIMESTAMP → TEXT"),
    Rule("convert_double_precision", CAP_TYPE_DOUBLE_PRECISION,
         re.compile(r"\bdouble\s+precision\b", re.IGNORECASE),
         replacement="REAL", scope="line", skip_insert=True,
         desc="DOUBLE PRECISION → REAL"),
    Rule("convert_pg_text_types", CAP_TYPE_TEXT,
         re.compile(r"\b(varchar|char|text)\b(\s*\(\d+\))?", re.IGNORECASE),
         replacement="TEXT", scope="line", skip_insert=True,
         desc="PG 字符串 → TEXT"),
    Rule("convert_pg_integer_types", CAP_TYPE_SERIAL,
         re.compile(r"\b(smallint|integer|int|bigint|int2|int4|int8)\b", re.IGNORECASE),
         replacement="INTEGER", scope="line", skip_insert=True,
         desc="PG 整数 → INTEGER"),
]
```

#### T6d: rules/modifier.py（阶段4：修饰符清理）

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
    Rule("strip_unsigned", CAP_UNSIGNED,
         re.compile(r"\s+unsigned\b", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 UNSIGNED"),
    Rule("strip_zerofill", CAP_ZEROFILL,
         re.compile(r"\s+zerofill\b", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 ZEROFILL"),
    Rule("strip_engine_clause", CAP_ENGINE,
         re.compile(r"\s*ENGINE\s*=\s*\w+", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 ENGINE=xxx"),
    Rule("strip_default_charset", CAP_CHARSET,
         re.compile(r"\s*(DEFAULT\s+)?(CHARACTER\s+SET|CHARSET)\s*=?\s*\w+(\s+COLLATE\s*=?\s*\w+)?", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 DEFAULT CHARSET / COLLATE"),
    Rule("strip_collate_standalone", CAP_COLLATE,
         re.compile(r"\s+COLLATE\s+\w+", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除独立 COLLATE"),
    Rule("strip_column_charset", CAP_CHARSET,
         re.compile(r"\s+(CHARACTER\s+SET|CHARSET)\s+\w+(\s+COLLATE\s+\w+)?", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除列级 CHARACTER SET / COLLATE"),
    Rule("strip_cascade", CAP_CASCADE,
         re.compile(r"\s+CASCADE\b", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 CASCADE"),
    Rule("strip_on_update_timestamp", CAP_ON_UPDATE_TIMESTAMP,
         re.compile(r"\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP(\s*\(\d+\))?", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 ON UPDATE CURRENT_TIMESTAMP"),
    Rule("strip_table_auto_increment", CAP_AUTO_INCREMENT,
         re.compile(r"\s*AUTO_INCREMENT\s*=\s*\d+", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除表级 AUTO_INCREMENT=N"),
    Rule("strip_row_format", CAP_ROW_FORMAT,
         re.compile(r"\s*(ROW_FORMAT|KEY_BLOCK_SIZE|PACK_KEYS|STATS_PERSISTENT|STATS_AUTO_RECALC|DELAY_KEY_WRITE)\s*=\s*\w+", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 ROW_FORMAT 等表选项"),
    Rule("strip_pg_type_cast", CAP_TYPE_PG_TYPE_CAST,
         re.compile(r"::\w+"),
         replacement="", scope="line", skip_insert=False,
         desc="删除 PG ::type 类型转换"),
    Rule("strip_pg_extension", CAP_TYPE_EXTENSION,
         re.compile(r"^\s*CREATE\s+EXTENSION\s+.*?;\s*$", re.IGNORECASE | re.MULTILINE),
         replacement="", scope="global", skip_insert=True,
         desc="删除 CREATE EXTENSION"),
]
```

#### T6e: rules/constraint.py（阶段5：约束适配）

```python
"""阶段5: 约束/索引适配。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_USING_BTREE

CONSTRAINT_RULES: list[Rule] = [
    Rule("strip_using_btree", CAP_USING_BTREE,
         re.compile(r"\s*USING\s+BTREE", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 USING BTREE"),
]
```

#### T6f: rules/postprocess.py（阶段6：后处理）

```python
"""阶段6: 后处理 — 最终语法修正。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_AUTO_INCREMENT

POSTPROCESS_RULES: list[Rule] = [
    Rule("fix_autoincrement_syntax", CAP_AUTO_INCREMENT,
         re.compile(r"\bNOT\s+NULL\s+AUTOINCREMENT\b", re.IGNORECASE),
         replacement="AUTOINCREMENT", scope="line", skip_insert=True,
         desc="去除 AUTOINCREMENT 前的 NOT NULL"),
]
```

#### T6g: 更新 rules/__init__.py

```python
"""规则包 — 汇总所有阶段规则。"""
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

---

## L4: 入口更新（2 个任务并行）

### T7: 更新 convert.py

**Files:** Modify `convert.py`

**变更：**

1. 替换导入（删除 `from dialects import get_dialect` 和 `from rules import RULES`）：
```python
from converter.registry import get_dialect
from converter.pipeline import Pipeline
from converter.rules import ALL_STAGES

_pipeline = Pipeline(ALL_STAGES)
```

2. 重写 `convert()` 函数：
```python
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

3. 更新 `main()` 中 verbose 输出：
```python
if args.verbose:
    print("Rule hit counts:")
    for name, n in sorted(counters.items()):
        if n > 0:
            print(f"  {name:<32} {n:>6}")
```

4. 删除旧函数：`filter_rules()`, `apply_global_rules()`, `apply_line_rules()`

### T8: 更新 tests/test_sniff.py

**Files:** Modify `tests/test_sniff.py`

替换导入：
```python
from converter.registry import get_dialect
from converter.dialects.pgsql import PgsqlDialect
```

---

## L5: 清理 + 验证

### T9: 删除旧文件

```bash
rm -rf dialects/ rules.py
```

### T10: 统一验证并提交

```bash
# 1. 导入检查
python -c "from convert import convert; print('convert.py OK')"

# 2. 运行测试
python -m unittest tests.test_sniff -v

# 3. 端到端：MySQL → Kingbase（与 sample_output.sql 对比）
python convert.py tests/sample_input.sql --target-mode kingbase -o tests/_v1.sql --overwrite
diff tests/sample_output.sql tests/_v1.sql && echo "MySQL→Kingbase: MATCH" || echo "MySQL→Kingbase: DIFF"

# 4. 端到端：MySQL → PGSQL
python convert.py tests/sample_input.sql --target-mode pgsql -o tests/_v2.sql --overwrite

# 5. 端到端：Oracle → PGSQL（与 actual_sniff_oracle.sql 对比）
python convert.py tests/sniff_oracle_input.sql --target-mode pgsql -o tests/_v3.sql --overwrite
diff tests/actual_sniff_oracle.sql tests/_v3.sql && echo "Oracle→PGSQL: MATCH" || echo "Oracle→PGSQL: DIFF"

# 6. 端到端：MySQL → SQLite（验证 .db 文件）
python -c "
import tempfile, os, sqlite3
f = tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8')
f.write('CREATE TABLE t (id INT AUTO_INCREMENT, name VARCHAR(64), PRIMARY KEY (id)) ENGINE=InnoDB;\\nINSERT INTO t VALUES (1,\\\"test\\\");\\n')
f.close()
os.system(f'python convert.py {f.name} --target-mode sqlite -o {f.name}_out --overwrite')
db = sqlite3.connect(f.name + '_out.db')
print('SQLite tables:', db.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())
print('SQLite rows:', db.execute('SELECT * FROM t').fetchall())
db.close()
for ext in ['', '.sql', '.db']:
    try: os.unlink(f.name + '_out' + ext)
    except: pass
os.unlink(f.name)
print('MySQL→SQLite: OK')
"

# 7. 清理临时文件
rm -f tests/_v1.sql tests/_v2.sql tests/_v3.sql

# 8. 统计
echo "--- 统计 ---"
python -c "from converter.rules import ALL_STAGES; print('总规则:', sum(len(s) for s in ALL_STAGES))"
find converter -name "*.py" | xargs wc -l | tail -1

# 9. 提交
git add -A
git commit -m "refactor: Dialect + Capability + Rule Engine architecture (Phase 1)"
```