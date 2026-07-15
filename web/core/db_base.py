from __future__ import annotations
import datetime
import hashlib
import hmac
import os
import sqlite3
import uuid
from pathlib import Path
from utils.config_manager import config
from core.logger import get_logger

# 确定持久化存储目录
DATA_DIR = Path(__file__).parent.parent.parent.resolve() / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "tasks.db"
SECRET_KEY_PATH = DATA_DIR / "secret.key"


def get_secret_key() -> bytes:
    """获取防篡改签名秘钥。如无，则自动生成持久化秘钥文件。"""
    config_key = config.get("web.secret_key")
    if config_key and config_key != "change-me-to-a-secure-key":
        return config_key.encode("utf-8")

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_bytes()

    new_key = os.urandom(32).hex().encode("utf-8")
    try:
        SECRET_KEY_PATH.write_bytes(new_key)
    except Exception as e:
        get_logger().error(f"[DB] 写入秘钥文件失败: {e}")
    return new_key


def calculate_signature(
    task_id: str,
    status: str,
    output_file: str | None,
    report_html: str | None
) -> str:
    """基于 HMAC-SM3 算法为一条任务记录的关键字段进行哈希签名。
    若当前 OpenSSL 不支持 SM3，将抛出 ValueError，服务应在启动阶段失败。
    """
    key = get_secret_key()
    payload = f"{task_id}:{status}:{output_file or ''}:{report_html or ''}".encode("utf-8")
    return hmac.new(key, payload, digestmod="sm3").hexdigest()


def verify_signature(
    task_id: str,
    status: str,
    output_file: str | None,
    report_html: str | None,
    signature: str
) -> bool:
    """校验数据库取出的记录是否与保存时的签名相符，防御外部篡改。"""
    calculated = calculate_signature(task_id, status, output_file, report_html)
    return hmac.compare_digest(calculated, signature)


def hash_password(password: str, salt: str) -> str:
    """执行加盐 SM3 哈希计算。若当前 OpenSSL 不支持 SM3，将抛出 ValueError。"""
    return hashlib.new("sm3", (password + salt).encode("utf-8")).hexdigest()


def _now_cst() -> str:
    """返回东八区当前时间字符串，格式 YYYY-MM-DD HH:mm:ss。"""
    from datetime import datetime, timezone, timedelta
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


def _session_expires_at() -> str:
    """基于配置 web.auth.session_expire 计算 Session 的到期时刻（东八区），单位为秒。"""
    from datetime import datetime, timezone, timedelta
    expire_seconds = config.get("web.auth.session_expire", 7200)
    return (datetime.now(timezone.utc) + timedelta(hours=8) + timedelta(seconds=expire_seconds)).strftime("%Y-%m-%d %H:%M:%S")


class DatabaseManagerBase:
    """SQLite 持久化连接管理器基类，管理数据库连接与数据表初始化。"""

    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """初始化 SQLite 数据表结构，并执行播种播洒默认用户与白名单。"""
        get_logger().info(f"[DB] 初始化数据库连接，文件: {self.db_path}")
        with self._get_connection() as conn:
            # 1. 创建核心 SQL 转换任务表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    source_mode TEXT NOT NULL,
                    target_mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress TEXT,
                    error TEXT,
                    output_file TEXT,
                    report_html TEXT,
                    signature TEXT NOT NULL,
                    convert_type TEXT DEFAULT 'online',
                    duration REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            # 2. 创建用户持久化表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 3. 创建账号登录锁频监控表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    username TEXT PRIMARY KEY,
                    fail_count INTEGER DEFAULT 0,
                    lock_time TIMESTAMP,
                    lock_count INTEGER DEFAULT 0,
                    is_permanent_lock INTEGER DEFAULT 0
                )
            """)

            # 4. 创建 IP 封禁监控表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ip_attempts (
                    ip TEXT PRIMARY KEY,
                    fail_count INTEGER DEFAULT 0,
                    lock_time TIMESTAMP,
                    is_permanent_lock INTEGER DEFAULT 0
                )
            """)

            # 5. 创建 IP 白名单拦截表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ip_whitelist (
                    ip TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 6. 创建登录审计日志表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    status TEXT NOT NULL,
                    msg TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 7. 创建操作审计日志表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    action TEXT NOT NULL,
                    detail TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 8. 创建定时任务执行日志表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS timer_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    deleted_tasks INTEGER DEFAULT 0,
                    deleted_files INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    detail TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 确保创建 user_sessions 表，用于同一账号单地登录限制
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    username TEXT NOT NULL,
                    session_token TEXT PRIMARY KEY,
                    ip TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            # 确保 user_sessions 表包含 ip 字段
            try:
                conn.execute("ALTER TABLE user_sessions ADD COLUMN ip TEXT")
            except sqlite3.OperationalError:
                pass
            # 确保 user_sessions 表包含 expires_at 字段（会话滑动窗口续期列）
            try:
                conn.execute("ALTER TABLE user_sessions ADD COLUMN expires_at TIMESTAMP")
            except sqlite3.OperationalError:
                pass
            
            # 确保 tasks 表包含 username 字段
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN username TEXT")
            except sqlite3.OperationalError:
                pass
            # 确保 tasks 表包含 convert_type 和 duration 字段
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN convert_type TEXT DEFAULT 'online'")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN duration REAL DEFAULT 0.0")
            except sqlite3.OperationalError:
                pass
            # 确保 tasks 表包含 completed_at 字段（完成时间戳）
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP")
            except sqlite3.OperationalError:
                pass
            # 确保 operation_logs 表包含 status 字段
            try:
                conn.execute("ALTER TABLE operation_logs ADD COLUMN status TEXT DEFAULT 'SUCCESS'")
            except sqlite3.OperationalError:
                pass
            # 确保 users 表包含 avatar 字段（base64 Data URI）
            try:
                conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
            except sqlite3.OperationalError:
                pass
            conn.commit()

            # 6. 执行播种初始化：若 users 表为空，根据配置进行管理员注入
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                default_user = config.get("web.auth.username", "admin")
                default_pass = config.get("web.auth.password", "admin")
                
                salt_val = uuid.uuid4().hex
                hash_val = hash_password(default_pass, salt_val)
                
                cursor.execute(
                    "INSERT INTO users (username, password_hash, salt, is_admin, created_at) VALUES (?, ?, ?, 1, ?)",
                    (default_user, hash_val, salt_val, _now_cst())
                )
                conn.commit()
                get_logger().info(f"[DB] 初始化播种：注入配置预置 of 初始加盐管理员: {default_user}")

            # 7. 执行白名单初始化：若白名单为空，自动注入本地环回 IP 防自锁
            cursor.execute("SELECT COUNT(*) FROM ip_whitelist")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT OR IGNORE INTO ip_whitelist (ip, created_at) VALUES ('127.0.0.1', ?)", (_now_cst(),))
                cursor.execute("INSERT OR IGNORE INTO ip_whitelist (ip, created_at) VALUES ('::1', ?)", (_now_cst(),))
                conn.commit()
                get_logger().info("[DB] 初始化播种：向动态白名单写入本地环回 IP (127.0.0.1 / ::1)")
