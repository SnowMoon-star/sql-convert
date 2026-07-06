"""MySQL → Kingbase (MySQL 兼容模式) 转换规则表。

新增规则时只需向 RULES 列表追加条目。主流程 convert.py 不需要改动。

规则字段：
- name:        规则唯一标识，用于 -v 统计与错误日志
- pattern:     预编译的 re.Pattern
- replacement: 字符串或 Callable[[re.Match], str]
- scope:       "global"（整文件一次性 re.sub）或 "line"（逐行应用）
- skip_insert: scope="line" 时，True 表示跳过以 INSERT INTO 开头的行
- desc:        人类可读描述
"""

import re
from typing import Callable

RULES: list[dict] = [
    {
        "name": "strip_version_comment",
        "pattern": re.compile(r"/\*!\d+\s.*?\*/;?", re.DOTALL),
        "replacement": "",
        "scope": "global",
        "skip_insert": True,
        "desc": "剔除 mysqldump 的版本条件注释 /*!40101 ... */",
    },
    {
        "name": "strip_lock_tables",
        "pattern": re.compile(
            r"^\s*(LOCK\s+TABLES\s.*?;|UNLOCK\s+TABLES\s*;)\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        "replacement": "",
        "scope": "global",
        "skip_insert": True,
        "desc": "删除 LOCK TABLES / UNLOCK TABLES 行",
    },
    {
        "name": "normalize_delimiter",
        # 匹配 DELIMITER $$ ... $$ DELIMITER ; 块，把内部 $$ 换回 ;，去掉 DELIMITER 行
        "pattern": re.compile(
            r"^\s*DELIMITER\s+(\S+)\s*$(.*?)\1\s*$\s*^\s*DELIMITER\s*;\s*$",
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        ),
        "replacement": lambda m: m.group(2).replace(m.group(1), ";").strip() + ";\n",
        "scope": "global",
        "skip_insert": True,
        "desc": "处理 DELIMITER $$ ... $$ DELIMITER ; 块，把 $$ 换回 ;",
    },
    {
        "name": "strip_session_vars",
        "pattern": re.compile(
            r"^\s*SET\s+(@OLD_\w+|@@[\w.]+|@\w+)\s*=.*?;\s*$",
            re.IGNORECASE,
        ),
        "replacement": "",
        "scope": "line",
        "skip_insert": True,
        "desc": "删除 SET @OLD_... / SET @@... 会话变量行",
    },
    {
        "name": "strip_engine_clause",
        "pattern": re.compile(r"\s*ENGINE\s*=\s*\w+", re.IGNORECASE),
        "replacement": "",
        "scope": "line",
        "skip_insert": True,
        "desc": "删除表级 ENGINE=xxx 子句",
    },
    {
        "name": "strip_default_charset",
        "pattern": re.compile(
            r"\s*(DEFAULT\s+)?(CHARACTER\s+SET|CHARSET)\s*=?\s*\w+"
            r"(\s+COLLATE\s*=?\s*\w+)?",
            re.IGNORECASE,
        ),
        "replacement": "",
        "scope": "line",
        "skip_insert": True,
        "desc": "删除表级 DEFAULT CHARSET / CHARACTER SET / COLLATE 子句",
    },
    {
        "name": "strip_table_auto_increment",
        "pattern": re.compile(r"\s*AUTO_INCREMENT\s*=\s*\d+", re.IGNORECASE),
        "replacement": "",
        "scope": "line",
        "skip_insert": True,
        "desc": "删除表级 AUTO_INCREMENT=N 起始值（列级 AUTO_INCREMENT 保留）",
    },
    {
        "name": "strip_row_format",
        "pattern": re.compile(
            r"\s*(ROW_FORMAT|KEY_BLOCK_SIZE|PACK_KEYS|STATS_PERSISTENT|"
            r"STATS_AUTO_RECALC|DELAY_KEY_WRITE)\s*=\s*\w+",
            re.IGNORECASE,
        ),
        "replacement": "",
        "scope": "line",
        "skip_insert": True,
        "desc": "删除 ROW_FORMAT / KEY_BLOCK_SIZE 等表选项",
    },
    {
        "name": "strip_column_charset",
        "pattern": re.compile(
            r"\s+(CHARACTER\s+SET|CHARSET)\s+\w+(\s+COLLATE\s+\w+)?",
            re.IGNORECASE,
        ),
        "replacement": "",
        "scope": "line",
        "skip_insert": True,
        "desc": "删除列定义中的 CHARACTER SET / COLLATE 子句",
    },
]
