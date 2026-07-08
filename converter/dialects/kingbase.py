"""Kingbase (金仓数据库) 方言策略。"""
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

    def quote_identifier(self, name: str) -> str:
        # 使用符合 SQL 标准的双引号
        return f'"{name}"'

    def format_drop_table(self, table: TableBlock) -> str:
        return f"DROP TABLE IF EXISTS {self.quote_identifier(table.name)} CASCADE;"

    def format_create_table(self, table: TableBlock) -> str:
        lines: list[str] = []
        lines.append(f"CREATE TABLE {self.quote_identifier(table.name)} (")

        # 列定义
        col_lines: list[str] = []
        for col in table.columns:
            # Kingbase 下字段不需要 COMMENT 关键字，字段注释使用独立的 COMMENT ON COLUMN 语句
            col_str = f"  {self.quote_identifier(col.name)} {col.type_}"
            col_lines.append(col_str)

        # 主键
        if table.primary_key:
            pk_cols = ", ".join(self.quote_identifier(c) for c in table.primary_key)
            col_lines.append(f"  PRIMARY KEY ({pk_cols})")

        lines.append(",\n".join(col_lines))
        lines.append(");")

        # 处理表注释与列注释 (作为独立 DDL 语句追加)
        comments: list[str] = []
        table_q = self.quote_identifier(table.name)
        if table.comment:
            comments.append(f"COMMENT ON TABLE {table_q} IS '{self.escape_comment(table.comment)}';")
        for col in table.columns:
            if col.comment:
                col_q = self.quote_identifier(col.name)
                comments.append(f"COMMENT ON COLUMN {table_q}.{col_q} IS '{self.escape_comment(col.comment)}';")

        if comments:
            lines.append("")
            lines.extend(comments)

        return "\n".join(lines)

    def format_indexes(self, table: TableBlock) -> list[str]:
        extra_indexes = table.indexes
        if not extra_indexes:
            return []

        stmts: list[str] = []
        for idx in extra_indexes:
            # Kingbase 中使用 CREATE INDEX 语句而非 ALTER TABLE ADD KEY
            uniq_str = "UNIQUE " if idx.unique else ""
            cols = ", ".join(self.quote_identifier(c) for c in idx.columns)
            stmt = f"CREATE {uniq_str}INDEX {self.quote_identifier(idx.name)} ON {self.quote_identifier(table.name)} ({cols});"
            stmts.append(stmt)
            if idx.comment:
                stmts.append(f"COMMENT ON INDEX {self.quote_identifier(idx.name)} IS '{self.escape_comment(idx.comment)}';")
        return stmts

    def format_foreign_keys(self, table: TableBlock) -> list[str]:
        if not table.foreign_keys:
            return []

        stmts: list[str] = []
        for i, fk in enumerate(table.foreign_keys, start=1):
            cols = ", ".join(self.quote_identifier(c) for c in fk.columns)
            ref_cols = ", ".join(self.quote_identifier(c) for c in fk.ref_columns)
            fk_name = fk.name or f"fk_{table.name}_{i}"
            stmt = (
                f"ALTER TABLE {self.quote_identifier(table.name)} ADD CONSTRAINT {self.quote_identifier(fk_name)} "
                f"FOREIGN KEY ({cols}) REFERENCES {self.quote_identifier(fk.ref_table)} ({ref_cols})"
            )
            if fk.on_delete:
                stmt += f" ON DELETE {fk.on_delete}"
            if fk.on_update:
                stmt += f" ON UPDATE {fk.on_update}"
            stmt += ";"
            stmts.append(stmt)
        return stmts

    def format_inserts(self, table: TableBlock) -> list[str]:
        if not table.inserts:
            return ["-- 无数据", ""]

        stmts: list[str] = []
        for insert_block in table.inserts:
            if insert_block.columns:
                cols_str = f" ({', '.join(self.quote_identifier(c) for c in insert_block.columns)})"
            else:
                cols_str = ""

            value_lines: list[str] = []
            for row in insert_block.values:
                formatted_values: list[str] = []
                for val in row:
                    if val.upper() == "NULL":
                        formatted_values.append("NULL")
                    else:
                        formatted_values.append(val)
                value_lines.append(f"({', '.join(formatted_values)})")

            vals_part = ",\n".join(value_lines) + ";"
            stmts.append(f"INSERT INTO {self.quote_identifier(table.name)}{cols_str} VALUES\n{vals_part}")
        return stmts
