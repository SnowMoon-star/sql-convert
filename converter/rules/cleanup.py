"""阶段1: 预处理清理 — 删除源方言特有的注释/锁表/会话变量/DELIMITER。"""
import re
from converter.pipeline import Rule
from converter.capabilities import (
    CAP_VERSION_COMMENT, CAP_LOCK_TABLES, CAP_DELIMITER,
    CAP_SESSION_VARS, CAP_CHARSET, CAP_FOREIGN_KEY_CHECKS, CAP_ORACLE_HINTS,
)

CLEANUP_RULES: list[Rule] = [
    Rule("strip_version_comment", CAP_VERSION_COMMENT,
         re.compile(r"/\*!\d+\s.*?\*/;?", re.DOTALL),
         replacement="", scope="global", skip_insert=True,
         desc="剔除 mysqldump 的版本条件注释"),
    Rule("strip_lock_tables", CAP_LOCK_TABLES,
         re.compile(r"^\s*(LOCK\s+TABLES\s.*?;|UNLOCK\s+TABLES\s*;)\s*$",
                    re.IGNORECASE | re.MULTILINE),
         replacement="", scope="global", skip_insert=True,
         desc="删除 LOCK TABLES / UNLOCK TABLES"),
    Rule("normalize_delimiter", CAP_DELIMITER,
         re.compile(r"^\s*DELIMITER\s+(\S+)\s*$(.*?)\1\s*$\s*^\s*DELIMITER\s*;\s*$",
                    re.IGNORECASE | re.MULTILINE | re.DOTALL),
         replacement="", scope="global", skip_insert=True,
         desc="处理 DELIMITER 块"),
    Rule("strip_session_vars", CAP_SESSION_VARS,
         re.compile(r"^\s*SET\s+(@OLD_\w+|@@[\w.]+|@\w+)\s*=.*?;\s*$", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 SET @OLD_... / SET @@... 会话变量"),
    Rule("strip_set_names", CAP_CHARSET,
         re.compile(r"^\s*SET\s+NAMES\s+'?\w+'?(\s+COLLATE\s+'?\w+'?)?\s*;\s*$", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 SET NAMES xxx"),
    Rule("strip_foreign_key_checks", CAP_FOREIGN_KEY_CHECKS,
         re.compile(r"^\s*SET\s+FOREIGN_KEY_CHECKS\s*=\s*\d+\s*;\s*$", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 SET FOREIGN_KEY_CHECKS"),
    Rule("strip_oracle_hints", CAP_ORACLE_HINTS,
         re.compile(r"/\*\+.*?\*/", re.DOTALL),
         replacement="", scope="global", skip_insert=True,
         desc="删除 Oracle 优化器提示"),
]
