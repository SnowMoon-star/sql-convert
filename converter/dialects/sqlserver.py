from __future__ import annotations
from converter.dialects.base import BaseDialect
from converter.registry import register
from model import TableBlock


@register
class SqlServerDialect(BaseDialect):
    """SQLServer (Microsoft SQL Server) 方言策略实现。"""

    family = "sqlserver"
    identifier_quote = '"'
    
    # 基础类型映射
    type_to_canonical: dict[str, str] = {
        "varchar": "Text", "nvarchar": "Text", "char": "Text", "nchar": "Text",
        "text": "Text", "ntext": "Text",
        "int": "Integer32", "bigint": "Integer64", "smallint": "Integer16",
        "tinyint": "Integer8", "decimal": "Decimal", "numeric": "Decimal",
        "float": "Real64", "real": "Real32",
        "datetime": "DateTime", "datetime2": "DateTime", "date": "DateTime",
        "image": "Blob", "binary": "Blob", "varbinary": "Blob",
    }

    def quote_identifier(self, name: str) -> str:
        # 支持用双引号作为 SQLServer 的 ANSI 标识符引用
        return f'"{name}"'

    def format_drop_table(self, table: TableBlock) -> str:
        return f"DROP TABLE {self.quote_identifier(table.name)};"

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
