"""ConversionReport 的单元测试。"""
import tempfile
import unittest
from pathlib import Path
from utils.report import ConversionReport


class TestConversionReport(unittest.TestCase):
    """测试 ConversionReport 各项指标更新及 HTML 报告生成。"""

    def test_metrics_collection(self):
        """测试指标收集和计算。"""
        report = ConversionReport()
        report.start()
        
        report.increment_table()
        report.increment_index(2)
        report.increment_constraint(3)
        
        report.update_rule_hits({"rule_a": 5, "rule_b": 2})
        report.add_warning("[UNSUPPORTED] Test warning")
        report.record_failure("SELECT 1", Exception("Syntax error"))
        
        report.stop()
        
        self.assertEqual(report.table_count, 1)
        self.assertEqual(report.index_count, 2)
        self.assertEqual(report.constraint_count, 3)
        self.assertEqual(report.rule_hits["rule_a"], 5)
        self.assertEqual(report.rule_hits["rule_b"], 2)
        self.assertEqual(len(report.warnings), 1)
        self.assertEqual(len(report.failed_statements), 1)
        self.assertGreater(report.duration, 0)

    def test_report_generation_all_formats(self):
        """测试 HTML, JSON 和 Markdown 格式报告生成与写入。"""
        report = ConversionReport()
        report.increment_table()
        report.update_rule_hits({"convert_type": 1})
        report.add_warning("Test warning message")
        
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
            tmp_output_path = Path(f.name)
        
        report_path = None
        json_path = None
        md_path = None
        try:
            report_path = report.write_report(tmp_output_path, "mysql", "pgsql")
            json_path = tmp_output_path.with_name(f"{tmp_output_path.stem}_{report_path.name.split('_')[-2]}_report.json")
            md_path = tmp_output_path.with_name(f"{tmp_output_path.stem}_{report_path.name.split('_')[-2]}_report.md")

            self.assertTrue(report_path.exists())
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            
            # HTML 验证
            html_content = report_path.read_text(encoding="utf-8")
            self.assertIn("SQL 转换评估报告", html_content)
            
            # JSON 验证
            json_content = json_path.read_text(encoding="utf-8")
            self.assertIn('"table_count": 1', json_content)
            
            # MD 验证
            md_content = md_path.read_text(encoding="utf-8")
            self.assertIn("# SQL 转换评估报告", md_content)
            self.assertIn("Test warning message", md_content)

        finally:
            tmp_output_path.unlink(missing_ok=True)
            if report_path and report_path.exists():
                report_path.unlink(missing_ok=True)
            if json_path and json_path.exists():
                json_path.unlink(missing_ok=True)
            if md_path and md_path.exists():
                md_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
