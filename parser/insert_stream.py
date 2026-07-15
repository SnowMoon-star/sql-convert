"""DML INSERT 流式解析引擎 — 逐行流式解析 INSERT 语句。"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Iterator

@dataclass
class InsertRow:
    """包装单行 INSERT 数据的对象，提供类似 list 的读取行为。"""
    values: list[str]

    def __iter__(self) -> Iterator[str]:
        return iter(self.values)

    def __getitem__(self, idx: int | slice) -> str | list[str]:
        return self.values[idx]

    def __len__(self) -> int:
        return len(self.values)


def _parse_value_row(row_str: str) -> InsertRow:
    """解析单行值列表 (v1, v2, ...)，处理引号和转义。"""
    values: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    i = 0
    n = len(row_str)

    while i < n:
        ch = row_str[i]

        if ch == "\\":
            if in_single or in_double:
                # 转义符号（如 \' 或 \"）：将其原样追加并跳过下一个字符，防止引号状态机误翻转
                current.append(ch)
                if i + 1 < n:
                    current.append(row_str[i + 1])
                    i += 2
                    continue

        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
        elif ch == "," and not in_single and not in_double:
            val = "".join(current).strip()
            values.append(val)
            current = []
        else:
            current.append(ch)

        i += 1

    # 最后一个值
    val = "".join(current).strip()
    if val:
        values.append(val)

    return InsertRow(values)


def iter_insert_rows(sql: str) -> Iterator[InsertRow]:
    """流式解析单条 INSERT 语句中的所有 values 行。

    输入：一条完整的 INSERT SQL，例如:
      INSERT INTO `tbl` (a, b) VALUES (1, 'hello'), (2, 'world');
    输出：逐行生成并返回每一行的列数据。
    """
    state = "DEFAULT"  # DEFAULT, SINGLE_QUOTE, DOUBLE_QUOTE, BACKTICK, BLOCK_COMMENT
    i = 0
    n = len(sql)

    # 1. 扫描跳过 DDL / 头部声明，找到 VALUES 关键字
    values_pos = -1
    while i < n:
        ch = sql[i]
        if state == "DEFAULT":
            if ch == "-" and i + 1 < n and sql[i + 1] == "-":
                next_newline = sql.find("\n", i)
                i = next_newline if next_newline != -1 else n
                continue
            elif ch == "#":
                next_newline = sql.find("\n", i)
                i = next_newline if next_newline != -1 else n
                continue
            elif ch == "/" and i + 1 < n and sql[i + 1] == "*":
                state = "BLOCK_COMMENT"
                i += 2
                continue
            elif ch in ("'", '"', "`"):
                state = "SINGLE_QUOTE" if ch == "'" else ("DOUBLE_QUOTE" if ch == '"' else "BACKTICK")
            elif ch.upper() == "V":
                if sql[i : i + 6].upper() == "VALUES":
                    # VALUES 后面必须是空白字符或开括号 (
                    if i + 6 < n and (sql[i + 6].isspace() or sql[i + 6] == "("):
                        values_pos = i + 6
                        break
        elif state in ("SINGLE_QUOTE", "DOUBLE_QUOTE", "BACKTICK"):
            quote = "'" if state == "SINGLE_QUOTE" else ('"' if state == "DOUBLE_QUOTE" else "`")
            if ch == "\\":
                i += 2
                continue
            elif ch == quote:
                state = "DEFAULT"
        elif state == "BLOCK_COMMENT":
            if ch == "*" and i + 1 < n and sql[i + 1] == "/":
                state = "DEFAULT"
                i += 2
                continue
        i += 1

    if values_pos == -1:
        return

    # 2. 从 values_pos 开始，提取每一组被括号包裹的行 (...)
    i = values_pos
    state = "DEFAULT"
    depth = 0
    start = -1

    while i < n:
        ch = sql[i]
        if state == "DEFAULT":
            if ch == "-" and i + 1 < n and sql[i + 1] == "-":
                next_newline = sql.find("\n", i)
                i = next_newline if next_newline != -1 else n
                continue
            elif ch == "#":
                next_newline = sql.find("\n", i)
                i = next_newline if next_newline != -1 else n
                continue
            elif ch == "/" and i + 1 < n and sql[i + 1] == "*":
                state = "BLOCK_COMMENT"
                i += 2
                continue
            elif ch == "'":
                state = "SINGLE_QUOTE"
            elif ch == '"':
                state = "DOUBLE_QUOTE"
            elif ch == "`":
                state = "BACKTICK"
            elif ch == "(":
                if depth == 0:
                    start = i + 1
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and start != -1:
                    row_str = sql[start:i]
                    yield _parse_value_row(row_str)
                    start = -1
        elif state in ("SINGLE_QUOTE", "DOUBLE_QUOTE", "BACKTICK"):
            quote = "'" if state == "SINGLE_QUOTE" else ('"' if state == "DOUBLE_QUOTE" else "`")
            if ch == "\\":
                i += 2
                continue
            elif ch == quote:
                state = "DEFAULT"
        elif state == "BLOCK_COMMENT":
            if ch == "*" and i + 1 < n and sql[i + 1] == "/":
                state = "DEFAULT"
                i += 2
                continue
        i += 1
