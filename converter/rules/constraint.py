"""阶段5: 约束/索引适配。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_USING_BTREE

CONSTRAINT_RULES: list[Rule] = [
    Rule("strip_using_btree", CAP_USING_BTREE,
         re.compile(r"\s*USING\s+BTREE", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 USING BTREE"),
]
