"""
启动环境校验模块 — 在服务启动时执行一次，验证所有关键依赖是否满足。

校验失败时直接打印明确错误并终止进程，防止服务在残缺环境下带病运行。
"""
from __future__ import annotations
import sys


def _fail(message: str) -> None:
    """打印致命错误并以非零状态码退出进程。"""
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("  [启动失败] 环境校验未通过", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"  {message}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("", file=sys.stderr)
    sys.exit(1)


def _check_python_version() -> None:
    """校验 Python 版本：要求 >= 3.10（海象运算符、match 语法等）。"""
    if sys.version_info < (3, 10):
        _fail(
            f"Python 版本不足：当前 {sys.version}，要求 >= 3.10。\n"
            "  请升级 Python 后重新启动。"
        )


def _check_sm_cryptography() -> None:
    """校验国密套件（SM2/SM3/SM4）的系统算法与第三方依赖支持。

    - SM3：依赖系统 OpenSSL 支持（hashlib.new / hmac）。
    - SM2/SM4：依赖第三方 gmssl / pycryptodome 扩展包支持。
    """
    import hashlib
    import hmac

    # 1. 校验系统 OpenSSL SM3 算法支持
    try:
        hashlib.new("sm3", b"probe")
        hmac.new(b"probe-key", b"probe-payload", digestmod="sm3").hexdigest()
    except ValueError:
        _fail(
            "当前系统 OpenSSL 不支持 SM3 算法。\n"
            "  SM3 用于密码哈希及防篡改校验，服务拒绝启动。\n"
            "  解决方案：请升级系统 OpenSSL 至 1.1.1+ 并确保编译时启用了 SM3。"
        )

    # 2. 校验第三方 SM2/SM4 依赖库可导入
    try:
        from gmssl.sm2 import CryptSM2  # noqa: F401
        from gmssl.sm4 import CryptSM4  # noqa: F401
    except ImportError as e:
        _fail(
            f"缺少国密扩展依赖库：{e}\n"
            "  解决方案：请执行 uv add gmssl pycryptodome 补全依赖。"
        )


def _check_sqlite() -> None:
    """校验 SQLite 可连接并支持 WAL 模式（所有数据持久化的底层存储）。"""
    import sqlite3
    import tempfile
    import os

    try:
        tmp = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(tmp)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE _probe (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO _probe VALUES (1)")
        conn.commit()
        conn.close()
        os.unlink(tmp)
    except Exception as e:
        _fail(
            f"SQLite 可用性校验失败：{e}\n"
            "  所有任务记录、用户数据、审计日志均依赖 SQLite，服务拒绝启动。"
        )


def _check_data_dir_writable() -> None:
    """校验数据目录（data/）可写：存放 SQLite 数据库、上传文件、密钥文件。"""
    from pathlib import Path
    import tempfile

    data_dir = Path(__file__).parent.parent.parent.resolve() / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe = data_dir / ".write_probe"
        probe.write_text("probe")
        probe.unlink()
    except Exception as e:
        _fail(
            f"数据目录 '{data_dir}' 不可写：{e}\n"
            "  上传文件、数据库、密钥均写入此目录，服务拒绝启动。\n"
            "  解决方案：检查目录权限，确保运行用户对该目录有读写权。"
        )


def _check_croniter() -> None:
    """校验 croniter 第三方库可导入（定时清理任务依赖）。"""
    try:
        import croniter  # noqa: F401
    except ImportError:
        _fail(
            "缺少依赖库 croniter（定时清理任务所需）。\n"
            "  解决方案：执行 pip install croniter 后重新启动。"
        )


def _check_fastapi_deps() -> None:
    """校验 FastAPI / uvicorn / pydantic 等核心 Web 框架依赖可导入。"""
    missing = []
    for pkg in ("fastapi", "uvicorn", "pydantic", "starlette"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        _fail(
            f"缺少以下核心 Web 框架依赖：{', '.join(missing)}\n"
            "  解决方案：执行 uv add/pip install 补全依赖。"
        )


# ──────────────────────────────────────────────────────────
# 公开入口：统一执行所有校验，仅的原入口调用一次
# ──────────────────────────────────────────────────────────
def run_all_checks() -> None:
    """依次执行全部启动环境校验。任意一项失败则打印错误并终止进程。

    设计原则：
      - 仅在服务启动时调用一次，避免重复检测。
      - 所有校验均为快速轻量探测（无网络 I/O、无业务逻辑）。
      - 失败时输出清晰的人类可读错误与解决建议，而非底层异常堆栈。
    """
    checks = [
        ("Python 版本",         _check_python_version),
        ("国密套件与算法支持",  _check_sm_cryptography),
        ("SQLite 可用性",       _check_sqlite),
        ("数据目录可写性",      _check_data_dir_writable),
        ("croniter 依赖",       _check_croniter),
        ("Web 框架核心依赖",    _check_fastapi_deps),
    ]

    print("  正在执行启动环境校验...", flush=True)
    for name, fn in checks:
        try:
            fn()
            print(f"  [OK] {name}", flush=True)
        except SystemExit:
            # _fail() 已打印错误并调用 sys.exit，直接透传
            raise
        except Exception as e:
            # 未预期的异常也视为致命错误
            _fail(f"{name} 校验时发生未预期异常：{e}")
    print("  所有环境校验通过，服务启动中...\n", flush=True)
