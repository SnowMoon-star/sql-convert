"""SQLite 数据库与数据持久化安全组件 — 包含数据模型序列化、HMAC 验签防篡改、历史保留期自动清理、用户加盐哈希与 IP/账号锁定。"""
from __future__ import annotations

from web.core.db_base import DatabaseManagerBase, calculate_signature, verify_signature, hash_password
from web.core.db_settings import SettingsDBMixin
from web.core.db_active_users import ActiveUsersDBMixin
from web.core.db_users import UsersDBMixin
from web.core.db_tasks import TasksDBMixin
from web.core.db_logs import LogsDBMixin


class DatabaseManager(SettingsDBMixin, ActiveUsersDBMixin, UsersDBMixin, TasksDBMixin, LogsDBMixin, DatabaseManagerBase):
    """SQLite 持久化连接管理器，支持业务及安全控制表的动态扩建与多功能模块 Mixin。"""
    pass


# 全局单例数据库实例
db = DatabaseManager()
