# SQL 方言转换器 — 第二阶段重构设计（Canonical Type + Function Mapping）

## 目标

将 Phase 1 中 `type_mapping.py` 的 30 条硬编码替换规则，替换为 **Source Type → Canonical Type → Target Type** 的映射引擎。同时引入 **Canonical Function Mapping**，处理函数名替换。

### 设计目标

- 类型映射从规则中移除，改为方言内置映射表
- 函数映射用同样的 Canonical 体系，简单替换走映射引擎，结构变换保留为 Rule
- 新增数据库时，只需声明自己的 `canonical_to_type` 和 `canonical_to_function` 表
- 规则数从 53 进一步减少

---

## Canonical Type 体系

### 规范类型定义（`converter/mappings/types.py`）

```python
"""Canonical 类型名常量 + 映射引擎。"""
import re

# ── 规范类型 ──
INTEGER_8 = "Integer8"
INTEGER_16 = "Integer16"
INTEGER_32 = "Integer32"
INTEGER_64 = "Integer64"
REAL_32 = "Real32"
REAL_64 = "Real64"
DECIMAL = "Decimal"
TEXT = "Text"
DATE_TIME = "DateTime"
DATE = "Date"
TIME = "Time"
BLOB = "Blob"
ENUM = "Enum"
SET = "Set"
BIT = "Bit"
BOOLEAN = "Boolean"


def build_type_pattern(dialect) -> re.Pattern:
    """从方言的 type_to_canonical 键构建匹配正则。"""
    # 按长度降序排列，确保 mediumint 在 int 之前匹配
    keys = sorted(dialect.type_to_canonical.keys(), key=len, reverse=True)
    return re.compile(
        r"\b(" + "|".join(re.escape(k) for k in keys) + r")\b(\s*\(\d+(,\d+)?\))?",
        re.IGNORECASE,
    )


def map_types(text: str, source_dialect, target_dialect) -> tuple[str, int]:
    """将文本中所有源类型替换为目标类型（自动去除显示宽度）。
    返回 (new_text, hit_count)。"""
    pattern = build_type_pattern(source_dialect)

    def repl(m):
        src_type = m.group(1).lower()
        canonical = source_dialect.type_to_canonical.get(src_type)
        if canonical:
            target_type = target_dialect.canonical_to_type.get(canonical)
            if target_type:
                return target_type
        return m.group(0)

    new_text, n = pattern.subn(repl, text)
    return new_text, n
```

### 方言映射表

每个方言声明两张映射表：

**源方言**（MySQL、Oracle）：`type_to_canonical`
```python
# MysqlDialect 新增
type_to_canonical: dict[str, str] = {
    "tinyint": "Integer8", "smallint": "Integer16",
    "mediumint": "Integer32", "int": "Integer32", "integer": "Integer32",
    "bigint": "Integer64", "float": "Real32", "double": "Real64",
    "decimal": "Decimal", "numeric": "Decimal",
    "varchar": "Text", "char": "Text", "tinytext": "Text",
    "mediumtext": "Text", "longtext": "Text", "text": "Text",
    "datetime": "DateTime", "timestamp": "DateTime",
    "date": "Date", "time": "Time", "year": "Integer16",
    "blob": "Blob", "tinyblob": "Blob", "mediumblob": "Blob", "longblob": "Blob",
    "binary": "Blob", "varbinary": "Blob",
    "enum": "Enum", "set": "Set", "bit": "Bit",
    "bool": "Boolean", "boolean": "Boolean",
}
```

**目标方言**（Kingbase、PGSQL、SQLite）：`canonical_to_type`
```python
# PgsqlDialect 新增
canonical_to_type: dict[str, str] = {
    "Integer8": "SMALLINT", "Integer16": "SMALLINT",
    "Integer32": "INTEGER", "Integer64": "BIGINT",
    "Real32": "REAL", "Real64": "DOUBLE PRECISION",
    "Decimal": "NUMERIC", "Text": "TEXT",
    "DateTime": "TIMESTAMP", "Date": "DATE", "Time": "TIME",
    "Blob": "BYTEA", "Enum": "VARCHAR(255)", "Set": "VARCHAR(255)",
    "Bit": "SMALLINT", "Boolean": "BOOLEAN",
}

# SqliteDialect 新增
canonical_to_type: dict[str, str] = {
    "Integer8": "INTEGER", "Integer16": "INTEGER",
    "Integer32": "INTEGER", "Integer64": "INTEGER",
    "Real32": "REAL", "Real64": "REAL",
    "Decimal": "REAL", "Text": "TEXT",
    "DateTime": "TEXT", "Date": "TEXT", "Time": "TEXT",
    "Blob": "BLOB", "Enum": "TEXT", "Set": "TEXT",
    "Bit": "INTEGER", "Boolean": "INTEGER",
}
```

---

## Canonical Function 体系

### 规范函数定义（`converter/mappings/functions.py`）

```python
"""Canonical 函数名常量 + 简单映射引擎。"""
import re

# ── 规范函数（简单替换类）──
CURRENT_TIMESTAMP = "CurrentTimestamp"
CURRENT_DATE = "CurrentDate"
CURRENT_TIME = "CurrentTime"
COALESCE = "Coalesce"
CONCAT_WS = "ConcatWs"
GROUP_CONCAT = "GroupConcat"
DATE_FORMAT = "DateFormat"
STR_TO_DATE = "StrToDate"
UNIX_TIMESTAMP = "UnixTimestamp"
FROM_UNIXTIME = "FromUnixtime"
UUID = "Uuid"
LENGTH = "Length"
CHAR_LENGTH = "CharLength"
SUBSTRING_INDEX = "SubstringIndex"
FIND_IN_SET = "FindInSet"
REGEXP = "Regexp"


def build_function_pattern(dialect) -> re.Pattern:
    """从方言的 function_to_canonical 键构建匹配正则。"""
    keys = sorted(dialect.function_to_canonical.keys(), key=len, reverse=True)
    return re.compile(
        "|".join(re.escape(k) for k in keys),
        re.IGNORECASE,
    )


def map_functions(text: str, source_dialect, target_dialect) -> tuple[str, int]:
    """将文本中所有源函数替换为目标函数。返回 (new_text, hit_count)。"""
    pattern = build_function_pattern(source_dialect)

    def repl(m):
        src_func = m.group(0)
        for key, canonical in source_dialect.function_to_canonical.items():
            if key.upper() == src_func.upper():
                target_func = target_dialect.canonical_to_function.get(canonical)
                if target_func:
                    return target_func
        return m.group(0)

    new_text, n = pattern.subn(repl, text)
    return new_text, n
```

### 方言映射表

```python
# MysqlDialect 新增
function_to_canonical: dict[str, str] = {
    "NOW()": "CurrentTimestamp", "CURDATE()": "CurrentDate",
    "CURTIME()": "CurrentTime", "IFNULL": "Coalesce",
    "CONCAT_WS": "ConcatWs", "GROUP_CONCAT": "GroupConcat",
    "DATE_FORMAT": "DateFormat", "STR_TO_DATE": "StrToDate",
    "UNIX_TIMESTAMP": "UnixTimestamp", "FROM_UNIXTIME": "FromUnixtime",
    "UUID()": "Uuid", "LENGTH": "Length", "CHAR_LENGTH": "CharLength",
}

# PgsqlDialect 新增
canonical_to_function: dict[str, str] = {
    "CurrentTimestamp": "CURRENT_TIMESTAMP",
    "CurrentDate": "CURRENT_DATE",
    "CurrentTime": "CURRENT_TIME",
    "Coalesce": "COALESCE",
    "ConcatWs": "CONCAT_WS",
    "GroupConcat": "STRING_AGG",
    "DateFormat": "TO_CHAR",
    "StrToDate": "TO_DATE",
    "UnixTimestamp": "EXTRACT(EPOCH FROM NOW())",
    "FromUnixtime": "TO_TIMESTAMP",
    "Uuid": "GEN_RANDOM_UUID()",
    "Length": "LENGTH",
    "CharLength": "CHAR_LENGTH",
}

# SqliteDialect 新增
canonical_to_function: dict[str, str] = {
    "CurrentTimestamp": "CURRENT_TIMESTAMP",
    "CurrentDate": "DATE('now')",
    "CurrentTime": "TIME('now')",
    "Coalesce": "IFNULL",
    "Uuid": "lower(hex(randomblob(16)))",
    "Length": "LENGTH",
    "CharLength": "LENGTH",
    "GroupConcat": "GROUP_CONCAT",
}
```

---

## Pipeline 变更

### 阶段调整

```
旧（7 阶段）:
1. cleanup      2. identifier   3. type_mapping(30条Rule)
4. modifier     5. constraint   6. postprocess

新（7 阶段）:
1. cleanup      2. identifier   3. type_mapping(Mapping引擎，0条Rule)
4. func_mapping(Mapping引擎)    5. modifier     6. constraint(+结构变换Rule)
7. postprocess
```

### Pipeline.run 变更

```python
def run(self, text, source, target):
    # 阶段1-2: 不变
    # 阶段3: 类型映射（引擎）
    text, n = map_types(text, source, target)
    counters["_type_mapping"] = n
    # 阶段4: 函数映射（引擎）
    text, n = map_functions(text, source, target)
    counters["_func_mapping"] = n
    # 阶段5-7: 不变（Rule 体系）
```

### BaseDialect 新增属性

```python
class BaseDialect:
    # 类型映射表（子类覆盖）
    type_to_canonical: dict[str, str] = {}
    canonical_to_type: dict[str, str] = {}

    # 函数映射表（子类覆盖）
    function_to_canonical: dict[str, str] = {}
    canonical_to_function: dict[str, str] = {}
```

---

## 文件变化一览

```
新建:
  converter/mappings/types.py       # Canonical 类型常量 + map_types()
  converter/mappings/functions.py   # Canonical 函数常量 + map_functions()

修改:
  converter/dialects/base.py        # + 4 个映射表属性
  converter/dialects/mysql.py       # + type_to_canonical + function_to_canonical
  converter/dialects/oracle.py      # + type_to_canonical + function_to_canonical
  converter/dialects/kingbase.py    # + canonical_to_type + canonical_to_function
  converter/dialects/pgsql.py       # + canonical_to_type + canonical_to_function
  converter/dialects/sqlite.py      # + canonical_to_type + canonical_to_function
  converter/pipeline.py             # + 阶段4 func_mapping
  converter/rules/__init__.py       # + func_mapping 阶段
  converter/rules/constraint.py     # + 5条结构变换函数 Rule
  convert.py                        # 删除 filter_rules 残留引用（如有）

删除:
  converter/rules/type_mapping.py   # 30条规则 → 方言映射表（文件删除）
```

---

## 规则数变化

| 文件 | Phase 1 | Phase 2 | 变化 |
|---|---|---|---|
| cleanup.py | 7 | 7 | 不变 |
| identifier.py | 2 | 2 | 不变 |
| type_mapping.py | 30 | **0** | 删除，移到映射表 |
| func_mapping | — | **0** | 引擎级别 |
| modifier.py | 12 | 12 | 不变 |
| constraint.py | 1 | ~6 | +5 结构变换函数 |
| postprocess.py | 1 | 1 | 不变 |
| **总计** | **53** | **~28** | |

---

## 结构变换函数（保留为 Rule）

以下 5 个函数需要结构变换，不适合简单映射，保留为 constraint 阶段的 Rule：

| 函数 | 源 | 目标 | 变换 |
|---|---|---|---|
| `IF(cond,a,b)` | MySQL | PG | `CASE WHEN cond THEN a ELSE b END` |
| `LIMIT offset, count` | MySQL | PG | `LIMIT count OFFSET offset` |
| `SUBSTRING_INDEX(str,delim,n)` | MySQL | PG | `SPLIT_PART(str,delim,n)` |
| `FIND_IN_SET(str,list)` | MySQL | PG | `str = ANY(STRING_TO_ARRAY(list,','))` |
| `REGEXP` 运算符 | MySQL | PG | `~` 运算符 |

---

## 验证标准

- Phase 1 所有测试继续通过
- MySQL→Kingbase、MySQL→PGSQL、Oracle→PGSQL、MySQL→SQLite 端到端输出与 Phase 1 一致
- 新增数据库时仅需声明映射表，无需修改规则文件
- 规则总数从 53 降至 ~28