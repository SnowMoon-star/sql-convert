from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from web.core.db import db, hash_password
from web.api.auth import verify_admin

router = APIRouter()


# ──────────────────────────────────────────────────────────
# 管理员接口的数据模型
# ──────────────────────────────────────────────────────────
class CreateUserRequest(BaseModel):
    """创建用户请求体。"""
    username: str
    password: str
    is_admin: int = 0


class UpdateUserRequest(BaseModel):
    """更新用户请求体（所有字段可选）。"""
    password: Optional[str] = None
    is_admin: Optional[int] = None


# ──────────────────────────────────────────────────────────
# 用户管理接口（仅管理员可操作）
# ──────────────────────────────────────────────────────────
@router.get("/users")
async def list_users(
    username: str | None = None,
    is_admin: int | None = None,
    is_locked: int | None = None,
    current_user: str = Depends(verify_admin)
):
    """获取所有用户列表及其安全状态（仅管理员）。"""
    return db.list_users(username=username, is_admin=is_admin, is_locked=is_locked)


@router.post("/users")
async def create_user(request: Request, body: CreateUserRequest, current_user: str = Depends(verify_admin)):
    """创建新用户（仅管理员）。"""
    client_ip = request.client.host
    if not body.username or not body.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空。")

    import uuid
    salt_val = uuid.uuid4().hex
    hash_val = hash_password(body.password, salt_val)

    if not db.create_user(body.username.strip(), hash_val, salt_val, body.is_admin):
        raise HTTPException(status_code=409, detail=f"用户 '{body.username}' 已存在。")

    db.write_operation_log(current_user, client_ip, "CREATE_USER",
                           f"Created user: {body.username}, is_admin={body.is_admin}")
    return {"status": "success", "username": body.username}


@router.put("/users/{username}")
async def update_user(request: Request, username: str, body: UpdateUserRequest,
                      current_user: str = Depends(verify_admin)):
    """更新用户密码或角色（仅管理员）。"""
    client_ip = request.client.host
    username_strip = username.strip()

    if username_strip == "admin" and body.is_admin == 0:
        raise HTTPException(status_code=400, detail="不能取消默认管理员的管理权限。")

    target_user_info = db.get_user(username_strip)
    if not target_user_info:
        raise HTTPException(status_code=404, detail=f"用户 '{username_strip}' 不存在。")
    is_target_admin = bool(target_user_info[2])

    if current_user != "admin":
        # 普通管理员修改别人时，如果对方也是管理员，则拒绝！
        if username_strip != current_user and is_target_admin:
            raise HTTPException(status_code=403, detail="权限不足：普通管理员不能修改其他管理员账号。")

    password_hash = None
    salt_val = None
    if body.password:
        import uuid
        salt_val = uuid.uuid4().hex
        password_hash = hash_password(body.password, salt_val)

    if not db.update_user(username_strip, password_hash, salt_val, body.is_admin):
        raise HTTPException(status_code=404, detail=f"用户 '{username_strip}' 不存在。")

    changes = []
    if body.password:
        changes.append("password")
    if body.is_admin is not None:
        changes.append(f"is_admin={body.is_admin}")
    db.write_operation_log(current_user, client_ip, "UPDATE_USER",
                           f"Updated user: {username_strip}, changes: {', '.join(changes)}")
    return {"status": "success"}


@router.delete("/users/{username}")
async def delete_user(request: Request, username: str, current_user: str = Depends(verify_admin)):
    """删除用户（仅管理员，且管理员不能删除其他管理员，admin超管可以删除任意非自用户）。"""
    client_ip = request.client.host
    username_strip = username.strip()

    if username_strip == current_user:
        raise HTTPException(status_code=400, detail="不能删除当前登录的管理员账号。")
    if username_strip == "admin":
        raise HTTPException(status_code=400, detail="不能删除默认超管账号。")

    target_user_info = db.get_user(username_strip)
    if not target_user_info:
        raise HTTPException(status_code=404, detail=f"用户 '{username_strip}' 不存在。")
    is_target_admin = bool(target_user_info[2])

    if current_user != "admin":
        # 普通管理员删除别人时，如果对方也是管理员，则拒绝！
        if is_target_admin:
            raise HTTPException(status_code=403, detail="权限不足：普通管理员不能删除其他管理员账号。")

    if not db.delete_user(username_strip):
        raise HTTPException(status_code=500, detail=f"删除用户 '{username_strip}' 失败。")

    db.write_operation_log(current_user, client_ip, "DELETE_USER", f"Deleted user: {username_strip}")
    return {"status": "success"}


@router.post("/users/{username}/unlock")
async def unlock_user_account(request: Request, username: str, current_user: str = Depends(verify_admin)):
    """解锁被锁定的用户账号（仅管理员）。"""
    client_ip = request.client.host
    db.unlock_user(username.strip())
    db.write_operation_log(current_user, client_ip, "UNLOCK_USER", f"Unlocked user: {username}")
    return {"status": "success"}
