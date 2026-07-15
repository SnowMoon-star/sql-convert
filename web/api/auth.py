from __future__ import annotations
import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from web.core.db import db, hash_password
from web.core.auth import generate_session_token
from utils.config_manager import config
from core.logger import get_logger

router = APIRouter()


async def verify_admin(request: Request) -> str:
    """管理员鉴权依赖 — 在 verify_auth 基础上进一步验证管理员身份。"""
    username = await verify_auth(request)
    user_info = db.get_user(username)
    if not user_info or not user_info[2]:  # is_admin == 0
        raise HTTPException(status_code=403, detail="权限不足：此操作需要管理员权限。")
    return username


def handle_login_failure(username: str, client_ip: str):
    """登录失败后，更新数据库中对应的账号 and IP 失败尝试与锁定逻辑。"""
    EAST8 = datetime.timezone(datetime.timedelta(hours=8))
    now_utc8 = datetime.datetime.now(EAST8)
    now_str = now_utc8.isoformat()

    # 1. 更新账号失败计数及锁定
    fail_count_user, lock_time_user, lock_count_user, is_perm_lock_user = db.get_login_attempts(username)
    if lock_time_user:
        lock_time = datetime.datetime.fromisoformat(lock_time_user)
        if lock_time.tzinfo is None:
            lock_time = lock_time.replace(tzinfo=EAST8)
        if now_utc8 >= lock_time:
            fail_count_user = 0
            lock_time_user = None

    fail_count_user += 1
    if fail_count_user >= 5:
        # 常规锁定 1 天
        lock_count_user += 1
        fail_count_user = 0
        lock_time_user = (now_utc8 + datetime.timedelta(days=1)).isoformat()
        if lock_count_user >= 3:
            is_perm_lock_user = 1
    db.update_login_attempts(username, fail_count_user, lock_time_user, lock_count_user, is_perm_lock_user)

    # 2. 更新 IP 失败计数及封禁
    fail_count_ip, lock_time_ip, is_perm_lock_ip = db.get_ip_attempts(client_ip)
    if lock_time_ip:
        lock_time = datetime.datetime.fromisoformat(lock_time_ip)
        if lock_time.tzinfo is None:
            lock_time = lock_time.replace(tzinfo=EAST8)
        if now_utc8 >= lock_time:
            fail_count_ip = 0
            lock_time_ip = None

    fail_count_ip += 1
    if fail_count_ip == 5:
        # 临时封禁 1 小时
        lock_time_ip = (now_utc8 + datetime.timedelta(hours=1)).isoformat()
    elif fail_count_ip >= 10:
        # 永久封禁
        is_perm_lock_ip = 1
    db.update_ip_attempts(client_ip, fail_count_ip, lock_time_ip, is_perm_lock_ip)


async def verify_auth(request: Request) -> str:
    """身份鉴权与白名单安全验证依赖拦截器，返回当前经认证的用户名。"""
    client_ip = request.client.host

    # 1. 检验 IP 封禁状态 (黑名单)
    fail_count_ip, lock_time_ip, is_perm_lock_ip = db.get_ip_attempts(client_ip)
    if is_perm_lock_ip:
        raise HTTPException(status_code=403, detail="您的 IP 已被永久封禁，请联系管理员解锁。")
    if lock_time_ip:
        EAST8 = datetime.timezone(datetime.timedelta(hours=8))
        lock_time = datetime.datetime.fromisoformat(lock_time_ip)
        if lock_time.tzinfo is None:
            lock_time = lock_time.replace(tzinfo=EAST8)
        if datetime.datetime.now(EAST8) < lock_time:
            raise HTTPException(status_code=403, detail="您的 IP 因尝试失败过多被临时封禁，请稍后再试。")

    # 2. 检验 IP 白名单放行
    if config.get("web.ip_whitelist.enabled", False):
        if not db.is_ip_whitelisted(client_ip):
            raise HTTPException(status_code=403, detail="访问受限：您的 IP 不在白名单允许范围内。")

    # 3. 检验用户登录状态
    if config.get("web.auth.enabled", True):
        token = request.cookies.get("session_token")
        authenticated_user = db.get_username_by_session(token) if token else None
        if not authenticated_user:
            raise HTTPException(status_code=401, detail="凭证失效，请先进行登录。")
        # 每次合法 API 调用均刷新 Session 过期时刻（滑动窗口续期）
        db.touch_session(token)
        return authenticated_user
    return "admin"


class LoginRequest(BaseModel):
    """登录接口请求体（经过国密 RC4 解密后由中间件恢复为明文 JSON）。"""
    username: str
    password: str


# ──────────────────────────────────────────────────────────
# 登录认证接口
# ──────────────────────────────────────────────────────────
@router.post("/login")
async def login(
    request: Request,
    body: LoginRequest,
):
    """用户登录接口，内嵌连续错误锁定与封禁控制。"""
    username = body.username
    password = body.password
    client_ip = request.client.host

    EAST8 = datetime.timezone(datetime.timedelta(hours=8))
    # 1. 验证 IP 黑名单
    fail_count_ip, lock_time_ip, is_perm_lock_ip = db.get_ip_attempts(client_ip)
    if is_perm_lock_ip:
        db.write_login_log(username, client_ip, "IP_BANNED", "IP block is active (permanent)")
        raise HTTPException(status_code=403, detail="您的 IP 已被永久封禁，请联系管理员解锁。")
    if lock_time_ip:
        lock_time = datetime.datetime.fromisoformat(lock_time_ip)
        if lock_time.tzinfo is None:
            lock_time = lock_time.replace(tzinfo=EAST8)
        if datetime.datetime.now(EAST8) < lock_time:
            db.write_login_log(username, client_ip, "IP_BANNED", "IP block is active (temporary)")
            raise HTTPException(status_code=403, detail="您的 IP 已被临时锁定，请稍后再试。")

    # 2. 验证账号锁定
    fail_count_user, lock_time_user, lock_count_user, is_perm_lock_user = db.get_login_attempts(username)
    if is_perm_lock_user:
        db.write_login_log(username, client_ip, "LOCKED", "Account is locked permanently")
        raise HTTPException(status_code=401, detail="该账号因安全问题已被永久锁定，请管理员命令行解锁。")
    if lock_time_user:
        lock_time = datetime.datetime.fromisoformat(lock_time_user)
        if lock_time.tzinfo is None:
            lock_time = lock_time.replace(tzinfo=EAST8)
        if datetime.datetime.now(EAST8) < lock_time:
            db.write_login_log(username, client_ip, "LOCKED", "Account is locked temporarily")
            raise HTTPException(status_code=401, detail="该账号目前处于锁定惩罚期，请稍后再试。")

    # 3. 验证账户与密码
    user_info = db.get_user(username)
    if not user_info:
        handle_login_failure(username, client_ip)
        db.write_login_log(username, client_ip, "FAILED", "User not found")
        raise HTTPException(status_code=401, detail="用户名或密码不正确。")

    password_hash, salt, is_admin, _ = user_info
    if hash_password(password, salt) != password_hash:
        handle_login_failure(username, client_ip)
        db.write_login_log(username, client_ip, "FAILED", "Password mismatch")
        raise HTTPException(status_code=401, detail="用户名或密码不正确。")

    # 4. 登录成功，重置失败统计
    db.reset_login_attempts(username)
    db.reset_ip_attempts(client_ip)
    db.write_login_log(username, client_ip, "SUCCESS", "Login successful")

    # 5. 登录成功，设置 HttpOnly Cookie（防 XSS 证书窃取）
    # 注意：之前存在的 session_token_js（httponly=False）已删除，它使 HttpOnly 防护完全失效。
    # 前端如需读取 token，应读取本响应 body 中的 token 字段并存入内存变量（不得存入 localStorage）。
    token = generate_session_token(username)
    
    # 根据多地登录配置进行活跃会话管理
    allow_multi_login = config.get("web.auth.allow_multi_login", False)
    if not allow_multi_login:
        db.clear_user_sessions(username)
    db.add_session(username, token, client_ip)
    response = JSONResponse(content={
        "status": "success",
        "username": username,
        "token": token,
        "is_admin": bool(is_admin)
    })
    response.set_cookie(key="session_token", value=token, httponly=True, samesite="lax")
    return response


@router.post("/logout")
async def logout(request: Request, current_user: str = Depends(verify_auth)):
    """用户注销接口。"""
    client_ip = request.client.host
    token = request.cookies.get("session_token")
    if token:
        db.delete_session(token)
    db.write_operation_log(current_user, client_ip, "LOGOUT", "Logout successful")
    response = JSONResponse(content={"status": "success"})
    response.delete_cookie(key="session_token")
    return response


@router.get("/me")
async def get_current_user(current_user: str = Depends(verify_auth)):
    """获取当前登录用户的信息（用于前端恢复登录状态、管理员权限及头像）。"""
    user_info = db.get_user(current_user)
    is_admin = bool(user_info[2]) if user_info else False
    avatar = user_info[3] if user_info else None
    return {
        "username": current_user,
        "is_admin": is_admin,
        "avatar": avatar
    }


# 支持的头像 MIME 类型及其 magic bytes 前缀
_AVATAR_MAGIC: dict[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"RIFF": "image/webp",  # webp: RIFF????WEBP，进一步校验见下方
}
_AVATAR_MAX_BYTES = 2 * 1024 * 1024  # 2 MB


@router.put("/me/avatar")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: str = Depends(verify_auth),
):
    """上传当前用户头像，服务端校验格式（magic bytes）与大小（≤2MB），转 base64 存库。"""
    # 1. 读取原始字节（最多读取超限 1 字节，用于精确判断是否超出）
    raw = await file.read(_AVATAR_MAX_BYTES + 1)
    if len(raw) > _AVATAR_MAX_BYTES:
        raise HTTPException(status_code=413, detail="头像文件不能超过 2MB。")

    # 2. magic bytes 格式校验（防止伪造 MIME 类型）
    mime: str | None = None
    for magic, candidate_mime in _AVATAR_MAGIC.items():
        if raw.startswith(magic):
            # WebP 需额外校验第 8-12 字节为 b"WEBP"
            if candidate_mime == "image/webp" and raw[8:12] != b"WEBP":
                continue
            mime = candidate_mime
            break

    if mime is None:
        raise HTTPException(status_code=415, detail="头像格式不支持，仅允许 JPG / PNG / WebP。")

    # 3. 转 base64 Data URI 并写库
    import base64
    b64 = base64.b64encode(raw).decode("ascii")
    data_uri = f"data:{mime};base64,{b64}"
    db.update_user(current_user, avatar=data_uri)

    client_ip = request.client.host
    db.write_operation_log(current_user, client_ip, "UPLOAD_AVATAR", f"Avatar updated, size={len(raw)} bytes, mime={mime}")
    return {"status": "success", "message": "头像更新成功。"}


class ChangePasswordRequest(BaseModel):
    """修改密码请求体。"""
    old_password: str
    new_password: str


@router.post("/me/password")
async def change_own_password(request: Request, body: ChangePasswordRequest, current_user: str = Depends(verify_auth)):
    """当前用户修改自己的密码（需要旧密码验证）。"""
    client_ip = request.client.host

    user_info = db.get_user(current_user)
    if not user_info:
        raise HTTPException(status_code=404, detail="用户不存在。")

    password_hash, salt, _, __ = user_info
    if hash_password(body.old_password, salt) != password_hash:
        db.write_operation_log(current_user, client_ip, "CHANGE_PASSWORD_FAILED", "Old password mismatch")
        raise HTTPException(status_code=400, detail="旧密码不正确。")

    import uuid
    new_salt = uuid.uuid4().hex
    new_hash = hash_password(body.new_password, new_salt)
    db.update_user(current_user, new_hash, new_salt, None)

    db.write_operation_log(current_user, client_ip, "CHANGE_PASSWORD", "Password changed successfully")
    return {"status": "success", "message": "密码修改成功。"}
