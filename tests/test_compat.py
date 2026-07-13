"""兼容性 Feature Matrix 的单元测试。"""
import unittest
from utils.report import ConversionReport
from utils.compat import check_compatibility


class TestCompatibilityChecker(unittest.TestCase):
    """测试 check_compatibility 对各种不支持语法的警告捕获。"""

    def test_partition_table_detection(self):
        """测试对分区表语法的捕获。"""
        report = ConversionReport()
        sql = "CREATE TABLE orders (id INT, order_date DATE) PARTITION BY RANGE (YEAR(order_date));"
        check_compatibility(sql, report)
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("PARTITION BY", report.warnings[0])
        self.assertIn("UNSUPPORTED", report.warnings[0])

    def test_trigger_detection(self):
        """测试对触发器声明的捕获。"""
        report = ConversionReport()
        sql = "CREATE TRIGGER audit_log AFTER INSERT ON users FOR EACH ROW BEGIN INSERT INTO logs ... END;"
        check_compatibility(sql, report)
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("CREATE TRIGGER", report.warnings[0])
        self.assertIn("UNSUPPORTED", report.warnings[0])

    def test_sequence_detection(self):
        """测试对序列声明的捕获。"""
        report = ConversionReport()
        sql = "CREATE SEQUENCE user_id_seq START WITH 1 INCREMENT BY 1;"
        check_compatibility(sql, report)
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("CREATE SEQUENCE", report.warnings[0])
        self.assertIn("PARTIALLY_SUPPORTED", report.warnings[0])

    def test_materialized_view_detection(self):
        """测试对物化视图声明的捕获。"""
        report = ConversionReport()
        sql = "CREATE MATERIALIZED VIEW mv_sales AS SELECT product, SUM(amount) FROM sales GROUP BY product;"
        check_compatibility(sql, report)
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("CREATE MATERIALIZED VIEW", report.warnings[0])
        self.assertIn("UNSUPPORTED", report.warnings[0])

    def test_function_index_detection(self):
        """测试对函数索引/表达式索引的捕获。"""
        report = ConversionReport()
        sql = "CREATE INDEX idx_lower_name ON users (lower(username));"
        check_compatibility(sql, report)
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("lower(username)", report.warnings[0])
        self.assertIn("PARTIALLY_SUPPORTED", report.warnings[0])


if __name__ == "__main__":
    unittest.main()
