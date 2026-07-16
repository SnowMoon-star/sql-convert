"""异步任务调度与线程隔离管理器 — 驱动计算密集的 SQL 转换在独立工作线程中运行，并利用 SQLite 数据库进行状态持久化。"""
from __future__ import annotations
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
import uuid
from typing import Any, Callable, Dict

from main import convert
from utils.report import ConversionReport
from utils.config_manager import config
from core.logger import get_logger


@dataclass
class TaskInfo:
    """转换任务状态实体。"""
    task_id: str
    filename: str
    source_mode: str
    target_mode: str
    status: str  # PENDING, RUNNING, SUCCESS, FAILED
    progress: dict[str, Any] = field(default_factory=lambda: {
        "current_line": 0,
        "table_count": 0,
        "index_count": 0,
        "constraint_count": 0,
        "warning_count": 0,
        "failure_count": 0
    })
    error: str | None = None
    output_file: str | None = None
    report_html: str | None = None
    username: str | None = None
    convert_type: str = "online"
    duration: float = 0.0
    completed_at: str | None = None


class TaskScheduler:
    """任务调度管理器 (单例)。"""

    def __init__(self):
        # 从全局 YAML 配置读取最大并发线程数
        max_workers = config.get("web.max_workers", 4)
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="sql-conv-worker")
        
        # 活跃的 WebSocket 消息队列字典 (key=username, 值为该用户的监听 Queue 集合，以支持多标签页/多端并发登录)
        self.ws_queues: Dict[str, set[asyncio.Queue]] = {}

    @property
    def tasks(self) -> dict[str, TaskInfo]:
        """向后兼容属性：拉取数据库中所有缓存的任务记录。"""
        from web.core.db import db
        raw_list = db.list_tasks()
        return {task.task_id: task for task, _ in raw_list}

    def create_task(self, filename: str, source_mode: str, target_mode: str, file_hash: str, username: str | None = None, convert_type: str = "online") -> str:
        """创建一个处于 PENDING 状态的新任务并存入 SQLite 数据库。"""
        from web.core.db import db
        task_id = str(uuid.uuid4())
        task = TaskInfo(
            task_id=task_id,
            filename=filename,
            source_mode=source_mode,
            target_mode=target_mode,
            status="PENDING",
            username=username,
            convert_type=convert_type,
            duration=0.0
        )
        setattr(task, "file_hash", file_hash)
        
        # 持久化至 SQLite
        db.save_task(task)
        get_logger().info(f"[Scheduler] 创建持久化任务 {task_id}，创建用户: {username}，目标文件: {filename} ({source_mode} -> {target_mode})")
        return task_id

    def submit_task(self, task_id: str, input_path: Path, output_path: Path, loop: asyncio.AbstractEventLoop) -> None:
        """提交任务到子线程池运行。"""
        from web.core.db import db
        task, _ = db.get_task(task_id)
        if not task:
            return

        task.status = "RUNNING"
        db.save_task(task)
        
        get_logger().info(f"[Scheduler] 提交任务 {task_id} 至子工作线程池执行")
        self._broadcast(task, loop)

        # 提交子线程
        self.executor.submit(
            self._run_conversion,
            task_id,
            input_path,
            output_path,
            task.source_mode,
            task.target_mode,
            loop
        )

    def register_ws_queue(self, username: str, queue: asyncio.Queue) -> None:
        """注册 WebSocket 监听队列，以 username 为 key，支持一个用户对应多个监听队列。"""
        if username not in self.ws_queues:
            self.ws_queues[username] = set()
        self.ws_queues[username].add(queue)

    def unregister_ws_queue(self, username: str, queue: asyncio.Queue) -> None:
        """注销特定的 WebSocket 监听队列（精确比对实例，防止并发冲突）。"""
        if username in self.ws_queues:
            self.ws_queues[username].discard(queue)
            if not self.ws_queues[username]:
                self.ws_queues.pop(username, None)

    def shutdown_all_ws(self) -> None:
        """服务关闭时释放所有 WebSocket 连接并清空字典。"""
        for queues in self.ws_queues.values():
            for q in queues:
                q.put_nowait(None)  # 给每个队列发退出信号
        self.ws_queues.clear()

    def _broadcast_to_recipients(self, username: str, message: dict, loop: asyncio.AbstractEventLoop) -> None:
        """安全地向指定用户的所有活跃连接以及 admin 广播消息。"""
        if not self.ws_queues:
            return
        recipients = set()
        # 1. 广播给任务创建者
        if username in self.ws_queues:
            recipients.update(self.ws_queues[username])
        # 2. 广播给所有 active 的 admin 用户
        if "admin" in self.ws_queues:
            recipients.update(self.ws_queues["admin"])

        for q in recipients:
            loop.call_soon_threadsafe(q.put_nowait, message)

    def _broadcast(self, task: TaskInfo, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """向任务所属用户及 admin 广播任务进度状态。"""
        if not self.ws_queues:
            return
        message = {
            "type": "status_change",
            "task_id": task.task_id,
            "filename": task.filename,
            "source_mode": task.source_mode,
            "target_mode": task.target_mode,
            "status": task.status,
            "progress": task.progress,
            "error": task.error,
            "output_file": task.output_file,
            "report_html": task.report_html
        }
        
        recipients = set()
        if task.username in self.ws_queues:
            recipients.update(self.ws_queues[task.username])
        if "admin" in self.ws_queues:
            recipients.update(self.ws_queues["admin"])

        if loop and loop.is_running():
            for q in recipients:
                loop.call_soon_threadsafe(q.put_nowait, message)
        else:
            for q in recipients:
                q.put_nowait(message)

    # ── 定义可执行的操作名称列表 ──
    OPERATIONS = ["task_history", "timer_log", "login_log", "operation_log", "activate_user", "auto_unlock"]

    def run_single_operation(self, op_name: str) -> dict:
        """运行单个清理操作，返回执行结果摘要字典。

        Args:
            op_name: 操作名称，可选值：task_history, timer_log, login_log, operation_log, activate_user

        Returns:
            {"status": "SUCCESS"|"SKIPPED"|"FAILED", "detail": str, "metrics": dict}
        """
        import time
        from web.core.db import db
        from datetime import datetime, timezone, timedelta

        handler = getattr(self, f"_run_{op_name}", None)
        if handler is None:
            return {"status": "SKIPPED", "detail": f"未知操作: {op_name}", "metrics": {}}

        start = time.time()
        try:
            result = handler()
            elapsed = time.time() - start
            metrics = result.get("metrics", {})
            detail = result.get("detail", f"耗时 {elapsed:.3f} 秒")
            status = result.get("status", "SUCCESS")

            db.write_timer_log(
                action=op_name.upper(),
                deleted_tasks=metrics.get("deleted_tasks", 0),
                deleted_files=metrics.get("deleted_files", 0),
                status=status,
                detail=detail,
            )
            get_logger().info(f"[Cleanup] {op_name}: {detail}")
            return {"status": status, "detail": detail, "metrics": metrics}
        except Exception as e:
            elapsed = time.time() - start
            db.write_timer_log(
                action=op_name.upper(),
                deleted_tasks=0,
                deleted_files=0,
                status="FAILED",
                detail=f"执行失败，耗时 {elapsed:.3f} 秒。错误: {str(e)}"
            )
            get_logger().error(f"[Cleanup] {op_name} 执行失败: {e}")
            return {"status": "FAILED", "detail": str(e), "metrics": {}}

    def _get_op_config(self, op_name: str) -> dict:
        """读取单个清理操作的配置。"""
        prefix = f"cleanup_scheduler.{op_name}"
        cfg = {"enabled": config.get(f"{prefix}.enabled", True)}
        if op_name in ("task_history", "timer_log", "login_log", "operation_log"):
            cfg["cron"] = config.get(f"{prefix}.cron", "0 3 * * *")
            cfg["retention_days"] = config.get(f"{prefix}.retention_days", 30)
        elif op_name in ("activate_user", "auto_unlock"):
            cfg["cron"] = config.get(f"{prefix}.cron", "* * * * *")
        return cfg

    def _run_task_history(self) -> dict:
        """清理历史 SQL 转换任务记录及关联磁盘文件。"""
        from web.core.db import db
        cfg = self._get_op_config("task_history")
        if not cfg["enabled"]:
            return {"status": "SKIPPED", "detail": "未启用", "metrics": {}}

        retention_days = cfg.get("retention_days", 30)
        deleted_files = db.delete_old_tasks(retention_days)
        deleted_tasks_count = len(deleted_files) if deleted_files else 0
        deleted_files_count = 0

        if deleted_files:
            for f_info in deleted_files:
                out_f = f_info.get("output_file")
                rep_f = f_info.get("report_html")

                if out_f:
                    p = Path(out_f)
                    if p.exists():
                        p.unlink(missing_ok=True)
                        deleted_files_count += 1
                        get_logger().info(f"[Cleanup] 物理删除过期输出文件: {p}")

                if rep_f:
                    p = Path(rep_f)
                    if p.exists():
                        p.unlink(missing_ok=True)
                        deleted_files_count += 1
                        get_logger().info(f"[Cleanup] 物理删除过期 HTML 报告: {p}")

        return {
            "status": "SUCCESS",
            "detail": f"任务保留 {retention_days} 天，删除任务 {deleted_tasks_count} 条，删除文件 {deleted_files_count} 个",
            "metrics": {"deleted_tasks": deleted_tasks_count, "deleted_files": deleted_files_count},
        }

    def _run_timer_log(self) -> dict:
        """清理过期的定时任务日志。"""
        return self._run_log_cleanup("timer_log", "timer_logs")

    def _run_login_log(self) -> dict:
        """清理过期的登录日志。"""
        return self._run_log_cleanup("login_log", "login_logs")

    def _run_operation_log(self) -> dict:
        """清理过期的操作日志。"""
        return self._run_log_cleanup("operation_log", "operation_logs")

    def _run_log_cleanup(self, op_name: str, table_name: str) -> dict:
        """通用的日志清理逻辑。"""
        from web.core.db import db

        # 白名单校验：仅允许操作已知的日志表，防止 table_name 字符串拼接引发 SQL 注入风险
        _ALLOWED_LOG_TABLES = {"login_logs", "operation_logs", "timer_logs"}
        if table_name not in _ALLOWED_LOG_TABLES:
            get_logger().error(f"[Cleanup] 非法日志表名被拒绝: {table_name!r}")
            return {"status": "FAILED", "detail": f"非法表名: {table_name}", "metrics": {}}

        cfg = self._get_op_config(op_name)
        if not cfg["enabled"]:
            return {"status": "SKIPPED", "detail": "未启用", "metrics": {}}

        retention_days = cfg.get("retention_days", 30)
        from datetime import datetime, timezone, timedelta
        now_cst = datetime.now(timezone.utc) + timedelta(hours=8)
        cutoff = (now_cst - timedelta(days=retention_days)).strftime("%Y-%m-%d %H:%M:%S")

        deleted_count = 0
        with db._get_connection() as conn:
            cursor = conn.execute(f"DELETE FROM {table_name} WHERE created_at <= ?", (cutoff,))
            deleted_count = cursor.rowcount
            conn.commit()

        get_logger().info(
            f"[DB] 清理 {table_name}：删除 {deleted_count} 条（截止时间: {cutoff}，保留 {retention_days} 天）"
        )

        return {
            "status": "SUCCESS",
            "detail": f"{table_name}：删除 {deleted_count} 条过期记录（保留 {retention_days} 天）",
            "metrics": {"deleted_tasks": 0, "deleted_files": 0},
        }

    def _run_activate_user(self) -> dict:
        """清理已过期的 Session 会话记录，防止 user_sessions 表长期积累膨胀。"""
        from web.core.db import db
        cfg = self._get_op_config("activate_user")
        if not cfg["enabled"]:
            return {"status": "SKIPPED", "detail": "未启用", "metrics": {}}

        deleted_sessions_count = db.delete_expired_sessions()
        if deleted_sessions_count > 0:
            get_logger().info(f"[Cleanup] 清理已过期的 Session 记录: {deleted_sessions_count} 条")

        return {
            "status": "SUCCESS",
            "detail": f"清理过期 Session 会话 {deleted_sessions_count} 条",
            "metrics": {"deleted_tasks": 0, "deleted_files": 0},
        }

    def _run_auto_unlock(self) -> dict:
        """自动解锁已过锁定期的用户和 IP（跳过永久锁定）。"""
        from web.core.db import db
        cfg = self._get_op_config("auto_unlock")
        if not cfg["enabled"]:
            return {"status": "SKIPPED", "detail": "未启用", "metrics": {}}

        from datetime import datetime, timezone, timedelta
        now_cst = datetime.now(timezone.utc) + timedelta(hours=8)
        now_str = now_cst.isoformat()
        unlocked_users = 0
        unlocked_ips = 0

        with db._get_connection() as conn:
            # 解锁已过期的账号临时封禁
            cursor = conn.execute(
                "DELETE FROM login_attempts WHERE lock_time IS NOT NULL AND lock_time <= ? AND is_permanent_lock = 0",
                (now_str,)
            )
            unlocked_users = cursor.rowcount

            # 解锁已过期的 IP 临时封禁
            cursor = conn.execute(
                "DELETE FROM ip_attempts WHERE lock_time IS NOT NULL AND lock_time <= ? AND is_permanent_lock = 0",
                (now_str,)
            )
            unlocked_ips = cursor.rowcount

            conn.commit()

        if unlocked_users > 0:
            get_logger().info(f"[Cleanup] 自动解锁 {unlocked_users} 个已过锁定期的账号")
        if unlocked_ips > 0:
            get_logger().info(f"[Cleanup] 自动解封 {unlocked_ips} 个已过封禁期的 IP")

        return {
            "status": "SUCCESS",
            "detail": f"自动解锁 {unlocked_users} 个账号、{unlocked_ips} 个 IP（锁定期已过）",
            "metrics": {"deleted_tasks": 0, "deleted_files": 0},
        }

    def run_retention_cleanup(self) -> None:
        """（向后兼容）运行所有已启用的清理操作。"""
        for op_name in self.OPERATIONS:
            self.run_single_operation(op_name)

    def _run_conversion(
        self,
        task_id: str,
        input_path: Path,
        output_path: Path,
        source_mode: str,
        target_mode: str,
        loop: asyncio.AbstractEventLoop
    ) -> None:
        """工作线程执行体：调用同步 convert。"""
        from web.core.db import db
        task, _ = db.get_task(task_id)
        if not task:
            return

        get_logger().info(f"[Worker] 任务 {task_id} 开始执行 SQL 转换流。输入: {input_path}")

        # 自动嗅探识别源方言支持
        if source_mode == "Auto-Sniff":
            from main import sniff_source_dialect
            try:
                sniffed_mode, confidence = sniff_source_dialect(input_path)
                source_mode = sniffed_mode
                get_logger().info(f"[Worker] 任务 {task_id} 自动识别源方言为: {source_mode} (置信度 {confidence:.1f}%)")
                task.source_mode = source_mode
                db.save_task(task)
            except Exception as e:
                get_logger().warning(f"[Worker] 任务 {task_id} 自动嗅探方言失败，回退默认为 mysql: {e}")
                source_mode = "mysql"
                task.source_mode = source_mode
                db.save_task(task)

        # 进度更新回调处理器

        def progress_callback(progress_data: dict[str, Any]):
            task.progress.update(progress_data)
            db.save_task(task)
            
            # 使用安全隔离路由推送给对应的 WS 队列
            message = {
                "type": "progress",
                "task_id": task_id,
                "status": progress_data.get("status", "PROCESSING"),
                "progress": task.progress
            }
            self._broadcast_to_recipients(task.username, message, loop)

        report = ConversionReport()
        report.progress_callback = progress_callback

        import time
        start_time = time.time()

        try:
            # 执行核心转换引擎 (I/O & CPU 密集型同步阻塞操作)
            convert(
                input_path=input_path,
                output_path=output_path,
                source_mode=source_mode,
                target_mode=target_mode,
                report=report,
                continue_on_error=True
            )

            # 写入 HTML 报告到磁盘
            report_file = None
            try:
                report_file = report.write_report(output_path, source_mode, target_mode)
            except Exception as e:
                get_logger().error(f"[Worker] 任务 {task_id} 写入 HTML 报告失败: {e}")

            from web.core.db_base import _now_cst
            elapsed = time.time() - start_time
            task.duration = int(round(elapsed * 1000))
            task.status = "SUCCESS"
            task.completed_at = _now_cst()
            task.output_file = str(output_path)
            task.report_html = str(report_file.absolute()) if report_file else None
            
            # 持久化更新
            db.save_task(task)
            get_logger().info(f"[Worker] 任务 {task_id} 转换成功完成！输出: {task.output_file}")

            # 精确路由推送成功消息
            message = {
                "type": "status_change",
                "task_id": task_id,
                "filename": task.filename,
                "source_mode": task.source_mode,
                "target_mode": task.target_mode,
                "status": "SUCCESS",
                "progress": task.progress,
                "output_file": task.output_file,
                "report_html": task.report_html
            }
            self._broadcast_to_recipients(task.username, message, loop)

        except Exception as e:
            from web.core.db_base import _now_cst
            elapsed = time.time() - start_time
            task.duration = int(round(elapsed * 1000))
            task.status = "FAILED"
            task.completed_at = _now_cst()
            task.error = str(e)
            
            # 持久化更新
            db.save_task(task)
            get_logger().error(f"[Worker] 任务 {task_id} 执行遇到异常崩溃: {e}", exc_info=True)
            
            # 精确路由推送失败消息
            message = {
                "type": "status_change",
                "task_id": task_id,
                "filename": task.filename,
                "source_mode": task.source_mode,
                "target_mode": task.target_mode,
                "status": "FAILED",
                "progress": task.progress,
                "error": task.error
            }
            self._broadcast_to_recipients(task.username, message, loop)


# 全局单例调度器
scheduler = TaskScheduler()
