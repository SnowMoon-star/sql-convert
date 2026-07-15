from __future__ import annotations
import datetime
from core.logger import get_logger
from web.core.db_base import _now_cst


class SettingsDBMixin:
    """系统的 IP 白名单、黑名单封禁及多次登录失败锁定管理相关的数据库操作 Mixin。"""

    # ──────────────────────────────────────────────────────────
    # IP 白名单管理
    # ──────────────────────────────────────────────────────────
    def add_to_whitelist(self: any, ip: str) -> None:
        """添加 IP 至白名单表格。"""
        with self._get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO ip_whitelist (ip) VALUES (?)", (ip.strip(),))
            conn.commit()

    def remove_from_whitelist(self: any, ip: str) -> None:
        """从白名单表格中移除 IP。"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM ip_whitelist WHERE ip = ?", (ip.strip(),))
            conn.commit()

    def get_whitelist(self: any) -> list[str]:
        """获取当前全部有效的白名单 IP 列表。"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT ip FROM ip_whitelist ORDER BY created_at DESC").fetchall()
            return [r["ip"] for r in rows]

    def is_ip_whitelisted(self: any, ip: str) -> bool:
        """检查特定 IP 是否在白名单放行中。"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT 1 FROM ip_whitelist WHERE ip = ?", (ip.strip(),)).fetchone()
            return row is not None

    def list_whitelist(self: any, ip_query: str | None = None) -> list[dict]:
        """获取全部白名单（支持 IP 模糊搜索）。"""
        with self._get_connection() as conn:
            query = "SELECT ip, created_at FROM ip_whitelist"
            params = []
            if ip_query:
                query += " WHERE ip LIKE ?"
                params.append(f"%{ip_query.strip()}%")
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [{"ip": r["ip"], "created_at": r["created_at"]} for r in rows]

    def update_whitelist_ip(self: any, old_ip: str, new_ip: str) -> bool:
        """将已有白名单 IP 修改为新 IP。"""
        with self._get_connection() as conn:
            existing = conn.execute("SELECT 1 FROM ip_whitelist WHERE ip = ?", (new_ip.strip(),)).fetchone()
            if existing:
                return False
            conn.execute("UPDATE ip_whitelist SET ip = ? WHERE ip = ?", (new_ip.strip(), old_ip.strip()))
            conn.commit()
            return True

    def list_login_attempts(self: any, username_query: str | None = None, is_locked: int | None = None) -> list[dict]:
        """获取账号登录锁定监控记录列表。"""
        with self._get_connection() as conn:
            query = "SELECT username, fail_count, lock_time, lock_count, is_permanent_lock FROM login_attempts"
            params = []
            if username_query:
                query += " WHERE username LIKE ?"
                params.append(f"%{username_query.strip()}%")
            query += " ORDER BY username ASC"
            rows = conn.execute(query, params).fetchall()
            
            EAST8 = datetime.timezone(datetime.timedelta(hours=8))
            
            result = []
            for r in rows:
                is_currently_locked = False
                lock_time_formatted = None
                if r["is_permanent_lock"]:
                    is_currently_locked = True
                elif r["lock_time"]:
                    lock_time_naive = datetime.datetime.fromisoformat(r["lock_time"])
                    if lock_time_naive.tzinfo is None:
                        lock_time_utc8 = lock_time_naive.replace(tzinfo=EAST8)
                    else:
                        lock_time_utc8 = lock_time_naive.astimezone(EAST8)
                    
                    now_utc8 = datetime.datetime.now(EAST8)
                    
                    if now_utc8 < lock_time_utc8:
                        is_currently_locked = True
                        lock_time_formatted = lock_time_utc8.strftime("%Y-%m-%d %H:%M:%S")
                
                if is_locked is not None:
                    if int(is_locked) != int(is_currently_locked):
                        continue
                
                result.append({
                    "username": r["username"],
                    "fail_count": r["fail_count"],
                    "lock_time": lock_time_formatted,
                    "lock_count": r["lock_count"],
                    "is_permanent_lock": bool(r["is_permanent_lock"]),
                    "is_locked": is_currently_locked
                })
            return result

    def list_ip_attempts(self: any, ip_query: str | None = None, is_locked: int | None = None) -> list[dict]:
        """获取 IP 封禁监控记录列表。"""
        with self._get_connection() as conn:
            query = "SELECT ip, fail_count, lock_time, is_permanent_lock FROM ip_attempts"
            params = []
            if ip_query:
                query += " WHERE ip LIKE ?"
                params.append(f"%{ip_query.strip()}%")
            query += " ORDER BY ip ASC"
            rows = conn.execute(query, params).fetchall()
            
            EAST8 = datetime.timezone(datetime.timedelta(hours=8))
            
            result = []
            for r in rows:
                is_currently_locked = False
                lock_time_formatted = None
                if r["is_permanent_lock"]:
                    is_currently_locked = True
                elif r["lock_time"]:
                    lock_time_naive = datetime.datetime.fromisoformat(r["lock_time"])
                    if lock_time_naive.tzinfo is None:
                        lock_time_utc8 = lock_time_naive.replace(tzinfo=EAST8)
                    else:
                        lock_time_utc8 = lock_time_naive.astimezone(EAST8)
                    
                    now_utc8 = datetime.datetime.now(EAST8)
                    
                    if now_utc8 < lock_time_utc8:
                        is_currently_locked = True
                        lock_time_formatted = lock_time_utc8.strftime("%Y-%m-%d %H:%M:%S")
                
                if is_locked is not None:
                    if int(is_locked) != int(is_currently_locked):
                        continue
                
                result.append({
                    "ip": r["ip"],
                    "fail_count": r["fail_count"],
                    "lock_time": lock_time_formatted,
                    "is_permanent_lock": bool(r["is_permanent_lock"]),
                    "is_locked": is_currently_locked
                })
            return result

    def create_login_attempt(self: any, username: str, fail_count: int = 0, lock_time: str | None = None, lock_count: int = 0, is_permanent_lock: int = 0) -> bool:
        """为指定账号新建锁定监控记录（如果不存在的话）。"""
        with self._get_connection() as conn:
            existing = conn.execute("SELECT 1 FROM login_attempts WHERE username = ?", (username.strip(),)).fetchone()
            if existing:
                return False
            conn.execute(
                """
                INSERT INTO login_attempts (username, fail_count, lock_time, lock_count, is_permanent_lock)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username.strip(), fail_count, lock_time, lock_count, is_permanent_lock)
            )
            conn.commit()
            return True

    def update_login_attempt(self: any, username: str, fail_count: int, lock_time: str | None, lock_count: int, is_permanent_lock: int) -> bool:
        """更新指定账号的锁定监控状态，存在则更新，不存在则返回 False。"""
        with self._get_connection() as conn:
            existing = conn.execute("SELECT 1 FROM login_attempts WHERE username = ?", (username.strip(),)).fetchone()
            if not existing:
                return False
            conn.execute(
                """
                UPDATE login_attempts
                SET fail_count = ?, lock_time = ?, lock_count = ?, is_permanent_lock = ?
                WHERE username = ?
                """,
                (fail_count, lock_time, lock_count, is_permanent_lock, username.strip())
            )
            conn.commit()
            return True

    def delete_login_attempt(self: any, username: str) -> bool:
        """删除指定账号的锁定监控记录。"""
        with self._get_connection() as conn:
            existing = conn.execute("SELECT 1 FROM login_attempts WHERE username = ?", (username.strip(),)).fetchone()
            if not existing:
                return False
            conn.execute("DELETE FROM login_attempts WHERE username = ?", (username.strip(),))
            conn.commit()
            return True

    # ──────────────────────────────────────────────────────────
    # 账户多次失败锁定机制 (Account Lockout Attempts)
    # ──────────────────────────────────────────────────────────
    def get_login_attempts(self: any, username: str) -> tuple[int, str | None, int, int]:
        """获取指定账号的安全尝试状态，返回: (fail_count, lock_time, lock_count, is_permanent_lock)。"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT fail_count, lock_time, lock_count, is_permanent_lock FROM login_attempts WHERE username = ?", (username.strip(),)).fetchone()
            if not row:
                return 0, None, 0, 0
            return row["fail_count"], row["lock_time"], row["lock_count"], row["is_permanent_lock"]

    def update_login_attempts(self: any, username: str, fail_count: int, lock_time: str | None, lock_count: int, is_permanent_lock: int) -> None:
        """更新指定账号的失败尝试与锁状态。"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO login_attempts (username, fail_count, lock_time, lock_count, is_permanent_lock)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username.strip(), fail_count, lock_time, lock_count, is_permanent_lock)
            )
            conn.commit()

    def reset_login_attempts(self: any, username: str) -> None:
        """重置指定账号的所有锁定惩罚（成功登录时触发）。"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM login_attempts WHERE username = ?", (username.strip(),))
            conn.commit()

    # ──────────────────────────────────────────────────────────
    # IP 失败封禁黑名单机制 (IP Ban Attempts)
    # ──────────────────────────────────────────────────────────
    def get_ip_attempts(self: any, ip: str) -> tuple[int, str | None, int]:
        """获取指定 IP 的失败与封禁状态，返回: (fail_count, lock_time, is_permanent_lock)。"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT fail_count, lock_time, is_permanent_lock FROM ip_attempts WHERE ip = ?", (ip.strip(),)).fetchone()
            if not row:
                return 0, None, 0
            return row["fail_count"], row["lock_time"], row["is_permanent_lock"]

    def update_ip_attempts(self: any, ip: str, fail_count: int, lock_time: str | None, is_permanent_lock: int) -> None:
        """更新 IP 封禁与计数状态。"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ip_attempts (ip, fail_count, lock_time, is_permanent_lock)
                VALUES (?, ?, ?, ?)
                """,
                (ip.strip(), fail_count, lock_time, is_permanent_lock)
            )
            conn.commit()

    def reset_ip_attempts(self: any, ip: str) -> None:
        """重置特定 IP 的封禁（管理员手动解锁）。"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM ip_attempts WHERE ip = ?", (ip.strip(),))
            conn.commit()

    # ──────────────────────────────────────────────────────────
    # 管理员控制台命令行强制解锁逻辑 (CLI Bypass)
    # ──────────────────────────────────────────────────────────
    def unlock_user(self: any, username: str) -> bool:
        """管理员解锁用户，清空锁定频次。"""
        self.reset_login_attempts(username)
        get_logger().info(f"[DB] 管理员命令行手动解锁账号成功: {username}")
        return True

    def unlock_ip(self: any, ip: str) -> bool:
        """管理员解锁 IP，清空封禁。"""
        self.reset_ip_attempts(ip)
        get_logger().info(f"[DB] 管理员命令行手动解锁 IP 成功: {ip}")
        return True
