"""FastAPI API 路由处理器 — 聚合了新拆分的各个业务模块子路由，并向后兼容导出所有原本在此定义的类和函数。"""
from __future__ import annotations

from fastapi import APIRouter
from web.api.auth import (
    router as auth_router, verify_admin, handle_login_failure, verify_auth, LoginRequest, login, logout,
    get_current_user, upload_avatar, ChangePasswordRequest, change_own_password
)
from web.api.settings import (
    router as settings_router, get_whitelist_list, add_whitelist_ip, delete_whitelist_ip,
    WhitelistUpdateRequest, WhitelistCreateRequest, UserLockoutUpdateRequest, UserLockoutCreateRequest,
    IPLockoutUpdateRequest, IPLockoutCreateRequest, settings_get_whitelist, settings_add_whitelist,
    settings_update_whitelist, settings_delete_whitelist, settings_get_user_lockouts,
    settings_create_user_lockout, settings_update_user_lockout, settings_delete_user_lockout,
    settings_get_ip_lockouts, settings_create_ip_lockout, settings_update_ip_lockout,
    settings_delete_ip_lockout
)
from web.api.active_users import (
    router as active_users_router, KickRequest, get_active_users, kick_user
)
from web.api.users import (
    router as users_router, CreateUserRequest, UpdateUserRequest, list_users, create_user, update_user,
    delete_user, unlock_user_account
)
from web.api.tasks import (
    router as tasks_router, calculate_file_hash, DIALECT_LABELS, list_dialects, list_tasks, get_task,
    validate_sql_file, start_conversion, download_output, view_report, get_stats,
    get_stats_history, websocket_endpoint
)
from web.api.logs import (
    router as logs_router, query_login_logs, query_operation_logs, query_timer_logs
)

from web.api.crypto_routes import router as crypto_router

router = APIRouter(prefix="/api")

# 引入所有子路由
router.include_router(crypto_router)
router.include_router(auth_router)
router.include_router(settings_router)
router.include_router(active_users_router)
router.include_router(users_router)
router.include_router(tasks_router)
router.include_router(logs_router)
