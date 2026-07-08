"""嗅探源方言功能的单元测试。"""
import tempfile
import unittest
from pathlib import Path

from convert import sniff_source_dialect, parse_args
from converter.registry import get_dialect
from converter.dialects.pgsql import PgsqlDialect


class TestSniffSourceDialect(unittest.TestCase):
    """测试 sniff_source_dialect 函数的准确性。"""

    def test_mysql_features(self):
        """MySQL 特征文件应被识别为 mysql。"""
        result, _ = sniff_source_dialect(Path("tests/sample_input.sql"))
        self.assertEqual(result, "mysql")

    def test_oracle_features(self):
        """Oracle 特征文件应被识别为 oracle。"""
        result, _ = sniff_source_dialect(Path("tests/sniff_oracle_input.sql"))
        self.assertEqual(result, "oracle")

    def test_mysql_edge_cases(self):
        """MySQL 边界场景文件应被识别为 mysql。"""
        result, _ = sniff_source_dialect(Path("tests/edge_cases_input.sql"))
        self.assertEqual(result, "mysql")

    def test_empty_file_defaults_to_mysql(self):
        """空文件（无任何特征）应降级为 mysql。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("")
            tmp_path = Path(f.name)
        try:
            result, _ = sniff_source_dialect(tmp_path)
            self.assertEqual(result, "mysql")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_no_feature_file_defaults_to_mysql(self):
        """无方言特征的 SQL 文件应降级为 mysql。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("SELECT * FROM users;\n")
            f.write("CREATE TABLE orders (id INTEGER);\n")
            tmp_path = Path(f.name)
        try:
            result, _ = sniff_source_dialect(tmp_path)
            self.assertEqual(result, "mysql")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_kingbase_features(self):
        """Kingbase 特征文件应被识别为 kingbase。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("CREATE TABLE t1 (id INT) WITHOUT OIDS;\n")
            f.write("CREATE TABLE t2 (id INT) WITHOUT SYSTEM OIDS;\n")
            tmp_path = Path(f.name)
        try:
            result, _ = sniff_source_dialect(tmp_path)
            self.assertEqual(result, "kingbase")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_pgsql_features(self):
        """PostgreSQL 特征文件应被识别为 pgsql。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("CREATE TABLE t1 (id SERIAL PRIMARY KEY);\n")
            f.write("SELECT * FROM t1 WHERE name ILIKE '%test%';\n")
            f.write("INSERT INTO t2 (name) VALUES ('a') RETURNING id;\n")
            f.write("SELECT '123'::integer;\n")
            f.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
            tmp_path = Path(f.name)
        try:
            result, _ = sniff_source_dialect(tmp_path)
            self.assertEqual(result, "pgsql")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_pgsql_serial_and_cast(self):
        """SERIAL 类型和 :: 转换是 PostgreSQL 强特征。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("CREATE TABLE t (id BIGSERIAL, val TEXT);\n")
            f.write("SELECT id::text FROM t;\n")
            tmp_path = Path(f.name)
        try:
            result, _ = sniff_source_dialect(tmp_path)
            self.assertEqual(result, "pgsql")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_mysql_scores_higher_when_mixed_with_oracle(self):
        """MySQL 特征多于 Oracle 特征时，应识别为 mysql。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("CREATE TABLE `test` (\n")
            f.write("  `id` INT NOT NULL AUTO_INCREMENT,\n")
            f.write("  `name` VARCHAR(64)\n")
            f.write(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n")
            f.write("CREATE TABLE t2 (x NUMBER);\n")
            tmp_path = Path(f.name)
        try:
            result, _ = sniff_source_dialect(tmp_path)
            self.assertEqual(result, "mysql")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_oracle_scores_higher_when_dominant(self):
        """Oracle 特征明显多于 MySQL 时，应识别为 oracle。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            for i in range(10):
                f.write(f"CREATE TABLE t{i} (col{i} VARCHAR2(100), n{i} NUMBER);\n")
            f.write("SELECT SYSDATE FROM DUAL;\n")
            f.write("SELECT * FROM t WHERE ROWNUM < 10;\n")
            f.write("CREATE TABLE t_extra (`col` INT);\n")
            tmp_path = Path(f.name)
        try:
            result, _ = sniff_source_dialect(tmp_path)
            self.assertEqual(result, "oracle")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_nonexistent_file_returns_default(self):
        """不存在的文件应降级为 mysql（不抛异常）。"""
        result, _ = sniff_source_dialect(Path("tests/does_not_exist.sql"))
        self.assertEqual(result, "mysql")

    def test_limit_lines_respected(self):
        """仅读取前 N 行进行嗅探（默认 1000 行）。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            for _ in range(5):
                f.write("-- comment\n")
            f.write("CREATE TABLE t (x VARCHAR2(100));\n")
            tmp_path = Path(f.name)
        try:
            result_limited, _ = sniff_source_dialect(tmp_path, limit_lines=5)
            self.assertEqual(result_limited, "mysql")
            result_default, _ = sniff_source_dialect(tmp_path)
            self.assertEqual(result_default, "oracle")
        finally:
            tmp_path.unlink(missing_ok=True)


class TestPgsqlDialect(unittest.TestCase):
    """测试 PostgreSQL 方言策略类。"""

    def test_factory_pgsql(self):
        """get_dialect('pgsql') 返回 PgsqlDialect 实例。"""
        d = get_dialect("pgsql")
        self.assertIsInstance(d, PgsqlDialect)

    def test_factory_postgresql(self):
        """get_dialect('postgresql') 返回 PgsqlDialect 实例。"""
        d = get_dialect("postgresql")
        self.assertIsInstance(d, PgsqlDialect)

    def test_factory_postgres(self):
        """get_dialect('postgres') 返回 PgsqlDialect 实例。"""
        d = get_dialect("postgres")
        self.assertIsInstance(d, PgsqlDialect)

    def test_quote_identifier(self):
        """PostgreSQL 使用双引号包围标识符。"""
        d = PgsqlDialect()
        self.assertEqual(d.quote_identifier("test"), '"test"')

    def test_drop_table(self):
        """PostgreSQL DROP TABLE 使用 CASCADE。"""
        from sql_parser import TableBlock
        tb = TableBlock(database=None, name="users", comment=None)
        d = PgsqlDialect()
        self.assertEqual(d.format_drop_table(tb), 'DROP TABLE IF EXISTS "users" CASCADE;')


class TestSniffIntegration(unittest.TestCase):
    """测试命令行参数解析与嗅探的集成。"""

    def test_source_mode_auto_when_not_specified(self):
        """未指定 --source-mode 时，args.source_mode 为 None。"""
        args = parse_args(["input.sql"])
        self.assertIsNone(args.source_mode)

    def test_source_mode_explicit_when_specified(self):
        """明确指定 --source-mode 时，args.source_mode 为指定值。"""
        args = parse_args(["input.sql", "--source-mode", "oracle"])
        self.assertEqual(args.source_mode, "oracle")

    def test_source_mode_default(self):
        """默认 source-mode 为 None（必填，无默认值）。"""
        args = parse_args(["input.sql"])
        self.assertIsNone(args.source_mode)

    def test_target_mode_default(self):
        """默认 target-mode 为 None（必填，无默认值）。"""
        args = parse_args(["input.sql"])
        self.assertIsNone(args.target_mode)


if __name__ == "__main__":
    unittest.main()