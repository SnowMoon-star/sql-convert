"""E2E 各方言转换黄金对比测试。"""
from __future__ import annotations
import unittest
from pathlib import Path
from .test_e2e_base import E2ETestBase


class TestE2ECases(E2ETestBase):
    """测试五组核心方言对之间的转换。"""

    def test_oracle_to_pgsql(self):
        self.run_golden_test(Path(__file__).parent / "oracle_to_pgsql")

    def test_oracle_to_mysql(self):
        self.run_golden_test(Path(__file__).parent / "oracle_to_mysql")

    def test_mysql_to_pgsql(self):
        self.run_golden_test(Path(__file__).parent / "mysql_to_pgsql")

    def test_mysql_to_oracle(self):
        self.run_golden_test(Path(__file__).parent / "mysql_to_oracle")

    def test_sqlserver_to_pgsql(self):
        self.run_golden_test(Path(__file__).parent / "sqlserver_to_pgsql")


if __name__ == "__main__":
    unittest.main()
