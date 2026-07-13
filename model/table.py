"""表结构定义模型。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from model.column import ColumnDef
from model.index import IndexDef
from model.constraint import ForeignKeyDef

@dataclass
class InsertBlock:
    """单条 INSERT 语句的数据（用于兼容老版本）。"""
    columns: list[str] = field(default_factory=list)
    values: list[list[str]] = field(default_factory=list)


@dataclass
class TableBlock:
    """一个表的完整结构定义（建表 schema 基础单元）。"""
    database: str | None   # 数据库名
    name: str              # 表名
    comment: str | None    # 表 COMMENT
    columns: list[ColumnDef] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    indexes: list[IndexDef] = field(default_factory=list)
    foreign_keys: list[ForeignKeyDef] = field(default_factory=list)
    inserts: list[Any] = field(default_factory=list)
