"""方言基础类。"""
from __future__ import annotations
from model import TableBlock


class BaseDialect:
    """SQL 方言抽象策略基类。"""

    family: str = ""              # 家族: mysql, pg, oracle, sqlite
    identifier_quote: str = '"'   # 标识符包围符
    capabilities: set[str] = set()  # 该方言支持的能力标签

    # 类型映射表（子类覆盖）
    type_to_canonical: dict[str, str] = {}
    canonical_to_type: dict[str, str] = {}

    # 函数映射表（子类覆盖）
    function_to_canonical: dict[str, str] = {}
    canonical_to_function: dict[str, str] = {}

    def __init__(self, database: str | None = None):
        self.database = database

    def quote_identifier(self, name: str) -> str:
        """包围标识符（表名、列名等）。"""
        raise NotImplementedError

    def format_table_label(self, table: TableBlock) -> str:
        """生成带/不带数据库前缀的表标识符（用于注释）。"""
        if table.database:
            return f"{self.quote_identifier(table.database)}.{self.quote_identifier(table.name)}"
        return self.quote_identifier(table.name)

    def escape_comment(self, text: str) -> str:
        """转义注释文本中的特殊字符（单引号、各类换行符）。"""
        text = text.replace("'", "\\'")
        text = text.replace("\r\n", " ")
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        text = text.replace("\\r\\n", " ")
        text = text.replace("\\n", " ")
        text = text.replace("\\r", " ")
        return text

    def format_drop_table(self, table: TableBlock) -> str:
        """格式化删除旧表语句 (步骤1)。"""
        raise NotImplementedError

    def format_create_table(self, table: TableBlock) -> str:
        """格式化创建表语句 (步骤2，返回包含建表及（若有）独立注释语句的字符串)。"""
        raise NotImplementedError

    def format_indexes(self, table: TableBlock) -> list[str]:
        """格式化添加索引语句列表 (步骤3)。"""
        raise NotImplementedError

    def format_foreign_keys(self, table: TableBlock) -> list[str]:
        """格式化外键约束语句列表 (步骤4)。"""
        raise NotImplementedError

    def format_inserts(self, table: TableBlock) -> list[str]:
        """格式化数据导入语句列表 (步骤5)。"""
        raise NotImplementedError

    def write_output(self, sql_text: str, output_path) -> str:
        """将 SQL 文本写入文件。子类可覆盖以实现不同输出格式（如 SQLite 的 .db）。"""
        import os
        tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        tmp_path.write_text(sql_text, encoding="utf-8")
        os.replace(tmp_path, output_path)
        return str(output_path)
