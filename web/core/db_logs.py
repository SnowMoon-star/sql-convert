from __future__ import annotations
from web.core.db_base import _now_cst


class LogsDBMixin:
    """审计日志管理相关的数据库操作 Mixin。"""

    # ──────────────────────────────────────────────────────────
    # 审计日志写入接口
    # ──────────────────────────────────────────────────────────
    def write_login_log(self: any, username: str, ip: str, status: str, msg: str | None = None) -> None:
        """记录登录审计日志。"""
        ts = _now_cst()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO login_logs (username, ip, status, msg, created_at) VALUES (?, ?, ?, ?, ?)",
                (username.strip(), ip.strip(), status.strip(), msg, ts)
            )
            conn.commit()

    def write_operation_log(self: any, username: str, ip: str, action: str, detail: str | None = None, status: str = "SUCCESS") -> None:
        """记录用户敏感操作审计日志。"""
        ts = _now_cst()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO operation_logs (username, ip, action, detail, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (username.strip(), ip.strip(), action.strip(), detail, status, ts)
            )
            conn.commit()

    def write_timer_log(self: any, action: str, deleted_tasks: int, deleted_files: int, status: str, detail: str | None = None) -> None:
        """记录定时任务执行审计日志。"""
        ts = _now_cst()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO timer_logs (action, deleted_tasks, deleted_files, status, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (action.strip(), deleted_tasks, deleted_files, status.strip(), detail, ts)
            )
            conn.commit()

    # ──────────────────────────────────────────────────────────
    # 审计日志查询（管理员功能）
    # ──────────────────────────────────────────────────────────
    def query_login_logs(self: any, page: int = 1, page_size: int = 10,
                         username: str | None = None, status: str | None = None,
                         date_from: str | None = None, date_to: str | None = None) -> tuple[list[dict], int]:
        """分页查询登录审计日志，返回 (日志列表, 总数)。"""
        with self._get_connection() as conn:
            where_clauses = []
            params = []
            if username:
                where_clauses.append("username LIKE ?")
                params.append(f"%{username.strip()}%")
            if status:
                where_clauses.append("status = ?")
                params.append(status.strip())
            if date_from:
                where_clauses.append("created_at >= ?")
                params.append(date_from)
            if date_to:
                where_clauses.append("created_at <= ?")
                params.append(date_to)

            where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
            count_row = conn.execute(f"SELECT COUNT(*) as cnt FROM login_logs {where}", params).fetchone()
            total = count_row["cnt"] if count_row else 0

            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM login_logs {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()
            return [dict(r) for r in rows], total

    def query_operation_logs(self: any, page: int = 1, page_size: int = 10,
                             username: str | None = None, action: str | None = None,
                             status: str | None = None,
                             date_from: str | None = None, date_to: str | None = None) -> tuple[list[dict], int]:
        """分页查询操作审计日志，返回 (日志列表, 总数)。"""
        with self._get_connection() as conn:
            where_clauses = []
            params = []
            if username:
                where_clauses.append("username LIKE ?")
                params.append(f"%{username.strip()}%")
            if action:
                where_clauses.append("action = ?")
                params.append(action.strip())
            if status:
                where_clauses.append("status = ?")
                params.append(status.strip())
            if date_from:
                where_clauses.append("created_at >= ?")
                params.append(date_from)
            if date_to:
                where_clauses.append("created_at <= ?")
                params.append(date_to)

            where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
            count_row = conn.execute(f"SELECT COUNT(*) as cnt FROM operation_logs {where}", params).fetchone()
            total = count_row["cnt"] if count_row else 0

            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM operation_logs {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()
            return [dict(r) for r in rows], total

    def query_timer_logs(self: any, page: int = 1, page_size: int = 10,
                         action: str | None = None,
                         status: str | None = None,
                         date_from: str | None = None, date_to: str | None = None) -> tuple[list[dict], int]:
        """分页查询定时任务日志，返回 (日志列表, 总数)。"""
        with self._get_connection() as conn:
            where_clauses = []
            params = []
            if action:
                where_clauses.append("action = ?")
                params.append(action.strip())
            if status:
                where_clauses.append("status = ?")
                params.append(status.strip())
            if date_from:
                where_clauses.append("created_at >= ?")
                params.append(date_from)
            if date_to:
                where_clauses.append("created_at <= ?")
                params.append(date_to)

            where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
            count_row = conn.execute(f"SELECT COUNT(*) as cnt FROM timer_logs {where}", params).fetchone()
            total = count_row["cnt"] if count_row else 0

            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM timer_logs {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()
            return [dict(r) for r in rows], total

    # ──────────────────────────────────────────────────────────
    # 审计日志清理（定时物理删除）
    # ──────────────────────────────────────────────────────────
    def delete_old_logs(self: any, login_days: int, operation_days: int, timer_days: int) -> dict[str, int]:
        """按照东八区当前时间，物理删除各日志表中超出保留期的过期记录。

        Args:
            login_days:     登录日志保留天数（超出此天数的记录将被删除）
            operation_days: 操作日志保留天数（超出此天数的记录将被删除）
            timer_days:     定时任务日志保留天数（超出此天数的记录将被删除）

        Returns:
            各表实际删除的行数字典，格式：
            {"login_logs": N, "operation_logs": N, "timer_logs": N}
        """
        from datetime import datetime, timezone, timedelta
        from core.logger import get_logger

        # 统一以东八区（CST, UTC+8）当前时间为基准计算各表的截止时间
        now_cst = datetime.now(timezone.utc) + timedelta(hours=8)

        cutoff_login     = (now_cst - timedelta(days=login_days)).strftime("%Y-%m-%d %H:%M:%S")
        cutoff_operation = (now_cst - timedelta(days=operation_days)).strftime("%Y-%m-%d %H:%M:%S")
        cutoff_timer     = (now_cst - timedelta(days=timer_days)).strftime("%Y-%m-%d %H:%M:%S")

        deleted_counts: dict[str, int] = {
            "login_logs":     0,
            "operation_logs": 0,
            "timer_logs":     0,
        }

        with self._get_connection() as conn:
            # 清理登录日志
            cursor = conn.execute("DELETE FROM login_logs WHERE created_at < ?", (cutoff_login,))
            deleted_counts["login_logs"] = cursor.rowcount
            get_logger().info(
                f"[DB] 清理登录日志：删除 {deleted_counts['login_logs']} 条（截止时间: {cutoff_login}，保留 {login_days} 天）"
            )

            # 清理操作日志
            cursor = conn.execute("DELETE FROM operation_logs WHERE created_at < ?", (cutoff_operation,))
            deleted_counts["operation_logs"] = cursor.rowcount
            get_logger().info(
                f"[DB] 清理操作日志：删除 {deleted_counts['operation_logs']} 条（截止时间: {cutoff_operation}，保留 {operation_days} 天）"
            )

            # 清理定时任务日志（需最后删除，避免本次清理日志在写入前即被清除）
            cursor = conn.execute("DELETE FROM timer_logs WHERE created_at < ?", (cutoff_timer,))
            deleted_counts["timer_logs"] = cursor.rowcount
            get_logger().info(
                f"[DB] 清理定时任务日志：删除 {deleted_counts['timer_logs']} 条（截止时间: {cutoff_timer}，保留 {timer_days} 天）"
            )

            conn.commit()

        return deleted_counts
