from __future__ import annotations
import datetime
import json
from pathlib import Path
from web.core.scheduler import TaskInfo
from web.core.db_base import _now_cst, calculate_signature, verify_signature
from core.logger import get_logger


class TasksDBMixin:
    """任务 CRUD 管理相关的数据库操作 Mixin。"""

    def save_task(self: any, task: TaskInfo) -> None:
        """持久化保存/更新一个任务的最新状态到 SQLite（包含生成 HMAC 签名）。"""
        sig = calculate_signature(task.task_id, task.status, task.output_file, task.report_html)
        progress_str = json.dumps(task.progress)

        with self._get_connection() as conn:
            existing = conn.execute("SELECT created_at, completed_at FROM tasks WHERE task_id = ?", (task.task_id,)).fetchone()
            created_at = existing["created_at"] if existing else _now_cst()
            completed_at = getattr(task, "completed_at", None) or (existing["completed_at"] if existing else None)

            conn.execute(
                """
                INSERT OR REPLACE INTO tasks 
                (task_id, filename, file_hash, source_mode, target_mode, status, progress, error, output_file, report_html, signature, username, convert_type, duration, created_at, updated_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.filename,
                    getattr(task, "file_hash", ""),
                    task.source_mode,
                    task.target_mode,
                    task.status,
                    progress_str,
                    task.error,
                    task.output_file,
                    task.report_html,
                    sig,
                    task.username,
                    getattr(task, "convert_type", "online"),
                    getattr(task, "duration", 0.0),
                    created_at,
                    _now_cst(),
                    completed_at
                )
            )
            conn.commit()

    def get_task(self: any, task_id: str) -> tuple[TaskInfo | None, bool]:
        """获取单个任务的最新值（含防篡改验签）。"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if not row:
                return None, True

            is_verified = verify_signature(
                row["task_id"],
                row["status"],
                row["output_file"],
                row["report_html"],
                row["signature"]
            )

            progress_data = {}
            if row["progress"]:
                try:
                    progress_data = json.loads(row["progress"])
                except Exception:
                    pass

            task = TaskInfo(
                task_id=row["task_id"],
                filename=row["filename"],
                source_mode=row["source_mode"],
                target_mode=row["target_mode"],
                status=row["status"],
                progress=progress_data,
                error=row["error"],
                output_file=row["output_file"],
                report_html=row["report_html"],
                username=row["username"],
                convert_type=row["convert_type"] if "convert_type" in row.keys() else "online",
                duration=row["duration"] if "duration" in row.keys() else 0.0,
                completed_at=row["completed_at"] if "completed_at" in row.keys() else None
            )
            setattr(task, "file_hash", row["file_hash"])
            setattr(task, "created_at", row["created_at"])
            setattr(task, "updated_at", row["updated_at"])
            return task, is_verified

    def list_tasks(self: any) -> list[tuple[TaskInfo, bool]]:
        """获取所有任务列表，每项任务都进行防篡改安全校验。"""
        results = []
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            for row in cursor.fetchall():
                task, is_verified = self._row_to_task(row)
                results.append((task, is_verified))
        return results

    def list_tasks_paginated(self: any, page: int = 1, page_size: int = 10,
                             filename: str | None = None,
                             status: str | None = None,
                             date_from: str | None = None, date_to: str | None = None) -> tuple[list[tuple[TaskInfo, bool]], int]:
        """分页查询任务列表，支持文件名搜索、状态和时间范围筛选。"""
        results = []
        offset = (page - 1) * page_size
        with self._get_connection() as conn:
            where_clauses = []
            params = []
            if filename:
                where_clauses.append("(filename LIKE ? OR task_id LIKE ?)")
                params.append(f"%{filename}%")
                params.append(f"%{filename}%")
            if status:
                where_clauses.append("status = ?")
                params.append(status)
            if date_from:
                where_clauses.append("created_at >= ?")
                params.append(date_from)
            if date_to:
                where_clauses.append("created_at <= ?")
                params.append(date_to)
            where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
            total = conn.execute(f"SELECT COUNT(*) as cnt FROM tasks {where}", params).fetchone()["cnt"]
            cursor = conn.execute(
                f"SELECT * FROM tasks {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            for row in cursor.fetchall():
                task, is_verified = self._row_to_task(row)
                results.append((task, is_verified))
        return results, total

    def _row_to_task(self: any, row) -> tuple[TaskInfo, bool]:
        """将数据库行转换为 (TaskInfo, is_verified) 元组。"""
        is_verified = verify_signature(
            row["task_id"],
            row["status"],
            row["output_file"],
            row["report_html"],
            row["signature"]
        )
        progress_data = {}
        if row["progress"]:
            try:
                progress_data = json.loads(row["progress"])
            except Exception:
                pass

        task = TaskInfo(
            task_id=row["task_id"],
            filename=row["filename"],
            source_mode=row["source_mode"],
            target_mode=row["target_mode"],
            status=row["status"],
            progress=progress_data,
            error=row["error"],
            output_file=row["output_file"],
            report_html=row["report_html"],
            username=row["username"],
            convert_type=row["convert_type"] if "convert_type" in row.keys() else "online",
            duration=row["duration"] if "duration" in row.keys() else 0.0,
            completed_at=row["completed_at"] if "completed_at" in row.keys() else None
        )
        setattr(task, "file_hash", row["file_hash"])
        setattr(task, "created_at", row["created_at"])
        setattr(task, "updated_at", row["updated_at"])
        return task, is_verified

    def delete_old_tasks(self: any, days: int) -> list[dict[str, str]]:
        """根据保留策略物理删除过期记录。"""
        get_logger().info(f"[DB] 执行历史保留清理策略，删除 {days} 天前的历史记录")
        files_to_delete = []
        time_limit = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT task_id, output_file, report_html FROM tasks WHERE created_at < ?", 
                (time_limit,)
            )
            for row in cursor.fetchall():
                files_to_delete.append({
                    "task_id": row["task_id"],
                    "output_file": row["output_file"],
                    "report_html": row["report_html"]
                })
            
            if files_to_delete:
                conn.execute("DELETE FROM tasks WHERE created_at < ?", (time_limit,))
                conn.commit()
                get_logger().info(f"[DB] 已成功从数据库清除 {len(files_to_delete)} 条历史任务。")

        return files_to_delete
