from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from web.core.db import db
from web.api.auth import verify_admin

router = APIRouter()


class KickRequest(BaseModel):
    """踢出会话请求体。"""
    session_token: str


@router.get("/active-users")
async def get_active_users(
    request: Request,
    page: int = 1,
    size: int = 10,
    username: str = None,
    ip: str = None,
    is_admin: int = None,
    current_user: str = Depends(verify_admin)
):
    """分页获取活跃用户会话列表（仅限管理员）。"""
    items, total = db.list_active_sessions(page=page, size=size, username=username, ip=ip, is_admin=is_admin)
    return {
        "total": total,
        "items": items
    }


@router.post("/active-users/kick")
async def kick_user(
    request: Request,
    body: KickRequest,
    current_user: str = Depends(verify_admin)
):
    """踢出指定活跃用户会话（仅限管理员，超管可以踢任何人，管理员不能踢管理员且不能踢自己）。"""
    session_token = body.session_token.strip()
    target_username = db.get_username_by_session(session_token)
    if not target_username:
        raise HTTPException(status_code=404, detail="会话不存在或已过期。")

    # 1. 禁止踢自己
    if target_username == current_user:
        raise HTTPException(status_code=400, detail="禁止强制下线您自己的账号。")

    # 2. 角色越权限制：超管（admin）可以踢所有人，普通管理员（is_admin=1）不能踢管理员（is_admin=1）
    if current_user != "admin":
        target_user_info = db.get_user(target_username)
        if target_user_info and target_user_info[2]:  # is_admin == 1
            raise HTTPException(status_code=403, detail="权限不足：普通管理员不能强制下线其他管理员。")

    db.delete_session(session_token)
    
    client_ip = request.client.host
    db.write_operation_log(
        current_user,
        client_ip,
        "KICK_USER",
        f"Kicked out user '{target_username}' session (token: {session_token[:12]}...)"
    )
    return {"status": "success", "message": f"用户 '{target_username}' 的会话已被强制下线。"}
