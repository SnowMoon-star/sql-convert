"""兼容性特性检查矩阵 (Feature Matrix) — 检测不支持或部分支持的高级 SQL 语法。"""
from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass
class FeatureMatrixEntry:
    feature_name: str
    pattern: re.Pattern
    status: str       # "SUPPORTED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED"
    warning_template: str


# 兼容性特征库
FEATURE_PATTERNS = [
    FeatureMatrixEntry(
        feature_name="Partition Table",
        pattern=re.compile(r"\bPARTITION\s+BY\b", re.IGNORECASE),
        status="UNSUPPORTED",
        warning_template="检测到分区表语法 'PARTITION BY'，当前目标库不支持自动分区转换，将忽略分区声明。"
    ),
    FeatureMatrixEntry(
        feature_name="Function Index",
        pattern=re.compile(r"\bINDEX\s+\w+\s*(?:ON\s+\w+\s*)?\(\s*\w+\([^)]+\)\s*\)", re.IGNORECASE),
        status="PARTIALLY_SUPPORTED",
        warning_template="检测到函数索引/表达式索引，请人工确认目标数据库是否兼容该索引函数表达式。"
    ),
    FeatureMatrixEntry(
        feature_name="Trigger",
        pattern=re.compile(r"\bCREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\b", re.IGNORECASE),
        status="UNSUPPORTED",
        warning_template="检测到触发器声明 'CREATE TRIGGER'，工具目前无法自动迁移触发器，请手动导出并转换迁移。"
    ),
    FeatureMatrixEntry(
        feature_name="Sequence",
        pattern=re.compile(r"\bCREATE\s+SEQUENCE\b", re.IGNORECASE),
        status="PARTIALLY_SUPPORTED",
        warning_template="检测到序列声明 'CREATE SEQUENCE'，转换时将按目标库方言适配自增列或保留定义。"
    ),
    FeatureMatrixEntry(
        feature_name="Materialized View",
        pattern=re.compile(r"\bCREATE\s+MATERIALIZED\s+VIEW\b", re.IGNORECASE),
        status="UNSUPPORTED",
        warning_template="检测到物化视图 'CREATE MATERIALIZED VIEW'，工具目前不支持物化视图语法转换，转换后将忽略。"
    ),
    FeatureMatrixEntry(
        feature_name="MySQL Conditional Comment",
        pattern=re.compile(r"/\*!\d*.*?\*/", re.DOTALL),
        status="PARTIALLY_SUPPORTED",
        warning_template="检测到 MySQL 条件注释 '/*! ... */'。转换器将根据目标库方言选择保留格式或提取内部主体转换。"
    )
]


def check_compatibility(sql: str, report) -> None:
    """在转换流程中，对输入的单条语句进行高级特性的兼容性检索并报告。"""
    for entry in FEATURE_PATTERNS:
        m = entry.pattern.search(sql)
        if m:
            if entry.status != "SUPPORTED":
                matched_snippet = m.group(0)
                report.add_warning(f"[{entry.status}] {entry.warning_template} (检测特征: {matched_snippet})")
