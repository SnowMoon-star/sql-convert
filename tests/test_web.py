"""Web UI 配置、异步调度器、双重滚动日志、IP白名单拦截与多重账号/IP锁定安全机制的单元测试。"""
import asyncio
import datetime
import logging
import tempfile
import unittest
from pathlib import Path

from utils.config_manager import ConfigManager
from web.core.scheduler import TaskScheduler, TaskInfo
from web.core.db import db, calculate_signature, verify_signature, hash_password
from core.logger import DailyAndSizeRotatingFileHandler


class TestWebConfig(unittest.TestCase):
    """测试 ConfigManager 的 YAML 读取与嵌套访问功能。"""

    def test_default_config(self):
        cfg = ConfigManager()
        self.assertEqual(cfg.get("converter.batch_size"), 1000)
        self.assertEqual(cfg.get("web.port"), 8000)
        self.assertTrue(cfg.get("dialects.pgsql.drop_cascade"))

    def test_dot_notation_access(self):
        cfg = ConfigManager()
        self.assertEqual(cfg.get("nonexistent.key", "fallback"), "fallback")
        self.assertEqual(cfg.get("converter.nonexistent", 999), 999)


class TestWebSecurityAndDatabase(unittest.TestCase):
    """测试 HMAC 签名计算、数据库存储及防篡改校验。"""

    def test_signature_verification(self):
        task_id = "test_uuid"
        status = "SUCCESS"
        out_file = "/data/output.sql"
        rep_html = "/data/report.html"

        sig = calculate_signature(task_id, status, out_file, rep_html)
        self.assertTrue(verify_signature(task_id, status, out_file, rep_html, sig))

        self.assertFalse(verify_signature(task_id, "FAILED", out_file, rep_html, sig))
        self.assertFalse(verify_signature(task_id, status, "/hacker.sql", rep_html, sig))

    def test_database_crud_and_tampering(self):
        task = TaskInfo(
            task_id="secure_task_1",
            filename="backup.sql",
            source_mode="mysql",
            target_mode="pgsql",
            status="SUCCESS",
            progress={"current_line": 500},
            output_file="/output.sql",
            report_html="/report.html",
            convert_type="upload",
            duration=123
        )
        setattr(task, "file_hash", "abc256hash")
        db.save_task(task)

        loaded_task, is_verified = db.get_task("secure_task_1")
        self.assertIsNotNone(loaded_task)
        self.assertTrue(is_verified)
        self.assertEqual(loaded_task.filename, "backup.sql")
        self.assertEqual(loaded_task.convert_type, "upload")
        self.assertEqual(loaded_task.duration, 123)

        with db._get_connection() as conn:
            conn.execute("UPDATE tasks SET status = 'FAILED' WHERE task_id = 'secure_task_1'")
            conn.commit()

        loaded_task_tampered, is_verified_tampered = db.get_task("secure_task_1")
        self.assertFalse(is_verified_tampered)

        with db._get_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE task_id = 'secure_task_1'")
            conn.commit()

    def test_user_ownership_isolation(self):
        # 1. 模拟写入两个不同属主的任务
        task_user1 = TaskInfo(
            task_id="task_u1",
            filename="user1.sql",
            source_mode="mysql",
            target_mode="pgsql",
            status="SUCCESS",
            username="user1"
        )
        setattr(task_user1, "file_hash", "hash1")
        
        task_user2 = TaskInfo(
            task_id="task_u2",
            filename="user2.sql",
            source_mode="mysql",
            target_mode="pgsql",
            status="SUCCESS",
            username="user2"
        )
        setattr(task_user2, "file_hash", "hash2")
        
        db.save_task(task_user1)
        db.save_task(task_user2)
        
        try:
            # 2. 读取并验证 username 归属
            t1, _ = db.get_task("task_u1")
            t2, _ = db.get_task("task_u2")
            self.assertEqual(t1.username, "user1")
            self.assertEqual(t2.username, "user2")
            self.assertEqual(t1.convert_type, "online")
            self.assertEqual(t1.duration, 0.0)
            
            # 3. 验证全量列表读取
            all_tasks = db.list_tasks()
            t_ids = [t.task_id for t, _ in all_tasks]
            self.assertIn("task_u1", t_ids)
            self.assertIn("task_u2", t_ids)
            
        finally:
            with db._get_connection() as conn:
                conn.execute("DELETE FROM tasks WHERE task_id IN ('task_u1', 'task_u2')")
                conn.commit()


class TestWebIPWhitelistAndLockout(unittest.TestCase):
    """测试 IP 动态白名单、账号失败锁定以及 IP 封禁与手动解锁策略。"""

    def test_ip_whitelist_crud(self):
        test_ip = "192.168.100.200"
        
        # 1. 初始状态不应包含该 IP
        self.assertFalse(db.is_ip_whitelisted(test_ip))
        
        # 2. 添加并验证
        db.add_to_whitelist(test_ip)
        self.assertTrue(db.is_ip_whitelisted(test_ip))
        
        # 3. 删除并验证
        db.remove_from_whitelist(test_ip)
        self.assertFalse(db.is_ip_whitelisted(test_ip))

    def test_account_attempts_lockout(self):
        test_user = "test_lock_user"
        
        # 1. 验证初始状态为未锁定
        fail_cnt, lock_t, lock_cnt, is_perm = db.get_login_attempts(test_user)
        self.assertEqual(fail_cnt, 0)
        self.assertEqual(is_perm, 0)
        
        # 2. 模拟输错 5 次，应触发临时锁定 (lock_time 写入)
        now_str = datetime.datetime.now().isoformat()
        db.update_login_attempts(test_user, 5, now_str, 1, 0)
        
        fail_cnt, lock_t, lock_cnt, is_perm = db.get_login_attempts(test_user)
        self.assertEqual(lock_cnt, 1)
        self.assertEqual(lock_t, now_str)
        self.assertEqual(is_perm, 0)
        
        # 3. 模拟连续锁定 3 次，应晋升为永久锁定
        db.update_login_attempts(test_user, 5, now_str, 3, 1)
        _, _, _, is_perm = db.get_login_attempts(test_user)
        self.assertEqual(is_perm, 1)
        
        # 4. 测试命令行解锁重置
        db.unlock_user(test_user)
        fail_cnt, _, lock_cnt, is_perm = db.get_login_attempts(test_user)
        self.assertEqual(fail_cnt, 0)
        self.assertEqual(lock_cnt, 0)
        self.assertEqual(is_perm, 0)

    def test_ip_attempts_ban(self):
        test_ip = "10.20.30.40"
        
        # 1. 验证 IP 尝试计数初始值
        fail_cnt, lock_t, is_perm = db.get_ip_attempts(test_ip)
        self.assertEqual(fail_cnt, 0)
        self.assertEqual(is_perm, 0)
        
        # 2. 连续 5 次失败，临时封禁
        now_str = datetime.datetime.now().isoformat()
        db.update_ip_attempts(test_ip, 5, now_str, 0)
        fail_cnt, lock_t, is_perm = db.get_ip_attempts(test_ip)
        self.assertEqual(lock_t, now_str)
        self.assertEqual(is_perm, 0)
        
        # 3. 连续 10 次失败（翻倍），永久封禁
        db.update_ip_attempts(test_ip, 10, now_str, 1)
        _, _, is_perm = db.get_ip_attempts(test_ip)
        self.assertEqual(is_perm, 1)
        
        # 4. 手动命令行解锁 IP
        db.unlock_ip(test_ip)
        fail_cnt, lock_t, is_perm = db.get_ip_attempts(test_ip)
        self.assertEqual(fail_cnt, 0)
        self.assertIsNone(lock_t)
        self.assertEqual(is_perm, 0)


class TestWebLoggerRotation(unittest.TestCase):
    """测试 DailyAndSizeRotatingFileHandler 按日期与大小双重滚动的边界情况。"""

    def test_logger_daily_and_size_rollover(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = Path(f.name)
            
        try:
            # 限制大小为极其狭小的 50 字节以便于瞬间触发体积轮转
            handler = DailyAndSizeRotatingFileHandler(
                filename=str(log_path),
                maxBytes=50,
                backupCount=2,
                encoding="utf-8"
            )
            
            # Mock 一个日志实体
            logger = logging.getLogger("test_rot_logger")
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)
            
            # 1. 验证正常写入不触发轮转
            logger.info("ABC")
            handler.flush()
            self.assertTrue(log_path.exists())
            self.assertFalse(log_path.with_name(log_path.name + ".1").exists())
            
            # 2. 验证体积越界 (大小轮转)
            logger.info("A" * 60)
            handler.flush()
            # 越界写入后，主文件重置，并分裂产生 .1 备份文件
            self.assertTrue(log_path.with_name(log_path.name + ".1").exists())
            
            # 3. 验证跨天时间变更 (天数轮转)
            # 手动修改 current_date 为昨天
            handler.current_date = "2026-07-12"
            
            # 跨天后写入记录，应立即主动触发 Rollover，并生成更旧的备份文件（如 .2）
            logger.info("ABC")
            handler.flush()
            self.assertTrue(log_path.with_name(log_path.name + ".2").exists())
            
            logger.removeHandler(handler)
            handler.close()
        finally:
            log_path.unlink(missing_ok=True)
            log_path.with_name(log_path.name + ".1").unlink(missing_ok=True)
            log_path.with_name(log_path.name + ".2").unlink(missing_ok=True)


class TestWebScheduler(unittest.TestCase):
    """测试 TaskScheduler 任务创建、池中异步运行及 WebSocket 通知行为。"""

    def setUp(self):
        self.scheduler = TaskScheduler()

    def test_create_and_submit_task(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write("SELECT 1;")
            input_path = Path(f.name)
        
        output_path = input_path.with_name(input_path.stem + "_out.sql")
        
        try:
            task_id = self.scheduler.create_task(
                filename=input_path.name,
                source_mode="mysql",
                target_mode="pgsql",
                file_hash="mock_hash_val"
            )
            
            task, is_verified = db.get_task(task_id)
            self.assertIsNotNone(task)
            self.assertEqual(task.status, "PENDING")
            self.assertTrue(is_verified)
            
            loop = asyncio.get_event_loop()
            
            ws_queue = asyncio.Queue()
            self.scheduler.register_ws_queue(ws_queue)
            
            self.scheduler.submit_task(task_id, input_path, output_path, loop)
            
            import time
            success = False
            for _ in range(20):
                cur_task, _ = db.get_task(task_id)
                if cur_task and cur_task.status in ("SUCCESS", "FAILED"):
                    success = True
                    break
                time.sleep(0.1)
                
            self.assertTrue(success)
            
            loop.run_until_complete(asyncio.sleep(0.05))
            self.assertGreater(ws_queue.qsize(), 0)
            
            self.scheduler.unregister_ws_queue(ws_queue)
            with db._get_connection() as conn:
                conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
                conn.commit()
            
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
            for report_file in input_path.parent.glob(f"{output_path.stem}*_report.html"):
                report_file.unlink(missing_ok=True)


class TestWebAuditAndCleanupScheduler(unittest.TestCase):
    """测试系统审计日志（登录、操作、定时日志）写入以及定时清理相关配置。"""

    def test_audit_logs_db_persistence(self):
        # 1. 测试登录审计日志写入与读取
        db.write_login_log("test_user_audit", "1.1.1.1", "FAILED", "Incorrect pass")
        db.write_login_log("test_user_audit", "1.1.1.1", "SUCCESS", "Welcome")
        
        with db._get_connection() as conn:
            logs = conn.execute("SELECT * FROM login_logs WHERE username = 'test_user_audit' ORDER BY created_at").fetchall()
            self.assertEqual(len(logs), 2)
            self.assertEqual(logs[0]["status"], "FAILED")
            self.assertEqual(logs[0]["ip"], "1.1.1.1")
            self.assertEqual(logs[0]["msg"], "Incorrect pass")
            self.assertEqual(logs[1]["status"], "SUCCESS")
            
            # 清理
            conn.execute("DELETE FROM login_logs WHERE username = 'test_user_audit'")
            conn.commit()

        # 2. 测试操作审计日志写入与读取
        db.write_operation_log("test_user_audit", "2.2.2.2", "CONVERT", "task_id=123")
        with db._get_connection() as conn:
            logs = conn.execute("SELECT * FROM operation_logs WHERE username = 'test_user_audit'").fetchall()
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]["action"], "CONVERT")
            self.assertEqual(logs[0]["ip"], "2.2.2.2")
            self.assertEqual(logs[0]["detail"], "task_id=123")
            
            # 清理
            conn.execute("DELETE FROM operation_logs WHERE username = 'test_user_audit'")
            conn.commit()

        # 3. 测试定时任务审计日志写入与读取
        db.write_timer_log("RETENTION_CLEANUP", 5, 10, "SUCCESS", "Finished in 0.05s")
        with db._get_connection() as conn:
            logs = conn.execute("SELECT * FROM timer_logs WHERE action = 'RETENTION_CLEANUP' ORDER BY id DESC").fetchall()
            self.assertGreaterEqual(len(logs), 1)
            self.assertEqual(logs[0]["deleted_tasks"], 5)
            self.assertEqual(logs[0]["deleted_files"], 10)
            self.assertEqual(logs[0]["status"], "SUCCESS")
            self.assertEqual(logs[0]["detail"], "Finished in 0.05s")

            # 清理
            conn.execute("DELETE FROM timer_logs WHERE action = 'RETENTION_CLEANUP'")
            conn.commit()

    def test_audit_logs_cleanup(self):
        """测试 delete_old_logs 能够正确物理删除各日志表中超出保留期的过期记录，
        同时保留仍在保留期内的记录。"""
        import datetime

        def ts_days_ago(days: float) -> str:
            """返回东八区 N 天前的时间字符串，用于模拟历史日志数据。"""
            from datetime import timezone, timedelta
            now_cst = datetime.datetime.now(timezone.utc) + timedelta(hours=8)
            return (now_cst - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

        # ── 准备测试数据 ──
        with db._get_connection() as conn:
            # 登录日志：31 天前（超期，应被清除）和 1 天前（未超期，应保留）
            conn.execute(
                "INSERT INTO login_logs (username, ip, status, msg, created_at) VALUES (?, ?, ?, ?, ?)",
                ("_test_cleanup_user", "9.9.9.9", "FAILED", "cleanup-test-old", ts_days_ago(31))
            )
            conn.execute(
                "INSERT INTO login_logs (username, ip, status, msg, created_at) VALUES (?, ?, ?, ?, ?)",
                ("_test_cleanup_user", "9.9.9.9", "SUCCESS", "cleanup-test-new", ts_days_ago(1))
            )

            # 操作日志：31 天前（超期）和 1 天前（未超期）
            conn.execute(
                "INSERT INTO operation_logs (username, ip, action, detail, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("_test_cleanup_user", "9.9.9.9", "CONVERT", "cleanup-test-old", "SUCCESS", ts_days_ago(31))
            )
            conn.execute(
                "INSERT INTO operation_logs (username, ip, action, detail, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("_test_cleanup_user", "9.9.9.9", "CONVERT", "cleanup-test-new", "SUCCESS", ts_days_ago(1))
            )

            # 定时任务日志：8 天前（超期，应被清除）和 1 天前（未超期，应保留）
            conn.execute(
                "INSERT INTO timer_logs (action, deleted_tasks, deleted_files, status, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("_TEST_CLEANUP_OLD", 0, 0, "SUCCESS", "cleanup-test-old", ts_days_ago(8))
            )
            conn.execute(
                "INSERT INTO timer_logs (action, deleted_tasks, deleted_files, status, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("_TEST_CLEANUP_NEW", 0, 0, "SUCCESS", "cleanup-test-new", ts_days_ago(1))
            )
            conn.commit()

        try:
            # ── 执行清理（登录/操作日志保留 30 天，定时任务日志保留 7 天）──
            result = db.delete_old_logs(login_days=30, operation_days=30, timer_days=7)

            # ── 断言：各表返回的删除数量 ≥ 1（可能存在其他测试数据） ──
            self.assertGreaterEqual(result["login_logs"],     1, "至少应清理 1 条超期登录日志")
            self.assertGreaterEqual(result["operation_logs"], 1, "至少应清理 1 条超期操作日志")
            self.assertGreaterEqual(result["timer_logs"],     1, "至少应清理 1 条超期定时任务日志")

            # ── 断言：超期记录已被物理删除 ──
            with db._get_connection() as conn:
                old_login = conn.execute(
                    "SELECT COUNT(*) as cnt FROM login_logs WHERE username = '_test_cleanup_user' AND msg = 'cleanup-test-old'"
                ).fetchone()["cnt"]
                self.assertEqual(old_login, 0, "超期登录日志应已被物理删除")

            # ── 断言：未超期记录仍然保留 ──
            with db._get_connection() as conn:
                new_login = conn.execute(
                    "SELECT COUNT(*) as cnt FROM login_logs WHERE username = '_test_cleanup_user' AND msg = 'cleanup-test-new'"
                ).fetchone()["cnt"]
                self.assertEqual(new_login, 1, "未超期登录日志应被保留")

                new_op = conn.execute(
                    "SELECT COUNT(*) as cnt FROM operation_logs WHERE username = '_test_cleanup_user' AND detail = 'cleanup-test-new'"
                ).fetchone()["cnt"]
                self.assertEqual(new_op, 1, "未超期操作日志应被保留")

                new_timer = conn.execute(
                    "SELECT COUNT(*) as cnt FROM timer_logs WHERE action = '_TEST_CLEANUP_NEW'"
                ).fetchone()["cnt"]
                self.assertEqual(new_timer, 1, "未超期定时任务日志应被保留")

        finally:
            # ── 清理残余测试数据（确保测试幂等） ──
            with db._get_connection() as conn:
                conn.execute("DELETE FROM login_logs WHERE username = '_test_cleanup_user'")
                conn.execute("DELETE FROM operation_logs WHERE username = '_test_cleanup_user'")
                conn.execute("DELETE FROM timer_logs WHERE action IN ('_TEST_CLEANUP_OLD', '_TEST_CLEANUP_NEW')")
                conn.commit()

    def test_api_encryption_and_tampering(self):
        from web.core.sm_crypto_helper import get_or_create_sm2_keypair, sm2_decrypt, sm4_cbc_encrypt, sm4_cbc_decrypt
        from gmssl.sm2 import CryptSM2

        # 1. 验证 SM2 密钥对获取与派生
        priv, pub = get_or_create_sm2_keypair()
        self.assertEqual(len(priv), 64)
        self.assertEqual(len(pub), 128)

        # 2. 验证 SM2 加解密闭环（C1C2C3 mode 0）
        envelop = b"test-key-16bytes" + b"test-iv--16bytes"
        sm2_client = CryptSM2(private_key="", public_key=pub)
        ciphertext = sm2_client.encrypt(envelop)
        
        # 服务端使用私钥解密
        decrypted_envelop = sm2_decrypt(ciphertext)
        self.assertEqual(decrypted_envelop, envelop)

        # 3. 验证 SM4-CBC 对称加解密
        key = envelop[:16]
        iv = envelop[16:]
        plaintext = b"Hello, SM4-CBC Secure Payload!"
        
        ciphertext_sm4 = sm4_cbc_encrypt(plaintext, key, iv)
        decrypted_plaintext = sm4_cbc_decrypt(ciphertext_sm4, key, iv)
        self.assertEqual(decrypted_plaintext, plaintext)


class TestActiveUsersManagement(unittest.TestCase):
    """测试活跃用户（Session）的分页、模糊查询、角色过滤及踢出拦截功能。"""

    def setUp(self):
        # 清理之前的脏数据
        with db._get_connection() as conn:
            conn.execute("DELETE FROM user_sessions")
            conn.execute("DELETE FROM users WHERE username IN ('test_user_a', 'test_user_b', 'another_user', 'admin', 'manager1', 'manager2', 'user1')")
            # 插入基础测试用户
            conn.execute("INSERT INTO users (username, password_hash, salt, is_admin, avatar) VALUES ('test_user_a', 'hash', 'salt', 1, 'avatar_a')")
            conn.execute("INSERT INTO users (username, password_hash, salt, is_admin, avatar) VALUES ('test_user_b', 'hash', 'salt', 0, 'avatar_b')")
            conn.execute("INSERT INTO users (username, password_hash, salt, is_admin, avatar) VALUES ('another_user', 'hash', 'salt', 0, '')")
            conn.commit()

    def tearDown(self):
        # 清理测试数据
        with db._get_connection() as conn:
            conn.execute("DELETE FROM user_sessions")
            conn.execute("DELETE FROM users WHERE username IN ('test_user_a', 'test_user_b', 'another_user', 'admin', 'manager1', 'manager2', 'user1')")
            conn.commit()

    def test_active_sessions_crud_and_query(self):
        # 1. 插入测试数据
        db.add_session("test_user_a", "token_a1", "192.168.1.10")
        db.add_session("test_user_a", "token_a2", "192.168.1.11")
        db.add_session("test_user_b", "token_b1", "10.0.0.1")
        db.add_session("another_user", "token_c1", "127.0.0.1")

        # 2. 验证全部查询（不带过滤条件，分页 1，大小 10）并确认 avatar/is_admin 联合查询返回
        items, total = db.list_active_sessions(page=1, size=10)
        self.assertEqual(total, 4)
        self.assertEqual(len(items), 4)
        
        # 验证关联 users 成功取得字段
        item_a1 = next(x for x in items if x["session_token"] == "token_a1")
        self.assertEqual(item_a1["avatar"], "avatar_a")
        self.assertEqual(item_a1["is_admin"], 1)

        item_c1 = next(x for x in items if x["session_token"] == "token_c1")
        self.assertEqual(item_c1["avatar"], "")
        self.assertEqual(item_c1["is_admin"], 0)

        # 3. 验证分页查询（大小 2）
        items_p1, total = db.list_active_sessions(page=1, size=2)
        self.assertEqual(total, 4)
        self.assertEqual(len(items_p1), 2)
        items_p2, total = db.list_active_sessions(page=2, size=2)
        self.assertEqual(total, 4)
        self.assertEqual(len(items_p2), 2)
        tokens_p1 = {x["session_token"] for x in items_p1}
        tokens_p2 = {x["session_token"] for x in items_p2}
        self.assertTrue(tokens_p1.isdisjoint(tokens_p2))

        # 4. 验证用户名模糊查询
        items_filter_user, total = db.list_active_sessions(page=1, size=10, username="test")
        self.assertEqual(total, 3)
        self.assertEqual(len(items_filter_user), 3)
        for x in items_filter_user:
            self.assertTrue(x["username"].startswith("test_user"))

        # 5. 验证 IP 模糊查询
        items_filter_ip, total = db.list_active_sessions(page=1, size=10, ip="192.168")
        self.assertEqual(total, 2)
        self.assertEqual(len(items_filter_ip), 2)
        for x in items_filter_ip:
            self.assertTrue(x["ip"].startswith("192.168"))

        # 6. 验证身份角色过滤 (is_admin=1)
        items_filter_admin, total = db.list_active_sessions(page=1, size=10, is_admin=1)
        self.assertEqual(total, 2)
        self.assertEqual(len(items_filter_admin), 2)
        for x in items_filter_admin:
            self.assertEqual(x["is_admin"], 1)

        items_filter_normal, total = db.list_active_sessions(page=1, size=10, is_admin=0)
        self.assertEqual(total, 2)
        self.assertEqual(len(items_filter_normal), 2)
        for x in items_filter_normal:
            self.assertEqual(x["is_admin"], 0)

        # 7. 验证删除会话（踢出）
        db.delete_session("token_a1")
        items_after, total_after = db.list_active_sessions(page=1, size=10)
        self.assertEqual(total_after, 3)
        self.assertNotIn("token_a1", {x["session_token"] for x in items_after})

    def test_kick_user_permissions(self):
        from web.api.routes import kick_user, KickRequest
        from fastapi import HTTPException
        from unittest.mock import MagicMock
        
        # 1. 模拟三个用户写入 users 表（超管 admin、普通管理员 manager1、普通管理员 manager2、普通用户 user1）
        with db._get_connection() as conn:
            # 插入超管
            conn.execute("INSERT OR REPLACE INTO users (username, password_hash, salt, is_admin, avatar) VALUES ('admin', 'hash', 'salt', 1, 'avatar_admin')")
            # 插入普通管理员 1
            conn.execute("INSERT OR REPLACE INTO users (username, password_hash, salt, is_admin, avatar) VALUES ('manager1', 'hash', 'salt', 1, 'avatar_m1')")
            # 插入普通管理员 2
            conn.execute("INSERT OR REPLACE INTO users (username, password_hash, salt, is_admin, avatar) VALUES ('manager2', 'hash', 'salt', 1, 'avatar_m2')")
            # 插入普通用户
            conn.execute("INSERT OR REPLACE INTO users (username, password_hash, salt, is_admin, avatar) VALUES ('user1', 'hash', 'salt', 0, 'avatar_u1')")
            conn.commit()

        db.add_session("admin", "token_admin", "127.0.0.1")
        db.add_session("manager1", "token_m1", "127.0.0.1")
        db.add_session("manager2", "token_m2", "127.0.0.1")
        db.add_session("user1", "token_u1", "127.0.0.1")

        # 2. 模拟 request
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # 自建 loop 运行以避免 asyncio.run 导致 event loop 清空
        loop = asyncio.new_event_loop()
        try:
            # 场景 A: 管理员踢自己 (manager1 踢 manager1) -> 预期 400 失败
            with self.assertRaises(HTTPException) as ctx:
                loop.run_until_complete(kick_user(mock_request, KickRequest(session_token="token_m1"), current_user="manager1"))
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("禁止强制下线您自己的账号", ctx.exception.detail)

            # 场景 B: 普通管理员踢超管 (manager1 踢 admin) -> 预期 403 失败
            with self.assertRaises(HTTPException) as ctx:
                loop.run_until_complete(kick_user(mock_request, KickRequest(session_token="token_admin"), current_user="manager1"))
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertIn("普通管理员不能强制下线其他管理员", ctx.exception.detail)

            # 场景 C: 普通管理员踢普通管理员 (manager1 踢 manager2) -> 预期 403 失败
            with self.assertRaises(HTTPException) as ctx:
                loop.run_until_complete(kick_user(mock_request, KickRequest(session_token="token_m2"), current_user="manager1"))
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertIn("普通管理员不能强制下线其他管理员", ctx.exception.detail)

            # 场景 D: 普通管理员踢普通用户 (manager1 踢 user1) -> 预期成功
            res = loop.run_until_complete(kick_user(mock_request, KickRequest(session_token="token_u1"), current_user="manager1"))
            self.assertEqual(res["status"], "success")
            self.assertIsNone(db.get_username_by_session("token_u1"))

            # 场景 E: 超管踢普通管理员 (admin 踢 manager2) -> 预期成功
            res2 = loop.run_until_complete(kick_user(mock_request, KickRequest(session_token="token_m2"), current_user="admin"))
            self.assertEqual(res2["status"], "success")
            self.assertIsNone(db.get_username_by_session("token_m2"))
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
