"""E2E 端到端集成测试基类 — 负责转换执行、Golden File 对比以及 Docker 校验兜底。"""
from __future__ import annotations
import os
import re
import unittest
from pathlib import Path
import yaml

from main import convert
from utils.report import ConversionReport


class E2ETestBase(unittest.TestCase):
    """E2E 测试基类，提供 Golden File Diff 核心校验方法。"""

    def run_golden_test(self, case_dir: Path) -> None:
        """执行指定用例目录下的 Golden File 测试。"""
        input_sql_path = case_dir / "input.sql"
        expected_sql_path = case_dir / "expected.sql"
        config_yaml_path = case_dir / "config.yaml"

        self.assertTrue(input_sql_path.exists(), f"未找到输入文件: {input_sql_path}")
        self.assertTrue(expected_sql_path.exists(), f"未找到预期文件: {expected_sql_path}")
        self.assertTrue(config_yaml_path.exists(), f"未找到配置文件: {config_yaml_path}")

        # 1. 加载配置
        with open(config_yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        source_mode = config.get("source_mode")
        target_mode = config.get("target_mode")
        ignore_comments = config.get("ignore_comments", True)

        # 2. 转换输出
        output_sql_path = case_dir / "output.sql"
        report = ConversionReport()
        
        try:
            convert(
                input_path=input_sql_path,
                output_path=output_sql_path,
                source_mode=source_mode,
                target_mode=target_mode,
                encoding="utf-8",
                report=report,
                continue_on_error=True
            )
            
            # 3. 读取内容并比对
            self.assertTrue(output_sql_path.exists(), "转换未生成目标 SQL 文件")
            
            actual_content = output_sql_path.read_text(encoding="utf-8")
            expected_content = expected_sql_path.read_text(encoding="utf-8")
            
            # 4. 应用 Diff 忽略规则
            actual_cleaned = self._clean_sql(actual_content, ignore_comments)
            expected_cleaned = self._clean_sql(expected_content, ignore_comments)
            
            self.assertEqual(
                actual_cleaned, 
                expected_cleaned, 
                f"SQL 转换结果与 Golden File (expected.sql) 不匹配！\n用例: {case_dir.name}"
            )
            
        finally:
            # 清理生成的临时输出 SQL 文件
            output_sql_path.unlink(missing_ok=True)
            # 清理生成的报告 HTML 文件
            for report_file in case_dir.glob("*_report.html"):
                report_file.unlink(missing_ok=True)

    def _clean_sql(self, sql: str, ignore_comments: bool) -> str:
        """根据配置，对 SQL 文本进行清洗以便于比对。"""
        # 1. 忽略 Line Endings (统一为 \n)
        sql = sql.replace("\r\n", "\n")

        # 2. 忽略 Comments (若配置)
        if ignore_comments:
            # 剔除行注释 -- 和 #
            sql = re.sub(r"--[^\n]*", "", sql)
            sql = re.sub(r"#[^\n]*", "", sql)
            # 剔除块注释 /* */
            sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

        # 3. 忽略 Whitespace (折叠连续空白为单个空格，并去除首尾空白)
        sql = re.sub(r"\s+", " ", sql)
        return sql.strip()
