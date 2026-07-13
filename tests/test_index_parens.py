"""测试 DDL 解析器中对索引字段包含 ASC/DESC 或嵌套前缀长度小括号的正确处理。"""
import unittest
from utils.sql_parser.ddl_parser import parse_tables


class TestIndexColumnParsing(unittest.TestCase):
    """验证包含 ASC/DESC 和嵌套长度限制如 (10) 的索引字段能够被剥离出真实列名。"""

    def test_index_columns_stripping(self):
        sql = (
            "CREATE TABLE t (\n"
            "  id INT PRIMARY KEY,\n"
            "  username VARCHAR(64) NOT NULL,\n"
            "  email VARCHAR(128),\n"
            "  KEY idx_user_desc (username(20) DESC),\n"
            "  KEY idx_user_asc (username ASC),\n"
            "  KEY idx_multi (username(10) ASC, email DESC)\n"
            ");"
        )
        tables = parse_tables(sql)
        self.assertEqual(len(tables), 1)
        table = tables[0]

        self.assertEqual(len(table.indexes), 3)

        # 1. idx_user_desc
        idx1 = table.indexes[0]
        self.assertEqual(idx1.name, "idx_user_desc")
        self.assertEqual(idx1.columns, ["username"])

        # 2. idx_user_asc
        idx2 = table.indexes[1]
        self.assertEqual(idx2.name, "idx_user_asc")
        self.assertEqual(idx2.columns, ["username"])

        # 3. idx_multi
        idx3 = table.indexes[2]
        self.assertEqual(idx3.name, "idx_multi")
        self.assertEqual(idx3.columns, ["username", "email"])


if __name__ == "__main__":
    unittest.main()
