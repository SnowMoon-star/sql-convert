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
]
