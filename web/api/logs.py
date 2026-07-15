from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Request

from web.core.db import db
from web.api.auth import verify_admin

router = APIRouter()


# ──────────────────────────────────────────────────────────
# 审计日志查询接口（仅管理员）
# ──────────────────────────────────────────────────────────
@router.get("/logs/login")
async def query_login_logs(request: Request,
                           page: int = 1, page_size: int = 10,
                           username: Optional[str] = None,
                           status: Optional[str] = None,
                           date_from: Optional[str] = None,
                           date_to: Optional[str] = None,
                           current_user: str = Depends(verify_admin)):
    """查询登录审计日志（仅管理员，支持分页与筛选）。"""
    client_ip = request.client.host
    db.write_operation_log(current_user, client_ip, "VIEW_LOGS", "Viewed login logs")
    rows, total = db.query_login_logs(page, page_size, username, status, date_from, date_to)
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


@router.get("/logs/operation")
async def query_operation_logs(page: int = 1, page_size: int = 10,
                               username: Optional[str] = None,
                               action: Optional[str] = None,
                               status: Optional[str] = None,
                               date_from: Optional[str] = None,
                               date_to: Optional[str] = None,
                               _current_user: str = Depends(verify_admin)):
    """查询操作审计日志（仅管理员，支持分页与筛选）。"""
    rows, total = db.query_operation_logs(page, page_size, username, action, status, date_from, date_to)
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


@router.get("/logs/timer")
async def query_timer_logs(page: int = 1, page_size: int = 10,
                           action: Optional[str] = None,
                           status: Optional[str] = None,
                           date_from: Optional[str] = None,
                           date_to: Optional[str] = None,
                           _current_user: str = Depends(verify_admin)):
    """查询定时任务日志（仅管理员，支持分页与筛选）。"""
    rows, total = db.query_timer_logs(page, page_size, action=action, status=status, date_from=date_from, date_to=date_to)
    return {"data": rows, "total": total, "page": page, "page_size": page_size}
