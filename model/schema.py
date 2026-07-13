"""Schema 整体数据库模型，包含所有表结构。"""
from __future__ import annotations
from dataclasses import dataclass, field
from model.table import TableBlock

@dataclass
class Schema:
    """包含了多个表 Block 的数据库 Schema 整体。"""
    tables: list[TableBlock] = field(default_factory=list)
