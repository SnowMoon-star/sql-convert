from __future__ import annotations
import datetime
import ipaddress
from fastapi import APIRouter, Form, HTTPException, Depends, Request
from pydantic import BaseModel

from web.core.db import db
from utils.config_manager import config
from web.api.auth import verify_admin


def _validate_ip(ip: str) -> str:
    """校验字符串是否为合法的 IPv4 或 IPv6 地址，非法则抛出 HTTP 400。"""
    ip = ip.strip()
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"非法的 IP 地址格式: {ip}")
    return ip

router = APIRouter()


# ──────────────────────────────────────────────────────────
# IP 白名单管理接口（仅管理员可访问，普通用户无权查看或修改）
# ──────────────────────────────────────────────────────────
@router.get("/whitelist")
async def get_whitelist_list(current_user: str = Depends(verify_admin)):
    """获取当前白名单列表及运行开关状态（仅管理员）。"""
    return {
        "enabled": config.get("web.ip_whitelist.enabled", False),
        "whitelist": db.get_whitelist()
    }


@router.post("/whitelist")
async def add_whitelist_ip(request: Request, ip: str = Form(...), current_user: str = Depends(verify_admin)):
    """添加 IP 到数据库白名单（仅管理员）。"""
    validated_ip = _validate_ip(ip)
    client_ip = request.client.host
    db.add_to_whitelist(validated_ip)
    db.write_operation_log(current_user, client_ip, "ADD_WHITELIST", f"Added IP: {validated_ip}")
    return {"status": "success"}


@router.delete("/whitelist/{ip}")
async def delete_whitelist_ip(request: Request, ip: str, current_user: str = Depends(verify_admin)):
    """从数据库白名单中删除指定 IP（仅管理员）。"""
    validated_ip = _validate_ip(ip)
    client_ip = request.client.host
    db.remove_from_whitelist(validated_ip)
    db.write_operation_log(current_user, client_ip, "DELETE_WHITELIST", f"Deleted IP: {validated_ip}")
    return {"status": "success"}


# ──────────────────────────────────────────────────────────
# 系统设置：白名单、用户锁定、IP锁定 管理接口的数据模型
# ──────────────────────────────────────────────────────────
class WhitelistUpdateRequest(BaseModel):
    old_ip: str
    new_ip: str

class WhitelistCreateRequest(BaseModel):
    ip: str

class UserLockoutUpdateRequest(BaseModel):
    fail_count: int
    lock_count: int
    is_permanent_lock: int
    lock_time: str | None = None

class UserLockoutCreateRequest(BaseModel):
    username: str
    fail_count: int = 0
    lock_count: int = 0
    is_permanent_lock: int = 0
    lock_time: str | None = None

class IPLockoutUpdateRequest(BaseModel):
    fail_count: int
    is_permanent_lock: int
    lock_time: str | None = None

class IPLockoutCreateRequest(BaseModel):
    ip: str
    fail_count: int = 0
    is_permanent_lock: int = 0
    lock_time: str | None = None


# ──────────────────────────────────────────────────────────
# 系统设置：白名单、用户锁定、IP锁定 管理路由（仅管理员）
# ──────────────────────────────────────────────────────────
@router.get("/settings/whitelist")
async def settings_get_whitelist(
    ip: str | None = None,
    current_user: str = Depends(verify_admin)
):
    """获取白名单列表（仅管理员）。"""
    return {
        "enabled": config.get("web.ip_whitelist.enabled", False),
        "whitelist": db.list_whitelist(ip_query=ip)
    }

@router.post("/settings/whitelist")
async def settings_add_whitelist(
    body: WhitelistCreateRequest,
    current_user: str = Depends(verify_admin)
):
    """添加 IP 到白名单（仅管理员）。"""
    if db.is_ip_whitelisted(body.ip):
        raise HTTPException(status_code=400, detail="该 IP 已存在于白名单中。")
    db.add_to_whitelist(body.ip)
    return {"status": "success"}

@router.put("/settings/whitelist")
async def settings_update_whitelist(
    body: WhitelistUpdateRequest,
    current_user: str = Depends(verify_admin)
):
    """更新白名单 IP（仅管理员）。"""
    success = db.update_whitelist_ip(body.old_ip, body.new_ip)
    if not success:
        raise HTTPException(status_code=400, detail="新 IP 已存在或更新失败。")
    return {"status": "success"}

@router.delete("/settings/whitelist/{ip}")
async def settings_delete_whitelist(
    ip: str,
    current_user: str = Depends(verify_admin)
):
    """从白名单中删除 IP（仅管理员）。"""
    db.remove_from_whitelist(ip)
    return {"status": "success"}


@router.get("/settings/user-lockouts")
async def settings_get_user_lockouts(
    username: str | None = None,
    is_locked: int | None = None,
    current_user: str = Depends(verify_admin)
):
    """获取用户账号锁定监控记录（仅管理员）。"""
    return db.list_login_attempts(username_query=username, is_locked=is_locked)

@router.post("/settings/user-lockouts")
async def settings_create_user_lockout(
    body: UserLockoutCreateRequest,
    current_user: str = Depends(verify_admin)
):
    """手动创建用户锁定监控记录（仅管理员）。"""
    if not db.get_user(body.username):
        raise HTTPException(status_code=404, detail="该用户名在系统中不存在，无法添加监控记录。")
    
    db_lock_time = None
    if body.lock_time:
        try:
            EAST8 = datetime.timezone(datetime.timedelta(hours=8))
            expire_dt = datetime.datetime.strptime(body.lock_time.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=EAST8)
            db_lock_time = expire_dt.isoformat()
        except ValueError:
            raise HTTPException(status_code=400, detail="时间格式非法，请使用 YYYY-MM-DD HH:MM:SS。")

    success = db.create_login_attempt(
        username=body.username,
        fail_count=body.fail_count,
        lock_time=db_lock_time,
        lock_count=body.lock_count,
        is_permanent_lock=body.is_permanent_lock
    )
    if not success:
        raise HTTPException(status_code=400, detail="该用户的监控记录已存在，请直接编辑。")
    return {"status": "success"}

@router.put("/settings/user-lockouts/{username}")
async def settings_update_user_lockout(
    username: str,
    body: UserLockoutUpdateRequest,
    current_user: str = Depends(verify_admin)
):
    """更新用户锁定监控记录属性（仅管理员）。"""
    db_lock_time = None
    if body.lock_time:
        try:
            EAST8 = datetime.timezone(datetime.timedelta(hours=8))
            expire_dt = datetime.datetime.strptime(body.lock_time.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=EAST8)
            db_lock_time = expire_dt.isoformat()
        except ValueError:
            raise HTTPException(status_code=400, detail="时间格式非法，请使用 YYYY-MM-DD HH:MM:SS。")

    success = db.update_login_attempt(
        username=username,
        fail_count=body.fail_count,
        lock_time=db_lock_time,
        lock_count=body.lock_count,
        is_permanent_lock=body.is_permanent_lock
    )
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在。")
    return {"status": "success"}

@router.delete("/settings/user-lockouts/{username}")
async def settings_delete_user_lockout(
    username: str,
    current_user: str = Depends(verify_admin)
):
    """解封并清除用户锁定记录（仅管理员）。"""
    success = db.delete_login_attempt(username)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在。")
    return {"status": "success"}


@router.get("/settings/ip-lockouts")
async def settings_get_ip_lockouts(
    ip: str | None = None,
    is_locked: int | None = None,
    current_user: str = Depends(verify_admin)
):
    """获取 IP 锁定监控记录列表（仅管理员）。"""
    return db.list_ip_attempts(ip_query=ip, is_locked=is_locked)

@router.post("/settings/ip-lockouts")
async def settings_create_ip_lockout(
    body: IPLockoutCreateRequest,
    current_user: str = Depends(verify_admin)
):
    """手动创建 IP 锁定监控记录（仅管理员）。"""
    db_lock_time = None
    if body.lock_time:
        try:
            EAST8 = datetime.timezone(datetime.timedelta(hours=8))
            expire_dt = datetime.datetime.strptime(body.lock_time.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=EAST8)
            db_lock_time = expire_dt.isoformat()
        except ValueError:
            raise HTTPException(status_code=400, detail="时间格式非法，请使用 YYYY-MM-DD HH:MM:SS。")

    db.update_ip_attempts(
        ip=body.ip,
        fail_count=body.fail_count,
        lock_time=db_lock_time,
        is_permanent_lock=body.is_permanent_lock
    )
    return {"status": "success"}

@router.put("/settings/ip-lockouts/{ip}")
async def settings_update_ip_lockout(
    ip: str,
    body: IPLockoutUpdateRequest,
    current_user: str = Depends(verify_admin)
):
    """更新 IP 锁定记录属性（仅管理员）。"""
    db_lock_time = None
    if body.lock_time:
        try:
            EAST8 = datetime.timezone(datetime.timedelta(hours=8))
            expire_dt = datetime.datetime.strptime(body.lock_time.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=EAST8)
            db_lock_time = expire_dt.isoformat()
        except ValueError:
            raise HTTPException(status_code=400, detail="时间格式非法，请使用 YYYY-MM-DD HH:MM:SS。")

    db.update_ip_attempts(
        ip=ip,
        fail_count=body.fail_count,
        lock_time=db_lock_time,
        is_permanent_lock=body.is_permanent_lock
    )
    return {"status": "success"}

@router.delete("/settings/ip-lockouts/{ip}")
async def settings_delete_ip_lockout(
    ip: str,
    current_user: str = Depends(verify_admin)
):
    """解封并删除 IP 锁定监控记录（仅管理员）。"""
    db.reset_ip_attempts(ip)
    return {"status": "success"}
