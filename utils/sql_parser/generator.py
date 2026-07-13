"""AST (Abstract Syntax Tree) SQL 生成器 — 负责将表定义 AST 重新渲染为标准的 SQL 文本。"""
from __future__ import annotations
from model import TableBlock, ColumnDef, IndexDef, ForeignKeyDef


class SQLGenerator:
    """通用的 SQL 渲染生成器。"""

    @staticmethod
    def generate_drop_table(table: TableBlock, quote_char: str = '"', cascade: bool = True) -> str:
        """渲染 DROP TABLE 语句。"""
        q = quote_char
        cascade_clause = " CASCADE" if cascade else ""
        return f"DROP TABLE IF EXISTS {q}{table.name}{q}{cascade_clause};"

    @staticmethod
    def generate_create_table(
        table: TableBlock, 
        quote_char: str = '"', 
        type_mapping: dict[str, str] | None = None
    ) -> str:
        """从 TableBlock 结构渲染 DDL 建表 SQL。"""
        q = quote_char
        lines = []
        lines.append(f"CREATE TABLE {q}{table.name}{q} (")
        
        col_lines = []
        for col in table.columns:
            # 基础类型映射替换
            col_type = col.type_
            if type_mapping:
                for src_t, tgt_t in type_mapping.items():
                    # 强行正则替换类型
                    col_type = re.sub(rf"\b{src_t}\b", tgt_t, col_type, flags=re.IGNORECASE)

            # COMMENT 在非 MySQL 的建表内通常不写，而是通过外部 COMMENT ON，这里根据 dialect 特点在子类控制
            col_lines.append(f"  {q}{col.name}{q} {col_type}")

        if table.primary_key:
            pk_cols = ", ".join(f"{q}{c}{q}" for c in table.primary_key)
            col_lines.append(f"  PRIMARY KEY ({pk_cols})")

        lines.append(",\n".join(col_lines))
        lines.append(");")
        return "\n".join(lines)
