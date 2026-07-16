from __future__ import annotations
import asyncio
import collections
import datetime
import hashlib
import os
import re
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from web.core.scheduler import scheduler, TaskInfo
from web.core.db import db
from utils.config_manager import config
from core.logger import get_logger
from web.api.auth import verify_auth

router = APIRouter()

# 全局资源历史记录（用于仪表盘折线图），使用 deque 保证内存安全且自动限制大小
_resource_history: collections.deque = collections.deque(maxlen=60)
_MAX_HISTORY_POINTS = 60  # 已由 deque(maxlen=60) 接管，保留字段以兼容旧引用

# 全局数据保存目录
DATA_DIR = Path(__file__).parent.parent.parent.resolve() / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 上传临时目录
TEMP_DIR = Path(tempfile.gettempdir()) / "sql_convert_temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def calculate_file_hash(file_path: Path) -> str:
    """流式计算文件的 SHA-256 哈希值，用于指纹识别去重。"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


# ──────────────────────────────────────────────────────────
# 引擎内置方言友好显示 Label 映射表
# ──────────────────────────────────────────────────────────
DIALECT_LABELS = {
    "mysql": "MySQL",
    "oracle": "Oracle",
    "pgsql": "PostgreSQL (pgsql)",
    "sqlite": "SQLite",
    "sqlserver": "SQL Server (MSSQL)",
    "kingbase": "Kingbase (人大金仓)"
}


@router.get("/dialects")
def list_dialects():
    """获取当前引擎注册支持的全部 SQL 方言列表，输入源与输出格式自适应动态拉取。"""
    try:
        from converter.registry import get_supported_dialects
        raw_dialects = get_supported_dialects()
        
        result = []
        for name in raw_dialects:
            val = name.lower()
            label = DIALECT_LABELS.get(val, name.capitalize())
            result.append({
                "value": val,
                "label": label
            })
        return result
    except Exception as e:
        get_logger().error(f"[API] 获取支持方言列表异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks(
    request: Request,
    page: int = 1,
    page_size: int = 10,
    filename: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: str = Depends(verify_auth)
):
    """分页获取历史转换任务（支持文件名搜索、状态和时间范围筛选）。"""
    result = []
    tasks_list, total = db.list_tasks_paginated(page, page_size, filename, status, date_from, date_to)
    for task, is_verified in tasks_list:
        if current_user != "admin" and task.username != current_user:
            continue
        task_dict = {
            "task_id": task.task_id,
            "filename": task.filename,
            "source_mode": task.source_mode,
            "target_mode": task.target_mode,
            "status": task.status,
            "progress": task.progress,
            "error": task.error,
            "is_verified": is_verified,
            "file_hash": getattr(task, "file_hash", ""),
            "convert_type": getattr(task, "convert_type", "online"),
            "duration": getattr(task, "duration", 0.0),
            "created_at": getattr(task, "created_at", None),
            "updated_at": getattr(task, "updated_at", None),
            "completed_at": getattr(task, "completed_at", None)
        }
        result.append(task_dict)
    return {"data": result, "total": total, "page": page, "page_size": page_size}


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, current_user: str = Depends(verify_auth)):
    """获取指定任务的详情（需要鉴权，隔离非拥有者防越权）。"""
    task, is_verified = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if current_user != "admin" and task.username != current_user:
        raise HTTPException(status_code=403, detail="拒绝访问：您无权查看此任务。")

    return {
        "task_id": task.task_id,
        "filename": task.filename,
        "source_mode": task.source_mode,
        "target_mode": task.target_mode,
        "status": task.status,
        "progress": task.progress,
        "error": task.error,
        "is_verified": is_verified,
        "file_hash": getattr(task, "file_hash", ""),
        "convert_type": getattr(task, "convert_type", "online"),
        "duration": getattr(task, "duration", 0.0),
        "created_at": getattr(task, "created_at", None),
        "updated_at": getattr(task, "updated_at", None),
        "completed_at": getattr(task, "completed_at", None)
    }


def validate_sql_file(file_path: Path) -> str | None:
    """校验 SQL 文件是否包含 CREATE TABLE 定义，返回 None 表示通过，否则返回错误消息。"""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")[:16384]
    except Exception:
        return "无法读取文件内容。"

    if not content.strip():
        return "文件内容为空。"

    # 检查是否包含 SQL 关键字
    if not re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)\b', content, re.IGNORECASE):
        return "文件内容不是有效的 SQL 语句。"

    # 提取 CREATE TABLE 中定义的表名
    created_tables = set()
    for m in re.finditer(
        r'CREATE\s+(?:TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`?\w+`?\.)?`?(\w+)`?',
        content, re.IGNORECASE
    ):
        created_tables.add(m.group(1).lower())

    # 有 CREATE TABLE 即视为有表结构
    if created_tables:
        return None

    has_dml = bool(re.search(r'\bINSERT\s+(?:IGNORE\s+)?INTO\b|\bUPDATE\b|\bDELETE\s+FROM\b', content, re.IGNORECASE))
    has_other_ddl = bool(re.search(r'\bALTER\s+TABLE\b|\bCREATE\s+(?:INDEX|VIEW|SEQUENCE|SCHEMA|DATABASE)\b', content, re.IGNORECASE))

    if has_dml and not has_other_ddl:
        return "转换需要表结构定义（CREATE TABLE），仅有 INSERT/UPDATE/DELETE 语句无法完成转换。"
    if not has_dml and not has_other_ddl and not re.search(r'\bSELECT\b', content, re.IGNORECASE):
        return "未检测到 CREATE TABLE 等表结构定义语句，无法进行方言转换。"

    return None


@router.post("/convert")
async def start_conversion(
    request: Request,
    background_tasks: BackgroundTasks,
    source_mode: Optional[str] = Form(None),
    target_mode: str = Form(...),
    file: UploadFile = File(...),
    current_user: str = Depends(verify_auth)
):
    """触发 SQL 转换（需要鉴权，仅接受文件上传）。"""
    client_ip = request.client.host

    input_file_path: Path

    max_size_mb = config.get("web.max_upload_size_mb", 500)
    filename = file.filename or "upload.sql"
    temp_file_path = TEMP_DIR / f"{os.urandom(8).hex()}_{filename}"

    try:
        with open(temp_file_path, "wb") as buffer:
            size = 0
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > max_size_mb * 1024 * 1024:
                    temp_file_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail=f"文件体积超出限制 ({max_size_mb} MB)")
                buffer.write(chunk)
    except Exception as e:
        if not isinstance(e, HTTPException):
            temp_file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"文件上传失败: {e}")
        raise e

    file_hash = calculate_file_hash(temp_file_path)
    input_file_path = UPLOAD_DIR / f"{file_hash}.sql"
    if input_file_path.exists():
        temp_file_path.unlink(missing_ok=True)
        get_logger().info(f"[API] 检测到完全相同的物理文件上传 (Hash: {file_hash})，复用磁盘存储")
    else:
        shutil.move(str(temp_file_path), str(input_file_path))


    src_dialect_mode = source_mode or "Auto-Sniff"
    get_logger().info(f"[API] 收到转换请求. 源: {src_dialect_mode}, 目标: {target_mode}, 哈希: {file_hash}")

    # SQL 内容校验：检查是否包含表结构定义
    sql_check = validate_sql_file(input_file_path)
    if sql_check:
        get_logger().warning(f"[API] SQL 校验未通过: {sql_check}")
        raise HTTPException(status_code=400, detail=sql_check)

    # 极速缓存检测
    cached_task = None
    for old_task, is_verified in db.list_tasks():
        if (
            getattr(old_task, "file_hash", "") == file_hash
            and old_task.source_mode == src_dialect_mode
            and old_task.target_mode == target_mode
            and old_task.status == "SUCCESS"
            and is_verified
        ):
            if (
                old_task.output_file and Path(old_task.output_file).exists()
                and old_task.report_html and Path(old_task.report_html).exists()
            ):
                cached_task = old_task
                break

    if cached_task:
        get_logger().info(f"[API] 命中转换缓存！复用任务 {cached_task.task_id} 的输出成果")
        task_id = scheduler.create_task(filename, src_dialect_mode, target_mode, file_hash, current_user, convert_type="online" if filename == "online_query.sql" else "upload")
        task, _ = db.get_task(task_id)
        task.status = "SUCCESS"
        task.output_file = cached_task.output_file
        task.report_html = cached_task.report_html
        task.progress = cached_task.progress.copy()
        db.save_task(task)
        
        db.write_operation_log(current_user, client_ip, "CONVERT", f"filename={filename}, target={target_mode}, cached=true, task_id={task_id}")
        scheduler._broadcast(task)
        return {"task_id": task_id, "status": "SUCCESS", "cached": True}

    task_id = scheduler.create_task(filename, src_dialect_mode, target_mode, file_hash, current_user, convert_type="online" if filename == "online_query.sql" else "upload")

    output_dir = input_file_path.parent
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y%m%d_%H%M%S")
    stem = input_file_path.stem
    ext = ".db" if target_mode == "sqlite" else ".sql"
    output_path = output_dir / f"{stem}_{target_mode}_{ts}{ext}"

    loop = asyncio.get_running_loop()
    scheduler.submit_task(task_id, input_file_path, output_path, loop)

    db.write_operation_log(current_user, client_ip, "CONVERT", f"filename={filename}, target={target_mode}, cached=false, task_id={task_id}")
    get_logger().info(f"[API] 任务已成功提交线程池，Task ID: {task_id}")
    return {"task_id": task_id, "status": "PENDING", "cached": False}


@router.get("/download/{task_id}")
async def download_output(request: Request, task_id: str, current_user: str = Depends(verify_auth)):
    """下载输出文件（需要鉴权，隔离非拥有者防越权）。"""
    client_ip = request.client.host
    task, is_verified = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if current_user != "admin" and task.username != current_user:
        raise HTTPException(status_code=403, detail="拒绝访问：您无权下载此任务文件。")

    if not is_verified:
        get_logger().warning(f"[Security] 拦截了对篡改任务 {task_id} 的文件下载！")
        raise HTTPException(status_code=403, detail="数据完整性校验失败，该记录已被外部非法篡改！")

    if task.status != "SUCCESS" or not task.output_file:
        raise HTTPException(status_code=404, detail="转换尚未成功或输出文件丢失。")
    
    p = Path(task.output_file)
    if not p.exists():
        raise HTTPException(status_code=404, detail="输出文件物理不存在。")

    db.write_operation_log(current_user, client_ip, "DOWNLOAD", f"task_id={task_id}, file={p.name}")
    return FileResponse(
        path=p,
        filename=p.name,
        media_type="application/octet-stream"
    )


@router.get("/report/{task_id}", response_class=HTMLResponse)
async def view_report(request: Request, task_id: str, current_user: str = Depends(verify_auth)):
    """预览 HTML 评估报告（需要鉴权，隔离非拥有者防越权）。"""
    client_ip = request.client.host
    task, is_verified = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if current_user != "admin" and task.username != current_user:
        raise HTTPException(status_code=403, detail="拒绝访问：您无权查看此任务报告。")

    if not is_verified:
        get_logger().warning(f"[Security] 拦截了对篡改任务 {task_id} 的报告查看！")
        raise HTTPException(status_code=403, detail="数据完整性校验失败，该报告已被外部非法篡改！")

    if task.status != "SUCCESS" or not task.report_html:
        raise HTTPException(status_code=404, detail="报告尚未生成或生成失败。")
    
    p = Path(task.report_html)
    if not p.exists():
        raise HTTPException(status_code=404, detail="报告文件已丢失。")

    db.write_operation_log(current_user, client_ip, "VIEW_REPORT", f"task_id={task_id}")
    return HTMLResponse(content=p.read_text(encoding="utf-8"))


@router.get("/stats")
async def get_stats(current_user: str = Depends(verify_auth)):
    """获取资源监控指标与任务转换统计数据（需要鉴权，普通用户只统计自己，admin统计全部）。"""
    tasks_list = db.list_tasks()
    if current_user != "admin":
        tasks_list = [(t, v) for t, v in tasks_list if t.username == current_user]
        
    total_tasks = len(tasks_list)
    success_tasks = sum(1 for t, _ in tasks_list if t.status == "SUCCESS")
    failed_tasks = sum(1 for t, _ in tasks_list if t.status == "FAILED")
    
    dialect_stats = {}
    total_warnings = 0
    total_failures_skipped = 0
    for task, _ in tasks_list:
        target = task.target_mode
        dialect_stats[target] = dialect_stats.get(target, 0) + 1
        total_warnings += task.progress.get("warning_count", 0)
        total_failures_skipped += task.progress.get("failure_count", 0)
        
    import platform
    import shutil

    # ── 磁盘使用率（跨平台）──
    try:
        total, used, _free = shutil.disk_usage(".")
        disk_pct = round((used / total) * 100, 1)
    except Exception:
        disk_pct = 0.0

    mem_pct = 0.0
    cpu_pct = 0.0

    system = platform.system().lower()
    if "windows" in system:
        try:
            import ctypes

            # ── Windows 内存使用率 ──
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            mem_pct = float(stat.dwMemoryLoad)

            # ── Windows CPU 使用率（GetSystemTimes 两次采样差值）──
            FILETIME = ctypes.c_uint64
            idle1, kernel1, user1 = FILETIME(), FILETIME(), FILETIME()
            ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle1), ctypes.byref(kernel1), ctypes.byref(user1)
            )
            import time as _time
            _time.sleep(0.1)
            idle2, kernel2, user2 = FILETIME(), FILETIME(), FILETIME()
            ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle2), ctypes.byref(kernel2), ctypes.byref(user2)
            )
            d_idle   = idle2.value   - idle1.value
            d_kernel = kernel2.value - kernel1.value
            d_user   = user2.value   - user1.value
            d_total  = d_kernel + d_user
            if d_total > 0:
                cpu_pct = round((1.0 - d_idle / d_total) * 100, 1)
        except Exception:
            pass
    else:
        # ── Linux / macOS CPU 使用率（/proc/stat 两次采样差值）──
        try:
            import time as _time

            def _read_proc_stat():
                with open("/proc/stat", "r") as f:
                    line = f.readline()
                parts = line.split()
                vals = [int(x) for x in parts[1:]]
                total_t = sum(vals)
                idle_t  = vals[3] + (vals[4] if len(vals) > 4 else 0)
                return total_t, idle_t

            t1, i1 = _read_proc_stat()
            _time.sleep(0.1)
            t2, i2 = _read_proc_stat()
            d_total = t2 - t1
            d_idle  = i2 - i1
            if d_total > 0:
                cpu_pct = round((1.0 - d_idle / d_total) * 100, 1)

            # Linux 内存使用率（/proc/meminfo）
            mem_info = {}
            with open("/proc/meminfo", "r") as f:
                for l in f:
                    k, v = l.split(":", 1)
                    mem_info[k.strip()] = int(v.split()[0])
            mem_total     = mem_info.get("MemTotal", 0)
            mem_available = mem_info.get("MemAvailable", 0)
            if mem_total > 0:
                mem_pct = round((1.0 - mem_available / mem_total) * 100, 1)
        except Exception:
            pass

    # ── 追加到 deque 历史（deque(maxlen=60) 自动淘汰最旧条目，无需手动 trim）──
    now_ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    _resource_history.append({
        "time": now_ts,
        "cpu": cpu_pct,
        "memory": mem_pct,
        "disk": disk_pct
    })

    return {
        "tasks": {
            "total": total_tasks,
            "success": success_tasks,
            "failed": failed_tasks,
            "warnings": total_warnings,
            "failures_skipped": total_failures_skipped,
            "dialect_distribution": dialect_stats
        },
        "resources": {
            "cpu": cpu_pct,
            "memory": mem_pct,
            "disk": disk_pct
        }
    }


@router.get("/stats/history")
async def get_stats_history(current_user: str = Depends(verify_auth)):
    """获取资源历史记录（用于仪表盘折线图）。"""
    return {"history": list(_resource_history)}


@router.get("/ws-config")
async def get_ws_config(current_user: str = Depends(verify_auth)):
    """返回 WebSocket 前端配置（重连策略等）。"""
    return {
        "max_reconnect_attempts": config.get("web.websocket.max_reconnect_attempts", 5)
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 接口，提供实时进度流式广播订阅（内部防越权握手）。"""
    # 必须首先 accept 握手连接，避免 ASGI 容器因未完成握手便终止而输出 ERROR 日志，
    # 并且能为前端提供准确的 close code（如 4001, 4003）以控制其断开后不再盲目重连。
    await websocket.accept()
    
    client_ip = websocket.client.host
    token = None
    authenticated_user = None
    queue = None

    # 1. 验证 IP 黑名单
    fail_count_ip, lock_time_ip, is_perm_lock_ip = db.get_ip_attempts(client_ip)
    if is_perm_lock_ip:
        await websocket.close(code=4003)
        return
    if lock_time_ip:
        lock_time = datetime.datetime.fromisoformat(lock_time_ip)
        if lock_time.tzinfo is None:
            lock_time = lock_time.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
        if datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))) < lock_time:
            await websocket.close(code=4003)
            return

    # 2. 验证 IP 白名单
    if config.get("web.ip_whitelist.enabled", False):
        if not db.is_ip_whitelisted(client_ip):
            await websocket.close(code=4003)
            return

    # 3. 验证登录 Token (支持 Query param 中显式传入的 token，降级使用 Cookie)
    token = websocket.query_params.get("token") or websocket.cookies.get("session_token")
    if token:
        authenticated_user = db.get_username_by_session(token)

    if config.get("web.auth.enabled", True):
        if not authenticated_user:
            await websocket.close(code=4001)
            return
    else:
        # 当禁用认证时，默认指定为 anonymous 用户，防止局部变量未定义异常
        authenticated_user = authenticated_user or "anonymous"
    get_logger().info(f"[WS] 客户端 WebSocket 通道已建立 (用户: {authenticated_user})。")

    queue = asyncio.Queue()
    scheduler.register_ws_queue(authenticated_user, queue)

    try:
        initial_tasks = []
        # 非 admin 用户只推送自己拥有的任务，防止 WS 初始化快照泄露他人数据
        for task, is_verified in db.list_tasks():
            if authenticated_user != "admin" and task.username != authenticated_user:
                continue
            initial_tasks.append({
                "task_id": task.task_id,
                "filename": task.filename,
                "source_mode": task.source_mode,
                "target_mode": task.target_mode,
                "status": task.status,
                "progress": task.progress,
                "error": task.error,
                "is_verified": is_verified
            })
            
        initial_msg = {
            "type": "init",
            "tasks": initial_tasks
        }
        await websocket.send_json(initial_msg)

        while True:
            try:
                # 设定 30 秒等待超时。既能防止 Nginx 60秒默认读写超时强断连接，又能在闲置无任务时进行链路探测
                msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                if msg is None:  # 服务关闭或收到显式断开信号时退出
                    break
                await websocket.send_json(msg)
                queue.task_done()
            except asyncio.TimeoutError:
                # 超时说明当前无进行中的任务广播，主动发送 ping 以检测客户端是否存活（防止静默断网造成残留协程内存泄漏）
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    # 发送失败表示底层 TCP 已断开，向上抛出以触发 finally 回收
                    raise
    except WebSocketDisconnect:
        get_logger().info(f"[WS] 客户端 WebSocket 主动断开连接 (用户: {authenticated_user})。")
    except (ConnectionResetError, RuntimeError, OSError) as e:
        # 捕捉常规网络重置与 ASGI 断开异常，净化日志，防止打印大段崩溃堆栈
        get_logger().info(f"[WS] 客户端 WebSocket 连接重置或异常关闭 (用户: {authenticated_user})。")
    except asyncio.CancelledError:
        # 服务关闭时 asyncio 取消所有任务，静默回收连接资源
        get_logger().info(f"[WS] 服务关闭，WebSocket 连接已回收 (用户: {authenticated_user})。")
    finally:
        if authenticated_user and queue:
            # 精确传入当前特定的 Queue 实例，避免多标签页退出时错误注销其他标签页的推送队列
            scheduler.unregister_ws_queue(authenticated_user, queue)
