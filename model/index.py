"""索引定义模型。"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class IndexDef:
    """索引定义。"""
    name: str              # 索引名
    columns: list[str]     # 字段列表（不含引号）
    unique: bool           # True = UNIQUE KEY, False = KEY/INDEX
    comment: str | None    # 索引注释
