"""外键约束模型。"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ForeignKeyDef:
    """外键定义。"""
    name: str | None       # 外键约束名（可为空）
    columns: list[str]     # 本表字段
    ref_table: str         # 关联表名
    ref_columns: list[str] # 关联字段
    on_delete: str | None  # CASCADE / SET NULL / NO ACTION / ...
    on_update: str | None
