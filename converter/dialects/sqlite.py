"""SQLite 方言策略。"""
from __future__ import annotations

from converter.dialects.base import BaseDialect
from converter.capabilities import (
    CAP_DOUBLE_QUOTE, CAP_TYPE_AUTOINCREMENT, CAP_TYPE_BLOB,
)
from converter.registry import register
from sql_parser import TableBlock


@register
class SqliteDialect(BaseDialect):
    """SQLite 方言策略实现。

    SQLite 与其他方言的关键差异：
    - 外键必须在 CREATE TABLE 内联定义（不支持 ALTER TABLE ADD CONSTRAINT）
    - DROP TABLE 不支持 CASCADE
    - 不支持 COMMENT ON 语句
    - 类型系统简化为 INTEGER / REAL / TEXT / BLOB
    - AUTOINCREMENT 关键字（非 AUTO_INCREMENT）
    """

    family = "sqlite"
    identifier_quote = '"'
    capabilities = {
        CAP_DOUBLE_QUOTE, CAP_TYPE_AUTOINCREMENT, CAP_TYPE_BLOB,
    }

    canonical_to_type: dict[str, str] = {
        "Integer8": "INTEGER", "Integer16": "INTEGER",
        "Integer32": "INTEGER", "Integer64": "INTEGER",
        "Real32": "REAL", "Real64": "REAL",
        "Decimal": "REAL", "Text": "TEXT",
        "DateTime": "TEXT", "Date": "TEXT", "Time": "TEXT",
        "Blob": "BLOB", "Enum": "TEXT", "Set": "TEXT",
        "Bit": "INTEGER", "Boolean": "INTEGER",
    }

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

    type_to_canonical: dict[str, str] = {
        "integer": "Integer32", "int": "Integer32",
        "real": "Real32",
        "text": "Text", "varchar": "Text", "char": "Text",
        "blob": "Blob",
    }

    function_to_canonical: dict[str, str] = {
        "CURRENT_TIMESTAMP": "CurrentTimestamp",
        "DATE('now')": "CurrentDate",
        "TIME('now')": "CurrentTime",
        "IFNULL": "Coalesce",
        "LENGTH": "Length",
        "GROUP_CONCAT": "GroupConcat",
        "lower(hex(randomblob(16)))": "Uuid",
    }

    def quote_identifier(self, name: str) -> str:
        return f'"{name}"'

    def format_drop_table(self, table: TableBlock) -> str:
        # SQLite 不支持 CASCADE
        return f"DROP TABLE IF EXISTS {self.quote_identifier(table.name)};"

    def format_create_table(self, table: TableBlock) -> str:
        lines: list[str] = []
        lines.append(f"CREATE TABLE {self.quote_identifier(table.name)} (")

        # 列定义
        col_lines: list[str] = []
        auto_pk_cols: set[str] = set()  # 已有 PRIMARY KEY 的列（如 AUTOINCREMENT 列）
        for col in table.columns:
            col_type = col.type_
            if "AUTOINCREMENT" in col_type.upper():
                # SQLite 要求 AUTOINCREMENT 必须与 PRIMARY KEY 搭配
                col_type = col_type.replace("AUTOINCREMENT", "PRIMARY KEY AUTOINCREMENT")
                auto_pk_cols.add(col.name)
            col_str = f"  {self.quote_identifier(col.name)} {col_type}"
            col_lines.append(col_str)

        # 主键（跳过已有 PRIMARY KEY 的 AUTOINCREMENT 列）
        if table.primary_key:
            pk_cols = [c for c in table.primary_key if c not in auto_pk_cols]
            if pk_cols:
                pk_str = ", ".join(self.quote_identifier(c) for c in pk_cols)
                col_lines.append(f"  PRIMARY KEY ({pk_str})")

        # 外键 — 内联到 CREATE TABLE 中（SQLite 不支持 ALTER TABLE ADD CONSTRAINT）
        for i, fk in enumerate(table.foreign_keys, start=1):
            cols = ", ".join(self.quote_identifier(c) for c in fk.columns)
            ref_cols = ", ".join(self.quote_identifier(c) for c in fk.ref_columns)
            fk_name = fk.name or f"fk_{table.name}_{i}"
            fk_line = (
                f"  CONSTRAINT {self.quote_identifier(fk_name)} "
                f"FOREIGN KEY ({cols}) REFERENCES {self.quote_identifier(fk.ref_table)} ({ref_cols})"
            )
            if fk.on_delete:
                fk_line += f" ON DELETE {fk.on_delete}"
            if fk.on_update:
                fk_line += f" ON UPDATE {fk.on_update}"
            col_lines.append(fk_line)

        # 索引 — 内联到 CREATE TABLE 中（非唯一索引仍用 CREATE INDEX）
        for idx in table.indexes:
            if idx.unique:
                cols = ", ".join(self.quote_identifier(c) for c in idx.columns)
                uniq = "UNIQUE " if idx.unique else ""
                col_lines.append(f"  {uniq}({cols})")

        lines.append(",\n".join(col_lines))
        lines.append(");")

        # SQLite 不支持 COMMENT ON
        return "\n".join(lines)

    def format_indexes(self, table: TableBlock) -> list[str]:
        """仅输出非唯一索引（唯一索引已在 CREATE TABLE 中内联）。"""
        extra_indexes = [idx for idx in table.indexes if not idx.unique]
        if not extra_indexes:
            return []

        stmts: list[str] = []
        for idx in extra_indexes:
            cols = ", ".join(self.quote_identifier(c) for c in idx.columns)
            stmt = f"CREATE INDEX {self.quote_identifier(idx.name)} ON {self.quote_identifier(table.name)} ({cols});"
            stmts.append(stmt)
        return stmts

    def format_foreign_keys(self, table: TableBlock) -> list[str]:
        """外键已在 CREATE TABLE 中内联，此处返回空。"""
        return []

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

    def write_output(self, sql_text: str, output_path) -> str:
        """将 SQL 文本写入 .db 文件（通过 sqlite3 执行），同时保留 .sql 参考文件。

        返回实际写入的 .db 文件路径。
        """
        import os
        import sqlite3

        db_path = output_path.with_suffix(".db")
        sql_path = output_path.with_suffix(".sql")

        # 写入 SQL 参考文件
        tmp_sql = sql_path.with_suffix(sql_path.suffix + ".tmp")
        tmp_sql.write_text(sql_text, encoding="utf-8")
        os.replace(tmp_sql, sql_path)

        # 创建 .db 文件
        tmp_db = db_path.with_suffix(db_path.suffix + ".tmp")
        if tmp_db.exists():
            tmp_db.unlink()
        conn = sqlite3.connect(str(tmp_db))
        try:
            conn.executescript(sql_text)
            conn.commit()
        except sqlite3.OperationalError as e:
            raise RuntimeError(
                f"SQLite 执行失败: {e}\n"
                f"SQL 参考文件已写入: {sql_path}\n"
                f"请打开该文件，搜索错误附近的语句定位问题。"
            ) from e
        finally:
            conn.close()
        os.replace(tmp_db, db_path)

        return str(db_path)
