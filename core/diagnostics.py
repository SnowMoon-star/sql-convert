"""SQL 转换器诊断信息与 Statement 元数据模型。"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reader.classifier import StatementType


@dataclass
class Statement:
    """SQL 语句元数据实体，记录其在源文件中的行列和偏移位置。"""
    text: str
    statement_type: StatementType
    start_line: int
    end_line: int
    offset: int
    source_file: Path

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.text == other
        if isinstance(other, Statement):
            return (
                self.text == other.text
                and self.start_line == other.start_line
                and self.source_file == other.source_file
            )
        return False

    def __str__(self) -> str:
        return self.text

    def __hash__(self) -> int:
        return hash((self.text, self.start_line, self.source_file))


class Severity(Enum):
    """诊断严重程度级别。"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass
class Diagnostic:
    """一条具体的编译/转换诊断信息。"""
    message: str
    severity: Severity
    rule: str | None = None
    statement: Statement | None = None
    line: int | None = None
    column: int | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        loc = f"Line {self.line}" if self.line is not None else "Unknown Line"
        if self.column is not None:
            loc += f", Col {self.column}"
        rule_str = f" [Rule: {self.rule}]" if self.rule else ""
        return f"[{self.severity.value}] {loc}{rule_str}: {self.message}"
