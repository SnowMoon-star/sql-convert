"""方言注册表 — 工厂函数 + 别名映射。"""
from __future__ import annotations
from converter.dialects.base import BaseDialect

_REGISTRY: dict[str, type[BaseDialect]] = {}
_ALIASES: dict[str, str] = {}
_REGISTERED = False


def _ensure_loaded() -> None:
    """确保所有方言类已注册（仅首次调用执行）。"""
    global _REGISTERED
    if not _REGISTERED:
        from converter.dialects import ensure_registered
        ensure_registered()
        _REGISTERED = True


def register(dialect_cls: type[BaseDialect]) -> type[BaseDialect]:
    """装饰器：注册方言类。"""
    name = dialect_cls.__name__.replace("Dialect", "").lower()
    _REGISTRY[name] = dialect_cls
    return dialect_cls


def register_alias(alias: str, target: str) -> None:
    """注册别名，如 pgsql → pgsql。"""
    _ALIASES[alias] = target


def get_dialect(mode: str, database: str | None = None) -> BaseDialect:
    """根据模式名获取方言实例。"""
    _ensure_loaded()
    key = mode.lower()
    key = _ALIASES.get(key, key)
    if key not in _REGISTRY:
        raise ValueError(f"Unsupported dialect mode: {mode}")
    return _REGISTRY[key](database)


# 别名
register_alias("pgsql", "pgsql")
register_alias("postgresql", "pgsql")
register_alias("postgres", "pgsql")
register_alias("sqlite3", "sqlite")
register_alias("pg", "pgsql")
