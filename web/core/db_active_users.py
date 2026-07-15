from __future__ import annotations
from web.core.db_base import _now_cst, _session_expires_at


class ActiveUsersDBMixin:
    """活跃用户会话管理的数据库操作 Mixin。"""

    # ──────────────────────────────────────────────────────────
    # 会话管理 (支持同一账号单地登录/多地登录控制)
    # ──────────────────────────────────────────────────────────
    def add_session(self: any, username: str, session_token: str, ip: str = None) -> None:
        """往数据库中添加新的活跃会话记录，并设置初始过期时刻。"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_sessions (username, session_token, ip, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                (username.strip(), session_token, ip, _now_cst(), _session_expires_at())
            )
            conn.commit()

    def verify_session(self: any, username: str, session_token: str) -> bool:
        """校验特定用户名与 Session Token 的映射是否在数据库中活跃且未过期。"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM user_sessions WHERE username = ? AND session_token = ? AND (expires_at IS NULL OR expires_at > ?)",
                (username.strip(), session_token, _now_cst())
            ).fetchone()
            return row is not None

    def delete_session(self: any, session_token: str) -> None:
        """注销/删除指定的 Session Token。"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
            conn.commit()

    def clear_user_sessions(self: any, username: str) -> None:
        """清空指定用户的所有活跃 Session 记录（用于挤退该账号在其他地方的登录）。"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM user_sessions WHERE username = ?", (username.strip(),))
            conn.commit()

    def get_username_by_session(self: any, session_token: str) -> str | None:
        """通过 Session Token 反查对应的用户名（活跃且未过期状态下）。"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT username FROM user_sessions WHERE session_token = ? AND (expires_at IS NULL OR expires_at > ?)",
                (session_token, _now_cst())
            ).fetchone()
            return row["username"] if row else None

    def touch_session(self: any, session_token: str) -> None:
        """刷新指定 Session Token 的过期时刻，实现滑动窗口续期。每次合法 API 请求均会调用此方法。"""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE user_sessions SET expires_at = ? WHERE session_token = ?",
                (_session_expires_at(), session_token)
            )
            conn.commit()

    def delete_expired_sessions(self: any) -> int:
        """删除所有已超过 expires_at 过期时刻的 Session 记录，返回删除行数。由定时清理任务调用。"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM user_sessions WHERE expires_at IS NOT NULL AND expires_at <= ?",
                (_now_cst(),)
            )
            conn.commit()
            return cursor.rowcount

    def list_active_sessions(self: any, page: int, size: int, username: str = None, ip: str = None, is_admin: int = None) -> tuple[list[dict], int]:
        """分页获取当前活跃的 Session 记录，并支持用户名、IP 模糊查询，以及角色过滤。"""
        offset = (page - 1) * size
        conditions = []
        params = []
        if username and username.strip():
            conditions.append("s.username LIKE ?")
            params.append(f"%{username.strip()}%")
        if ip and ip.strip():
            conditions.append("s.ip LIKE ?")
            params.append(f"%{ip.strip()}%")
        if is_admin is not None:
            conditions.append("u.is_admin = ?")
            params.append(is_admin)
            
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
            
        count_sql = f"""
            SELECT COUNT(*) as cnt 
            FROM user_sessions s
            LEFT JOIN users u ON s.username = u.username
            {where_clause}
        """
        query_sql = f"""
            SELECT s.username, s.session_token, s.ip, s.created_at, s.expires_at, u.avatar, u.is_admin
            FROM user_sessions s
            LEFT JOIN users u ON s.username = u.username
            {where_clause}
            ORDER BY s.created_at DESC
            LIMIT ? OFFSET ?
        """
        
        with self._get_connection() as conn:
            count_row = conn.execute(count_sql, params).fetchone()
            total = count_row["cnt"] if count_row else 0
            
            query_params = params + [size, offset]
            rows = conn.execute(query_sql, query_params).fetchall()
            
            items = []
            for r in rows:
                items.append({
                    "username": r["username"],
                    "session_token": r["session_token"],
                    "ip": r["ip"] or "",
                    "created_at": r["created_at"],
                    "expires_at": r["expires_at"] or "",
                    "avatar": r["avatar"] or "",
                    "is_admin": r["is_admin"] if r["is_admin"] is not None else 0
                })
            return items, total
