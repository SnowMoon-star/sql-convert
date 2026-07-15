"""SQL 语句分类器 — 将 SQL 语句归类为 DDL、DML、COMMENT 等。"""
from __future__ import annotations
import re
from enum import Enum, auto

class StatementType(Enum):
    DDL = auto()
    DML = auto()
    COMMENT = auto()
    INDEX = auto()
    UNKNOWN = auto()

# 一次性匹配并剥离所有前导注释/空白的正则（使用 + 量词替代外层循环，避免 O(n²) DoS）
_LEADING_COMMENTS_PAT = re.compile(
    r"^(?:\s+|--[^\n]*\n?|#[^\n]*\n?|/\*.*?\*/)+",
    re.DOTALL | re.IGNORECASE
)

def _clean_for_classification(sql: str) -> str:
    """单次剥离 SQL 开头的所有空白和注释块，获取干净的起始文本。"""
    return _LEADING_COMMENTS_PAT.sub("", sql).strip()

def classify_statement(sql: str) -> StatementType:
    """对 SQL 语句进行分类。"""
    clean_sql = _clean_for_classification(sql)
    if not clean_sql:
        return StatementType.UNKNOWN

    upper_sql = clean_sql.upper()

    # 1. DML
    if upper_sql.startswith("INSERT") or upper_sql.startswith("UPDATE") or \
       upper_sql.startswith("DELETE") or upper_sql.startswith("SELECT") or \
       upper_sql.startswith("REPLACE"):
        return StatementType.DML

    # 2. COMMENT
    if upper_sql.startswith("COMMENT"):
        return StatementType.COMMENT

    # 3. INDEX
    if (upper_sql.startswith("CREATE") and "INDEX" in upper_sql[:50]) or \
       upper_sql.startswith("DROP INDEX"):
        return StatementType.INDEX

    # 4. DDL
    if upper_sql.startswith("CREATE") or upper_sql.startswith("DROP") or \
       upper_sql.startswith("ALTER") or upper_sql.startswith("TRUNCATE") or \
       upper_sql.startswith("RENAME"):
        return StatementType.DDL

    return StatementType.UNKNOWN
