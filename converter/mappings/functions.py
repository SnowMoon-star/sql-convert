"""Canonical 函数名常量 + 简单映射引擎。

Source Function → Canonical Function → Target Function
仅处理简单名称替换。结构变换函数（IF, LIMIT 等）保留为 Rule。
"""
import re

# ── 规范函数（简单替换类）──
CURRENT_TIMESTAMP = "CurrentTimestamp"
CURRENT_DATE = "CurrentDate"
CURRENT_TIME = "CurrentTime"
COALESCE = "Coalesce"
CONCAT_WS = "ConcatWs"
GROUP_CONCAT = "GroupConcat"
DATE_FORMAT = "DateFormat"
STR_TO_DATE = "StrToDate"
UNIX_TIMESTAMP = "UnixTimestamp"
FROM_UNIXTIME = "FromUnixtime"
UUID = "Uuid"
LENGTH = "Length"
CHAR_LENGTH = "CharLength"


from functools import lru_cache

@lru_cache(maxsize=16)
def _get_cached_function_pattern(dialect_class) -> re.Pattern:
    keys = sorted(dialect_class.function_to_canonical.keys(), key=len, reverse=True)
    return re.compile(
        "|".join(re.escape(k) for k in keys),
        re.IGNORECASE,
    )


def build_function_pattern(dialect) -> re.Pattern:
    """从方言的 function_to_canonical 键构建匹配正则。"""
    return _get_cached_function_pattern(dialect.__class__)


def map_functions(text: str, source_dialect, target_dialect) -> tuple[str, int]:
    """将文本中所有源函数替换为目标函数。"""
    if not source_dialect.function_to_canonical or not target_dialect.canonical_to_function:
        return text, 0

    pattern = build_function_pattern(source_dialect)

    def repl(m):
        src_func = m.group(0)
        for key, canonical in source_dialect.function_to_canonical.items():
            if key.upper() == src_func.upper():
                target_func = target_dialect.canonical_to_function.get(canonical)
                if target_func:
                    return target_func
        return m.group(0)

    return pattern.subn(repl, text)
