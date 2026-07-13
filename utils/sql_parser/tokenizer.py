"""SQL 词法切分与辅助匹配工具。"""
from __future__ import annotations
import re

# 匹配 CREATE TABLE `name` ( 或 CREATE TABLE IF NOT EXISTS `name` (
_CREATE_TABLE_PAT = re.compile(
    r"""
    CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?  # 可选 IF NOT EXISTS
    (?:`(\w+)`|"(\w+)"|(\w+))                    # 表名（反引号、双引号、无引号）
    \s*\(""",
    re.IGNORECASE | re.VERBOSE,
)

# 匹配列定义开头的标识符: `name`、"name" 或无引号 name
_COL_START_PAT = re.compile(r'^\s*(?:`(\w+)`|"(\w+)"|(\w+))\s')

# 匹配 COMMENT 'xxx' 或 COMMENT "xxx"（支持跨行注释）
_COMMENT_PAT = re.compile(
    r"""COMMENT\s+(['"])(.*?)\1""",
    re.IGNORECASE | re.DOTALL,
)

# 匹配表 COMMENT = 'xxx'（在 CREATE TABLE 尾部，支持跨行）
_TABLE_COMMENT_PAT = re.compile(
    r"""COMMENT\s*=\s*(['"])(.*?)\1""",
    re.IGNORECASE | re.DOTALL,
)

# 匹配 DROP TABLE IF EXISTS `name`
_DROP_TABLE_PAT = re.compile(
    r"""DROP\s+TABLE\s+IF\s+EXISTS\s+(?:`(\w+)`|"(\w+)"|(\w+))\s*;""",
    re.IGNORECASE,
)


def _strip_quotes(name: str) -> str:
    """去掉标识符外层的反引号或双引号。"""
    if (name.startswith('`') and name.endswith('`')) or \
       (name.startswith('"') and name.endswith('"')):
        return name[1:-1]
    return name


def _extract_comment(text: str) -> str | None:
    """从文本中提取 COMMENT 'xxx' 的注释文本。"""
    m = _COMMENT_PAT.search(text)
    if m:
        return m.group(2)
    return None


def _extract_identifiers(ids_text: str) -> list[str]:
    """从 KEY/FK 列列表中提取纯标识符名（去引号、去 ASC/DESC/前缀长度）。

    处理: `col` ASC, "col2" DESC, col3(10), `col4` 等格式。
    """
    result: list[str] = []
    for part in ids_text.split(','):
        part = part.strip()
        if not part:
            continue
        # 匹配引号包裹的标识符: `name` 或 "name"，可能后跟 ASC/DESC/(N)
        m = re.match(r'[`"](\w+)[`"]', part)
        if m:
            result.append(m.group(1))
        else:
            # 无引号标识符：取第一个单词，去掉前缀长度括号 col(10) → col
            word = part.split()[0] if part.split() else part
            word = re.sub(r'\(\d+\)$', '', word)
            if word:
                result.append(word)
    return result


def _split_by_top_level_commas(body: str) -> list[str]:
    """在顶层逗号处分割 CREATE TABLE body，忽略括号和引号内的逗号。

    括号深度跟踪：只在深度为 0 且不在引号内时才将逗号视为分隔符。
    """
    parts: list[str] = []
    depth = 0
    in_single = False
    in_double = False
    in_backtick = False
    last = 0

    i = 0
    n = len(body)
    while i < n:
        ch = body[i]

        if ch == '\\':
            i += 2  # 跳过转义字符
            continue

        if ch == "'" and not in_double and not in_backtick:
            in_single = not in_single
        elif ch == '"' and not in_single and not in_backtick:
            in_double = not in_double
        elif ch == '`' and not in_single and not in_double:
            in_backtick = not in_backtick
        elif ch == '(' and not in_single and not in_double and not in_backtick:
            depth += 1
        elif ch == ')' and not in_single and not in_double and not in_backtick:
            depth -= 1
        elif ch == ',' and depth == 0 and not in_single and not in_double and not in_backtick:
            parts.append(body[last:i])
            last = i + 1

        i += 1

    # 最后一部分
    remainder = body[last:].strip()
    if remainder:
        parts.append(remainder)

    return parts


def _find_matching_paren(text: str, start: int) -> int:
    """从 start 位置（'(' 的位置）开始，找到匹配的 ')' 位置。

    使用 while 循环以支持转义字符双步跳跃（i += 2），
    避免 `\'` 等转义序列错误翻转引号状态。
    """
    depth = 0
    in_single = False
    in_double = False
    in_backtick = False

    i = start
    n = len(text)
    while i < n:
        ch = text[i]

        # 转义字符：跳过自身及下一个字符，防止 \' 翻转引号状态
        if ch == '\\' and (in_single or in_double):
            i += 2
            continue

        if ch == "'" and not in_double and not in_backtick:
            in_single = not in_single
        elif ch == '"' and not in_single and not in_backtick:
            in_double = not in_double
        elif ch == '`' and not in_single and not in_double:
            in_backtick = not in_backtick
        elif ch == '(' and not in_single and not in_double and not in_backtick:
            depth += 1
        elif ch == ')' and not in_single and not in_double and not in_backtick:
            depth -= 1
            if depth == 0:
                return i

        i += 1

    return -1  # 未找到匹配


def _extract_table_name(sql: str) -> str | None:
    """从 CREATE TABLE 语句中提取表名。"""
    m = _CREATE_TABLE_PAT.search(sql)
    if m:
        # 三个捕获组之一：反引号、双引号、无引号
        return m.group(1) or m.group(2) or m.group(3)
    return None
