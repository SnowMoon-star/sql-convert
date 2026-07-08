"""方言包 — 提供方言基类和延迟注册入口。"""

from converter.dialects.base import BaseDialect


def ensure_registered() -> None:
    """确保所有方言已被 @register 装饰器注册。

    延迟导入以打破：registry → dialects.__init__ → mysql → registry 的循环。
    """
    # 触发每个方言模块的 @register 装饰器
    from converter.dialects.mysql import MysqlDialect       # noqa: F401
    from converter.dialects.kingbase import KingbaseDialect  # noqa: F401
    from converter.dialects.pgsql import PgsqlDialect        # noqa: F401
    from converter.dialects.sqlite import SqliteDialect      # noqa: F401
    from converter.dialects.oracle import OracleDialect      # noqa: F401


__all__ = [
    "BaseDialect",
    "ensure_registered",
]
