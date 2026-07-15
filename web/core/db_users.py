from __future__ import annotations
import datetime
from core.logger import get_logger
from web.core.db_base import _now_cst


class UsersDBMixin:
    """用户 CRUD 安全管理的数据库操作 Mixin。"""

    def get_user(self: any, username: str) -> tuple[str, str, int, str | None] | None:
        """读取指定账号，返回: (password_hash, salt, is_admin, avatar)。"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT password_hash, salt, is_admin, avatar FROM users WHERE username = ?", (username.strip(),)).fetchone()
            if not row:
                return None
            return row["password_hash"], row["salt"], row["is_admin"], row["avatar"]

    def list_users(self: any, username: str | None = None, is_admin: int | None = None, is_locked: int | None = None) -> list[dict]:
        """获取所有用户列表及其锁定状态（管理员用），支持搜索过滤。"""
        with self._get_connection() as conn:
            users = conn.execute(
                "SELECT username, is_admin, avatar, created_at FROM users ORDER BY created_at DESC"
            ).fetchall()
            result = []
            for u in users:
                lock_row = conn.execute(
                    "SELECT fail_count, lock_time, lock_count, is_permanent_lock FROM login_attempts WHERE username = ?",
                    (u["username"],)
                ).fetchone()
                is_locked_status = False
                if lock_row:
                    if lock_row["is_permanent_lock"]:
                        is_locked_status = True
                    elif lock_row["lock_time"]:
                        lock_time = datetime.datetime.fromisoformat(lock_row["lock_time"])
                        if lock_time.tzinfo is None:
                            lock_time = lock_time.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
                        if datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))) < lock_time:
                            is_locked_status = True
                
                # 模糊匹配用户名
                if username and username.strip().lower() not in u["username"].lower():
                    continue
                # 精确匹配角色
                if is_admin is not None and int(u["is_admin"]) != int(is_admin):
                    continue
                # 精确匹配锁定状态
                if is_locked is not None and int(is_locked_status) != int(is_locked):
                    continue

                result.append({
                    "username": u["username"],
                    "is_admin": bool(u["is_admin"]),
                    "avatar": u["avatar"],
                    "created_at": u["created_at"],
                    "is_locked": is_locked_status,
                    "fail_count": lock_row["fail_count"] if lock_row else 0
                })
            return result

    def create_user(self: any, username: str, password_hash: str, salt: str, is_admin: int = 0) -> bool:
        """创建新用户，已存在则返回 False。"""
        with self._get_connection() as conn:
            existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username.strip(),)).fetchone()
            if existing:
                return False
            conn.execute(
                "INSERT INTO users (username, password_hash, salt, is_admin, created_at) VALUES (?, ?, ?, ?, ?)",
                (username.strip(), password_hash, salt, is_admin, _now_cst())
            )
            conn.commit()
            get_logger().info(f"[DB] 管理员创建新用户: {username}")
            return True

    def update_user(self: any, username: str, password_hash: str | None = None, salt: str | None = None, is_admin: int | None = None, avatar: str | None = ...) -> bool:
        """更新用户密码、角色或头像，用户不存在则返回 False。avatar 传 None 表示清空，不传则保持原值。"""
        with self._get_connection() as conn:
            existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username.strip(),)).fetchone()
            if not existing:
                return False
            if password_hash and salt:
                conn.execute(
                    "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
                    (password_hash, salt, username.strip())
                )
            if is_admin is not None:
                conn.execute(
                    "UPDATE users SET is_admin = ? WHERE username = ?",
                    (is_admin, username.strip())
                )
            # avatar 使用哨兵默认值 `...`，仅在调用方明确传入时才更新
            if avatar is not ...:
                conn.execute(
                    "UPDATE users SET avatar = ? WHERE username = ?",
                    (avatar, username.strip())
                )
            conn.commit()
            get_logger().info(f"[DB] 更新用户: {username}")
            return True

    def delete_user(self: any, username: str) -> bool:
        """删除用户及关联的锁定记录。"""
        with self._get_connection() as conn:
            existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username.strip(),)).fetchone()
            if not existing:
                return False
            conn.execute("DELETE FROM users WHERE username = ?", (username.strip(),))
            conn.execute("DELETE FROM login_attempts WHERE username = ?", (username.strip(),))
            conn.commit()
            get_logger().info(f"[DB] 管理员删除用户: {username}")
            return True
