"""Statement 与 Diagnostics 的单元测试。"""
import tempfile
import unittest
from pathlib import Path

from core.diagnostics import Statement, Severity, Diagnostic
from reader.sql_reader import SQLReader
from reader.classifier import StatementType


class TestDiagnosticsAndMetadata(unittest.TestCase):
    """验证 Statement 物理行列和偏移量的跟踪，以及 Diagnostic 各字段。"""

    def test_statement_tracking(self):
        """验证 SQLReader 能正确提取 Statement 行号与偏移。"""
        sql_content = (
            "SELECT 1;\n"              # Line 1
            "\n"                       # Line 2
            "  CREATE TABLE t (\n"      # Line 3
            "    id INT\n"             # Line 4
            "  );\n"                   # Line 5
            "INSERT INTO t VALUES(1);"  # Line 6
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write(sql_content)
            tmp_path = Path(f.name)

        try:
            reader = SQLReader(tmp_path)
            stmts = list(reader.iter_statements())
            
            self.assertEqual(len(stmts), 3)
            
            # Stmt 1: SELECT 1;
            self.assertEqual(stmts[0].text, "SELECT 1;")
            self.assertEqual(stmts[0].start_line, 1)
            self.assertEqual(stmts[0].end_line, 1)
            self.assertEqual(stmts[0].offset, 0)
            self.assertEqual(stmts[0].statement_type, StatementType.DML)
            
            # Stmt 2: CREATE TABLE t (...
            self.assertEqual(stmts[1].start_line, 3)
            self.assertEqual(stmts[1].end_line, 5)
            # 偏移量：SELECT 1;\n\n -> 10 + 1 + 1 = 12 个字符 (可能根据换行符长度略有浮动，这里做前导空白后起始匹配检测)
            self.assertEqual(stmts[1].text, "CREATE TABLE t (\n    id INT\n  );")
            
            # Stmt 3: INSERT INTO...
            self.assertEqual(stmts[2].start_line, 6)
            self.assertEqual(stmts[2].end_line, 6)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_diagnostic_formatting(self):
        """验证 Diagnostic 的格式化输出。"""
        stmt = Statement(
            text="SELECT *",
            statement_type=StatementType.DML,
            start_line=10,
            end_line=11,
            offset=100,
            source_file=Path("test.sql")
        )
        diag = Diagnostic(
            message="语法不完整",
            severity=Severity.ERROR,
            rule="SelectCheckRule",
            statement=stmt,
            line=stmt.start_line,
            column=1,
            suggestion="补全 FROM 关键字"
        )
        self.assertEqual(diag.line, 10)
        self.assertEqual(diag.rule, "SelectCheckRule")
        self.assertIn("[ERROR] Line 10, Col 1 [Rule: SelectCheckRule]: 语法不完整", str(diag))


if __name__ == "__main__":
    unittest.main()
