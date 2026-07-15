"""sql_convert 接口级国密混合安全传输套件 (SM4-CBC + SM2 + SM3)。"""
from __future__ import annotations
import base64
import hmac
import json
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from web.core.sm_crypto_helper import sm2_decrypt, sm4_cbc_decrypt
from core.logger import get_logger


def decrypt_payload(base64_str: str, key: bytes, iv: bytes) -> dict | list:
    """对 Base64 密文解码并利用 SM4-CBC 还原明文 JSON 结构。"""
    ciphertext = base64.b64decode(base64_str.encode("utf-8"))
    raw_bytes = sm4_cbc_decrypt(ciphertext, key, iv)
    return json.loads(raw_bytes.decode("utf-8"))


class APISecurityMiddleware(BaseHTTPMiddleware):
    """接口加密与防篡改安全验证中间件 (基于 SM2 密钥信封交换，SM4-CBC 传输加密和 SM3 完整性校验)。"""

    async def dispatch(self, request: Request, call_next):
        from starlette.responses import Response
        
        path = request.url.path
        # 非 API 路径、GET 请求或公钥下发接口直接透传，不做任何加密校验
        if not path.startswith("/api") or request.method == "GET" or path == "/api/crypto/key":
            return await call_next(request)

        # 1. 提取签名与密钥交换参数
        timestamp_str = request.headers.get("X-Timestamp") or request.query_params.get("timestamp")
        nonce = request.headers.get("X-Nonce") or request.query_params.get("nonce")
        signature = request.headers.get("X-Signature") or request.query_params.get("signature")
        encrypted_key_b64 = request.headers.get("X-Encrypted-Key") or request.query_params.get("encrypted_key")

        if not timestamp_str or not nonce or not signature or not encrypted_key_b64:
            get_logger().warning(f"[Security] 拦截未授权访问：缺失接口安全验证参数。Path: {path}")
            return Response(
                content=json.dumps({"detail": "安全验证失败：缺失防篡改签名或密钥信封。"}),
                status_code=403,
                media_type="application/json"
            )

        # 2. 校验时戳防重放 (5分钟限制)
        try:
            req_time = float(timestamp_str) / 1000.0
            if req_time < 1000000000:
                req_time = float(timestamp_str)
            if abs(time.time() - req_time) > 300:
                get_logger().warning(f"[Security] 拦截重放/过期请求。时差超限。Path: {path}")
                return Response(
                    content=json.dumps({"detail": "安全验证失败：请求超时，请校准本地系统时钟。"}),
                    status_code=403,
                    media_type="application/json"
                )
        except Exception:
            return Response(
                content=json.dumps({"detail": "安全验证失败：时间戳格式非法。"}),
                status_code=403,
                media_type="application/json"
            )

        # 3. 利用 SM2 私钥解密对称密钥信封，解析出 16 字节 SM4 Key 与 16 字节 IV
        try:
            encrypted_key_bytes = base64.b64decode(encrypted_key_b64.encode("utf-8"))
            envelop = sm2_decrypt(encrypted_key_bytes)
            if len(envelop) != 32:
                raise ValueError("解密出的密钥信封长度必须为 32 字节。")
            sm4_key = envelop[:16]
            sm4_iv = envelop[16:32]
        except Exception as e:
            get_logger().warning(f"[Security] 解析或解密密钥信封失败: {e}")
            return Response(
                content=json.dumps({"detail": "安全验证失败：密钥解密失败，请校准客户端公钥。"}),
                status_code=403,
                media_type="application/json"
            )

        # 4. 判断请求类型并校签与解密
        body_bytes = b""
        if request.method in ("POST", "PUT", "DELETE"):
            content_type = request.headers.get("content-type", "")
            if "multipart/form-data" in content_type:
                # 文件上传只校验基本参数签名：sign(path + ":" + timestamp + ":" + nonce)
                payload_to_sign = f"{path}:{timestamp_str}:{nonce}"
                expected_sig = hmac.new(sm4_key, payload_to_sign.encode("utf-8"), digestmod="sm3").hexdigest()
                if not hmac.compare_digest(expected_sig, signature):
                    get_logger().warning(f"[Security] 拦截篡改的文件上传请求！Path: {path}")
                    return Response(
                        content=json.dumps({"detail": "安全验证失败：文件上传接口签名校验不通过。"}),
                        status_code=403,
                        media_type="application/json"
                    )
                return await call_next(request)
            else:
                body_bytes = await request.body()

        # 处理非文件上传的请求体
        if body_bytes:
            try:
                payload_json = json.loads(body_bytes.decode("utf-8"))
                encrypted_data = payload_json.get("payload")
                if not encrypted_data:
                    return Response(
                        content=json.dumps({"detail": "安全验证失败：接口参数格式不符合加密标准。"}),
                        status_code=400,
                        media_type="application/json"
                    )
                # 校验签名: sign(path + ":" + timestamp + ":" + nonce + ":" + encrypted_data)
                payload_to_sign = f"{path}:{timestamp_str}:{nonce}:{encrypted_data}"
                expected_sig = hmac.new(sm4_key, payload_to_sign.encode("utf-8"), digestmod="sm3").hexdigest()
                if not hmac.compare_digest(expected_sig, signature):
                    get_logger().warning(f"[Security] 拦截内容篡改请求！Path: {path}")
                    return Response(
                        content=json.dumps({"detail": "安全验证失败：接口内容防篡改签名校验失败。"}),
                        status_code=403,
                        media_type="application/json"
                    )
                
                # 解密 Body 并重装为明文供底层 FastAPI 路由解析
                decrypted_dict = decrypt_payload(encrypted_data, sm4_key, sm4_iv)
                decrypted_bytes = json.dumps(decrypted_dict).encode("utf-8")
                
                async def receive():
                    return {"type": "http.request", "body": decrypted_bytes, "more_body": False}
                request._receive = receive
                # 覆盖 cached body，防止 FastAPI 逻辑直接使用读取到的未解密密文缓存
                request._body = decrypted_bytes
                
            except Exception as e:
                get_logger().warning(f"[Security] 接口明文解密失败: {e}")
                return Response(
                    content=json.dumps({"detail": f"安全验证失败：密文解析或解密失败。"}),
                    status_code=400,
                    media_type="application/json"
                )

        # 5. 执行路由并直接返回，响应体不再加密
        return await call_next(request)
