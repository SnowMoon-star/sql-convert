"""Web UI 服务入口 — 整合 API 路由、静态资源托管，加载 YAML 配置启动 uvicorn。"""
from __future__ import annotations
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from web.api.routes import router
from utils.config_manager import config
from core.logger import setup_logger

from web.core.security import APISecurityMiddleware

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    from web.core.scheduler import scheduler
    from core.logger import get_logger

    async def cleanup_loop():
        from croniter import croniter
        from datetime import datetime, timezone, timedelta
        EAST8 = timezone(timedelta(hours=8))

        # 收集所有已启用的操作及其 cron 表达式
        enabled_ops = {}
        for op_name in scheduler.OPERATIONS:
            cfg = scheduler._get_op_config(op_name)
            if cfg.get("enabled", True):
                enabled_ops[op_name] = cfg.get("cron", "0 3 * * *")

        if not enabled_ops:
            get_logger().info("[Server] 后台定时清理服务：所有操作均未启用")
            return

        # 初始化每个操作的下次执行时间
        now = datetime.now(EAST8)
        next_runs = {}
        for op_name, cron_expr in enabled_ops.items():
            cron = croniter(cron_expr, now)
            next_runs[op_name] = cron.get_next(datetime)

        get_logger().info(
            f"[Server] 后台定时清理服务启动，{len(enabled_ops)} 个操作已启用，检查间隔 60s"
        )

        while True:
            try:
                now = datetime.now(EAST8)
                for op_name in list(next_runs.keys()):
                    if now >= next_runs[op_name]:
                        get_logger().info(
                            f"[Server] cron 触发操作: {op_name} (scheduled at {next_runs[op_name].strftime('%H:%M')})"
                        )
                        scheduler.run_single_operation(op_name)
                        cron = croniter(enabled_ops[op_name], now)
                        next_runs[op_name] = cron.get_next(datetime)
            except Exception as e:
                get_logger().error(f"[Server] 后台定时清理循环运行异常: {e}")
            await asyncio.sleep(60)

    # 启动后台定时任务
    cleanup_task = asyncio.create_task(cleanup_loop())
    
    yield
    
    # 优雅退出：取消清理协程
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="sql_convert Web UI",
    description="多方言 SQL 流式转换器可视化 Web 面板",
    version="1.0.0",
    lifespan=lifespan
)

# 挂载接口加密与防篡改国密安全中间件
app.add_middleware(APISecurityMiddleware)

# 允许跨域（本地调试开发时常用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 API 路由
app.include_router(router)

# 挂载前端静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)

# 确保 index.html 存在，作为 SPA 的兜底
index_html = static_dir / "index.html"
if not index_html.exists():
    # 后面我们会生成美观的单页 index.html
    pass

# 静态资源挂载
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


def run():
    """启动 Web 服务。"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="sql_convert Web Server")
    parser.add_argument("--unlock-user", type=str, help="人工解锁被锁定的账号")
    parser.add_argument("--unlock-ip", type=str, help="人工解锁被封禁的 IP 地址")
    args, unknown = parser.parse_known_args()
    
    # 处理解锁参数
    if args.unlock_user or args.unlock_ip:
        from web.core.db import db
        if args.unlock_user:
            db.unlock_user(args.unlock_user)
            print(f"[CLI] 安全指令：已手动解锁账号: {args.unlock_user}")
        if args.unlock_ip:
            db.unlock_ip(args.unlock_ip)
            print(f"[CLI] 安全指令：已手动解锁客户端 IP: {args.unlock_ip}")
        sys.exit(0)

    # ── 启动环境校验（仅执行一次，任意项失败则终止进程）──
    from web.core.startup_check import run_all_checks
    run_all_checks()

    setup_logger(
        verbose=config.get("web.verbose", True),
        debug=config.get("web.debug", False),
        trace=config.get("web.trace", False)
    )

    host = config.get("web.host", "127.0.0.1")
    port = config.get("web.port", 8000)

    print(f"==================================================")
    print(f"  sql_convert Web UI 服务启动中...")
    print(f"  请在浏览器访问: http://{host}:{port}/")
    print(f"==================================================")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
