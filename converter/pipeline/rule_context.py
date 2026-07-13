"""规则执行上下文 — 封装转换过程中的状态。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from converter.dialects.base import BaseDialect
from reader.classifier import StatementType

@dataclass
class RuleContext:
    """转换规则运行时的上下文参数。"""
    source_dialect: BaseDialect
    target_dialect: BaseDialect
    statement_type: StatementType
    schema: Any = None
    options: dict[str, Any] = field(default_factory=dict)
