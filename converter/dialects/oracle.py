from __future__ import annotations
from converter.dialects.base import BaseDialect
from converter.capabilities import (
    CAP_ORACLE_HINTS, CAP_DOUBLE_QUOTE,
    CAP_TYPE_VARCHAR2, CAP_TYPE_NVARCHAR2, CAP_TYPE_NUMBER,
    CAP_TYPE_CLOB, CAP_TYPE_NCLOB, CAP_TYPE_BLOB_ORACLE,
    CAP_TYPE_LONG, CAP_TYPE_LONG_RAW, CAP_TYPE_RAW, CAP_TYPE_NCHAR,
    CAP_TYPE_ORACLE_DATE,
)
from converter.registry import register
from sql_parser import TableBlock


@register
class OracleDialect(BaseDialect):
    """Oracle 方言策略实现（主要用于源方言识别和规则匹配）。"""

    family = "oracle"
    identifier_quote = '"'
    capabilities = {
        CAP_ORACLE_HINTS, CAP_DOUBLE_QUOTE,
        CAP_TYPE_VARCHAR2, CAP_TYPE_NVARCHAR2, CAP_TYPE_NUMBER,
        CAP_TYPE_CLOB, CAP_TYPE_NCLOB, CAP_TYPE_BLOB_ORACLE,
        CAP_TYPE_LONG, CAP_TYPE_LONG_RAW, CAP_TYPE_RAW, CAP_TYPE_NCHAR,
        CAP_TYPE_ORACLE_DATE,
    }

    def quote_identifier(self, name: str) -> str:
        return f'"{name}"'

    def format_drop_table(self, table: TableBlock) -> str:
        return f"DROP TABLE {self.quote_identifier(table.name)} CASCADE CONSTRAINTS;"

    def format_create_table(self, table: TableBlock) -> str:
        lines: list[str] = []
        lines.append(f"CREATE TABLE {self.quote_identifier(table.name)} (")
        col_lines: list[str] = []
        for col in table.columns:
            col_lines.append(f"  {self.quote_identifier(col.name)} {col.type_}")
        if table.primary_key:
            pk_cols = ", ".join(self.quote_identifier(c) for c in table.primary_key)
            col_lines.append(f"  PRIMARY KEY ({pk_cols})")
        lines.append(",\n".join(col_lines))
        lines.append(");")
        return "\n".join(lines)

    def format_indexes(self, table: TableBlock) -> list[str]:
        return []

    def format_foreign_keys(self, table: TableBlock) -> list[str]:
        return []

    def format_inserts(self, table: TableBlock) -> list[str]:
        return ["-- 无数据", ""]
