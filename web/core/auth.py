"""会话 Token 生成与校验的独立工具模块，供 routes.py 和 security.py 共同使用，避免循环导入。"""
from __future__ import annotations
import secrets


def generate_session_token(username: str) -> str:
    """生成唯一的、高强度的随机 Session Token，保证每次登录的 Session 均不同。"""
    random_part = secrets.token_hex(24)
    return f"sess_{random_part}"


def verify_session_token(token: str, username: str) -> bool:
    """校验会话 Token 是否处于数据库活跃状态且与特定用户名匹配。"""
    from web.core.db import db
    return db.verify_session(username, token)
