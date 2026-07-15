"""国密接口公钥下发路由模块 — 提供免鉴权的 SM2 公钥拉取接口。"""
from __future__ import annotations
from fastapi import APIRouter
from web.core.sm_crypto_helper import get_or_create_sm2_keypair

router = APIRouter()


@router.get("/crypto/key")
def get_sm2_public_key():
    """获取服务端的 SM2 公钥（十六进制格式，128 字符）。

    此接口不需要鉴权，前端冷启动及加密登录请求前需调用此接口拉取公钥。
    """
    _, public_key = get_or_create_sm2_keypair()
    return {"public_key": public_key}
