"""Canonical 类型名常量 + 映射引擎。

Source Type → Canonical Type → Target Type
"""
import re

# ── 规范类型 ──
INTEGER_8 = "Integer8"
INTEGER_16 = "Integer16"
INTEGER_32 = "Integer32"
INTEGER_64 = "Integer64"
REAL_32 = "Real32"
REAL_64 = "Real64"
DECIMAL = "Decimal"
TEXT = "Text"
DATE_TIME = "DateTime"
DATE = "Date"
TIME = "Time"
BLOB = "Blob"
ENUM = "Enum"
SET = "Set"
BIT = "Bit"
BOOLEAN = "Boolean"


def build_type_pattern(dialect) -> re.Pattern:
    """从方言的 type_to_canonical 键构建匹配正则。
    按长度降序排列，确保 mediumint 在 int 之前匹配。
    自动匹配并丢弃显示宽度如 int(11)、decimal(10,2)。"""
    keys = sorted(dialect.type_to_canonical.keys(), key=len, reverse=True)
    return re.compile(
        r"\b(" + "|".join(re.escape(k) for k in keys) + r")\b(\s*\(\d+(,\d+)?\))?",
        re.IGNORECASE,
    )


# 需要保留尺寸参数的规范类型（VARCHAR(64)、DECIMAL(10,2) 等）
_SIZE_PRESERVING = {"Text", "Decimal"}


def map_types(text: str, source_dialect, target_dialect) -> tuple[str, int]:
    """将文本中所有源类型替换为目标类型。整数显示宽度丢弃，VARCHAR/DECIMAL 尺寸保留。"""
    if not source_dialect.type_to_canonical or not target_dialect.canonical_to_type:
        return text, 0

    pattern = build_type_pattern(source_dialect)

    def repl(m):
        src_type = m.group(1).lower()
        size_param = m.group(2) or ""  # 如 "(64)" 或 "(10,2)" 或空
        canonical = source_dialect.type_to_canonical.get(src_type)
        if canonical:
            target_type = target_dialect.canonical_to_type.get(canonical)
            if target_type:
                # 保留尺寸参数（Text/Decimal 类型）
                if canonical in _SIZE_PRESERVING and size_param.strip():
                    # 处理目标类型可能已有尺寸的情况（如 VARCHAR(255)）
                    base = target_type.split("(")[0]
                    return base + size_param
                return target_type
        return m.group(0)

    return pattern.subn(repl, text)
