"""流式读取、分类与 INSERT 解析引擎的单元测试。"""
import tempfile
import unittest
from pathlib import Path

from reader.sql_reader import SQLReader
from reader.classifier import classify_statement, StatementType
from parser.insert_stream import iter_insert_rows, InsertRow
from convert import convert


class TestSQLReader(unittest.TestCase):
    """测试 SQLReader 对 SQL 语句的流式切分功能。"""

    def test_basic_statements(self):
        """测试基本语句切分。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("SELECT 1;\nSELECT 2;\nSELECT 3;")
            tmp_path = Path(f.name)
        try:
            reader = SQLReader(tmp_path)
            stmts = list(reader.iter_statements())
            self.assertEqual(len(stmts), 3)
            self.assertEqual(stmts[0], "SELECT 1;")
            self.assertEqual(stmts[1], "SELECT 2;")
            self.assertEqual(stmts[2], "SELECT 3;")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_custom_delimiter(self):
        """测试 MySQL DELIMITER 关键字声明与自定义边界切分。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("SELECT 1;\n")
            f.write("DELIMITER //\n")
            f.write("CREATE PROCEDURE p() BEGIN SELECT 2; END//\n")
            f.write("DELIMITER ;\n")
            f.write("SELECT 3;\n")
            tmp_path = Path(f.name)
        try:
            reader = SQLReader(tmp_path)
            stmts = list(reader.iter_statements())
            self.assertEqual(len(stmts), 3)
            self.assertEqual(stmts[0], "SELECT 1;")
            self.assertEqual(stmts[1], "CREATE PROCEDURE p() BEGIN SELECT 2; END//")
            self.assertEqual(stmts[2], "SELECT 3;")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_comments_and_quotes(self):
        """测试注释和各种引号包裹，确保忽略引号或注释内部的分号。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("SELECT 'a;b'; -- comment with ;\n")
            f.write("SELECT /* comment; */ \"c;d\";\n")
            f.write("SELECT `e;f`;\n")
            tmp_path = Path(f.name)
        try:
            reader = SQLReader(tmp_path)
            stmts = list(reader.iter_statements())
            self.assertEqual(len(stmts), 3)
            self.assertEqual(stmts[0], "SELECT 'a;b';")
            self.assertEqual(stmts[1], 'SELECT  "c;d";')
            self.assertEqual(stmts[2], "SELECT `e;f`;")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_postgres_dollar_quote(self):
        """测试 PostgreSQL Dollar Quote ($tag$...$tag$) 切分。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("CREATE FUNCTION f() RETURNS void AS $body$\n")
            f.write("BEGIN\n  SELECT 1;\nEND;\n")
            f.write("$body$ LANGUAGE plpgsql;\n")
            f.write("SELECT 2;\n")
            tmp_path = Path(f.name)
        try:
            reader = SQLReader(tmp_path)
            stmts = list(reader.iter_statements())
            self.assertEqual(len(stmts), 2)
            self.assertTrue(stmts[0].startswith("CREATE FUNCTION"))
            self.assertEqual(stmts[1], "SELECT 2;")
        finally:
            tmp_path.unlink(missing_ok=True)


class TestClassifier(unittest.TestCase):
    """测试 Statement Classifier 分类器。"""

    def test_classification(self):
        self.assertEqual(classify_statement("CREATE TABLE t (id INT);"), StatementType.DDL)
        self.assertEqual(classify_statement("DROP TABLE IF EXISTS t;"), StatementType.DDL)
        self.assertEqual(classify_statement("ALTER TABLE t ADD COLUMN name TEXT;"), StatementType.DDL)
        
        self.assertEqual(classify_statement("INSERT INTO t VALUES (1);"), StatementType.DML)
        self.assertEqual(classify_statement("UPDATE t SET x = 1;"), StatementType.DML)
        self.assertEqual(classify_statement("SELECT * FROM t;"), StatementType.DML)

        self.assertEqual(classify_statement("COMMENT ON TABLE t IS 'test';"), StatementType.COMMENT)
        self.assertEqual(classify_statement("COMMENT ON COLUMN t.c IS 'test';"), StatementType.COMMENT)

        self.assertEqual(classify_statement("CREATE INDEX idx_t ON t (c);"), StatementType.INDEX)
        self.assertEqual(classify_statement("DROP INDEX idx_t;"), StatementType.INDEX)

        # 带有前置注释的语句分类
        self.assertEqual(
            classify_statement("-- comment line\n/* block comment */\nINSERT INTO t VALUES (1);"),
            StatementType.DML
        )


class TestInsertStream(unittest.TestCase):
    """测试 INSERT 流式解析引擎。"""

    def test_iter_insert_rows(self):
        """测试正常 INSERT 提取 VALUES。"""
        sql = "INSERT INTO t (id, name) VALUES (1, 'alice'), (2, 'bob'), (3, NULL);"
        rows = list(iter_insert_rows(sql))
        self.assertEqual(len(rows), 3)

        self.assertIsInstance(rows[0], InsertRow)
        self.assertEqual(rows[0][0], "1")
        self.assertEqual(rows[0][1], "'alice'")

        self.assertEqual(rows[1][0], "2")
        self.assertEqual(rows[1][1], "'bob'")

        self.assertEqual(rows[2][0], "3")
        self.assertEqual(rows[2][1], "NULL")

    def test_escaped_quotes_in_insert(self):
        """测试包含转义引号和特殊控制字符的值解析。"""
        sql = "INSERT INTO t VALUES (1, 'it\\'s a test'), (2, 'line1\\r\\nline2');"
        rows = list(iter_insert_rows(sql))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], "'it\\'s a test'")
        self.assertEqual(rows[1][1], "'line1\\r\\nline2'")


if __name__ == "__main__":
    unittest.main()
