"""列定义模型。"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ColumnDef:
    """列定义。"""
    name: str              # 字段名（不含引号）
    type_: str             # 完整类型+约束声明，如 "INT NOT NULL AUTO_INCREMENT"
    comment: str | None    # COMMENT 'xxx' 注释文本（不含引号）
