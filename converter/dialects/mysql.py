"""MySQL 方言策略。"""
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

    def format_drop_table(self, table: TableBlock) -> str:
        return f"DROP TABLE IF EXISTS {self.quote_identifier(table.name)} CASCADE;"

    def format_create_table(self, table: TableBlock) -> str:
        lines: list[str] = []
        lines.append(f"CREATE TABLE {self.quote_identifier(table.name)} (")

        # 列定义
        col_lines: list[str] = []
        for col in table.columns:
            col_str = f"  {self.quote_identifier(col.name)} {col.type_}"
            if col.comment:
                col_str += f" COMMENT '{self.escape_comment(col.comment)}'"
            col_lines.append(col_str)

        # 主键
        if table.primary_key:
            pk_cols = ", ".join(self.quote_identifier(c) for c in table.primary_key)
            col_lines.append(f"  PRIMARY KEY ({pk_cols})")

        lines.append(",\n".join(col_lines))
        lines.append(")")
        if table.comment:
            lines[-1] += f" COMMENT='{self.escape_comment(table.comment)}'"
        lines[-1] += ";"
        return "\n".join(lines)

    def format_indexes(self, table: TableBlock) -> list[str]:
        extra_indexes = table.indexes
        if not extra_indexes:
            return []

        stmts: list[str] = []
        for idx in extra_indexes:
            key_type = "UNIQUE KEY" if idx.unique else "KEY"
            cols = ", ".join(self.quote_identifier(c) for c in idx.columns)
            stmt = f"ALTER TABLE {self.quote_identifier(table.name)} ADD {key_type} {self.quote_identifier(idx.name)} ({cols})"
            if idx.comment:
                stmt += f" COMMENT '{self.escape_comment(idx.comment)}'"
            stmt += ";"
            stmts.append(stmt)
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
