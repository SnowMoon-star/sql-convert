"""MySQL 条件注释 (MYSQL_VERSION_COMMENT) 转换与提取单元测试。"""
import tempfile
import unittest
from pathlib import Path

from main import convert
from reader.sql_reader import SQLReader
from utils.report import ConversionReport


class TestConditionalComment(unittest.TestCase):
    """测试条件注释在 SQLReader 中提取、以及在不同目标库下的转换行为。"""

    def test_sql_reader_extracts_conditional_comments(self):
        """测试 SQLReader 正确识别并切分出 MYSQL_VERSION_COMMENT。"""
        sql_content = (
            "/*!40101 SET NAMES utf8mb4 */;\n"
            "SELECT 1;"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write(sql_content)
            tmp_path = Path(f.name)

        try:
            reader = SQLReader(tmp_path)
            stmts = list(reader.iter_statements())
            self.assertEqual(len(stmts), 2)
            self.assertEqual(stmts[0].text, "/*!40101 SET NAMES utf8mb4 */;")
            self.assertEqual(stmts[1].text, "SELECT 1;")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_convert_non_mysql_target_extracts_body(self):
        """测试目标库为非 MySQL（如 pgsql）时，条件注释提取内部真实 SQL 主体。"""
        # 测试在 DDL 中，如果包含条件注释（例如 `ENGINE=InnoDB` 的条件注释被剥离），或者独立 DML 被剥离
        # 我们用一个最简的 DML 来测试，它流经 Pipeline 会变成干净的 SQL 并输出
        input_sql = "/*!40101 SET NAMES utf8mb4 */;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write(input_sql)
            tmp_path = Path(f.name)
        
        output_path = tmp_path.with_name(tmp_path.stem + "_converted.sql")
        
        try:
            # 目标是 PG
            convert(tmp_path, output_path, "mysql", "pgsql", encoding="utf-8")
            self.assertTrue(output_path.exists())
            
            content = output_path.read_text(encoding="utf-8")
            # 非 MySQL 目标，外层的 /*!40101 ... */ 应该被提取出主体
            # 因为 "SET @OLD_SQL_MODE=..." 会正常作为语句传递并被转换（虽然会因为无匹配规则而直接保留），但肯定不含外层注释壳
            self.assertNotIn("/*!40101", content)
            self.assertIn("client_encoding", content)
            
        finally:
            tmp_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def test_convert_mysql_target_keeps_comment(self):
        """测试目标库为 MySQL 时，条件注释应原样保留。"""
        # 刚才我们在 MySQL 转换为 Oracle 看到它在 DDL 里被正常识别。
        # 如果 target 是 MySQL，它应该原样保留条件注释
        input_sql = "/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE */;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write(input_sql)
            tmp_path = Path(f.name)
        
        output_path = tmp_path.with_name(tmp_path.stem + "_converted.sql")
        
        try:
            # 目标是 MySQL
            convert(tmp_path, output_path, "mysql", "mysql", encoding="utf-8")
            self.assertTrue(output_path.exists())
            
            content = output_path.read_text(encoding="utf-8")
            # 目标为 MySQL，外层的 /*!40101 和 */ 应被原样输出保留
            self.assertIn("/*!40101", content)
            self.assertIn("*/", content)
            
        finally:
            tmp_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
