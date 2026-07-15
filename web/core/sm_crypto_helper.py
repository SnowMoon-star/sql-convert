"""后端国密加解密辅助模块 — 集中提供基于 SM2 和 SM4-CBC 的加解密原语。"""
from __future__ import annotations
import os
from pathlib import Path
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
from gmssl.sm2 import CryptSM2
from core.logger import get_logger

DATA_DIR = Path(__file__).parent.parent.parent.resolve() / "data"
SM2_KEY_PATH = DATA_DIR / "sm2.key"


def get_or_create_sm2_keypair() -> tuple[str, str]:
    """获取本地持久化的 SM2 密钥对。若不存在，则动态生成并保存。

    返回:
      (private_key_hex, public_key_hex)
      私钥为 64 位十六进制字符串，公钥为 128 位十六进制字符串。
    """
    if SM2_KEY_PATH.exists():
        try:
            content = SM2_KEY_PATH.read_text(encoding="utf-8").strip()
            parts = content.split(":")
            if len(parts) == 2 and len(parts[0]) == 64 and len(parts[1]) == 128:
                return parts[0], parts[1]
        except Exception as e:
            get_logger().error(f"[SM2] 读取密钥对文件异常: {e}")

    # 自动生成新的 SM2 密钥对
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # 生成 32 字节随机私钥
        private_key_hex = os.urandom(32).hex()

        # 推导公钥
        tmp_crypt = CryptSM2(private_key=private_key_hex, public_key="")
        d = int(private_key_hex, 16)
        public_key_hex = tmp_crypt._kg(d, tmp_crypt.ecc_table['g'])

        # 写入文件保护
        SM2_KEY_PATH.write_text(f"{private_key_hex}:{public_key_hex}", encoding="utf-8")
        get_logger().info("[SM2] 已自动生成并持久化全新 SM2 密钥对。")
        return private_key_hex, public_key_hex
    except Exception as e:
        get_logger().error(f"[SM2] 自动生成密钥对失败: {e}")
        # 降级：如果写磁盘失败，返回内存临时密钥对
        private_key_hex = os.urandom(32).hex()
        tmp_crypt = CryptSM2(private_key=private_key_hex, public_key="")
        d = int(private_key_hex, 16)
        public_key_hex = tmp_crypt._kg(d, tmp_crypt.ecc_table['g'])
        return private_key_hex, public_key_hex


def sm2_decrypt(ciphertext_bytes: bytes) -> bytes:
    """使用服务端的 SM2 私钥解密数据。

    常用于解密前端用公钥加密的对称密钥信封。
    """
    priv_key, pub_key = get_or_create_sm2_keypair()
    sm2_crypt = CryptSM2(private_key=priv_key, public_key=pub_key)
    try:
        return sm2_crypt.decrypt(ciphertext_bytes)
    except Exception as e:
        get_logger().warning(f"[SM2] 解密失败: {e}")
        raise ValueError("SM2 解密失败：无效的密文或密钥不匹配。")


def sm4_cbc_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    """使用 SM4-CBC 算法加密明文。"""
    if len(key) != 16 or len(iv) != 16:
        raise ValueError("SM4 密钥和 IV 长度必须为 16 字节。")
    try:
        sm4 = CryptSM4()
        sm4.set_key(key, SM4_ENCRYPT)
        return sm4.crypt_cbc(iv, plaintext)
    except Exception as e:
        get_logger().error(f"[SM4] 加密异常: {e}")
        raise ValueError(f"SM4 加密失败: {e}")


def sm4_cbc_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """使用 SM4-CBC 算法解密密文（含自动 PKCS7 去填充）。"""
    if len(key) != 16 or len(iv) != 16:
        raise ValueError("SM4 密钥和 IV 长度必须为 16 字节。")
    try:
        sm4 = CryptSM4()
        sm4.set_key(key, SM4_DECRYPT)
        return sm4.crypt_cbc(iv, ciphertext)
    except Exception as e:
        get_logger().warning(f"[SM4] 解密异常: {e}")
        raise ValueError(f"SM4 解密失败: {e}")
