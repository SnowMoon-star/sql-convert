"""阶段2: 标识符转换 — 引号风格转换。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_BACKTICK_QUOTE, CAP_DOUBLE_QUOTE

IDENTIFIER_RULES: list[Rule] = [
    Rule("convert_backtick_quote", CAP_BACKTICK_QUOTE,
         re.compile(r"`(\w+)`"),
         replacement="", scope="line", skip_insert=False,
         desc="将反引号标识符转为目标引号风格"),
    Rule("convert_double_quote", CAP_DOUBLE_QUOTE,
         re.compile(r'"(\w+)"'),
         replacement="", scope="line", skip_insert=False,
         desc="将双引号标识符转为目标引号风格"),
]
