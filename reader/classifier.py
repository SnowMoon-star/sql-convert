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

# 用于清理前导注释和空白字符的正则
_LEADING_COMMENT_PAT = re.compile(
    r"^(\s+|(--[^\n]*\n?)|(#[^\n]*\n?)|(/\*.*?\*/))",
    re.DOTALL | re.IGNORECASE
)

def _clean_for_classification(sql: str) -> str:
    """循环剥离 SQL 开头的所有空白和注释，获取干净的起始文本。"""
    last_len = -1
    while len(sql) != last_len:
        last_len = len(sql)
        sql = _LEADING_COMMENT_PAT.sub("", sql)
    return sql.strip()

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
