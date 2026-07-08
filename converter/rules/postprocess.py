"""阶段6: 后处理 — 最终语法修正。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_AUTO_INCREMENT

POSTPROCESS_RULES: list[Rule] = [
    Rule("fix_autoincrement_syntax", CAP_AUTO_INCREMENT,
         re.compile(r"\bNOT\s+NULL\s+AUTOINCREMENT\b", re.IGNORECASE),
         replacement="AUTOINCREMENT", scope="line", skip_insert=True,
         desc="去除 AUTOINCREMENT 前的 NOT NULL"),
]
