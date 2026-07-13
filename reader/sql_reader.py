"""SQL 流式读取器 — 从 SQL 文件中流式提取单条语句。"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Iterator

class SQLReader:
    """SQL 文件流式读取与语句切分器。"""

    def __init__(self, file_path: str | Path, encoding: str = "utf-8"):
        self.file_path = Path(file_path)
        self.encoding = encoding

    def iter_statements(self) -> Iterator[str]:
        """流式遍历文件，生成单条完整的 SQL 语句。

        能够处理并剔除：
        - 注释（行注释 --、# 和块注释 /* */）
        并能够处理：
        - 各种引号（单引号、双引号、反引号）及转义字符
        - PostgreSQL Dollar Quote ($tag$...$tag$)
        - MySQL DELIMITER 自定义结束符
        """
        if not self.file_path.exists():
            return

        state = "DEFAULT"  # DEFAULT, SINGLE_QUOTE, DOUBLE_QUOTE, BACKTICK, BLOCK_COMMENT, DOLLAR_QUOTE
        dollar_tag = ""
        delimiter = ";"
        current_parts: list[str] = []

        with open(self.file_path, "r", encoding=self.encoding, errors="ignore") as f:
            for line in f:
                # 在默认状态下，检查是否是 MySQL DELIMITER 声明
                if state == "DEFAULT":
                    stripped = line.strip()
                    if stripped.upper().startswith("DELIMITER "):
                        parts = stripped.split(None, 1)
                        if len(parts) > 1:
                            delimiter = parts[1].strip()
                        continue  # 略过 DELIMITER 自身声明行的输出

                i = 0
                n = len(line)
                while i < n:
                    ch = line[i]

                    if state == "DEFAULT":
                        # 行注释：直接忽略本行剩余部分
                        if ch == "-" and i + 1 < n and line[i + 1] == "-":
                            break
                        elif ch == "#":
                            break
                        # 块注释开始
                        elif ch == "/" and i + 1 < n and line[i + 1] == "*":
                            state = "BLOCK_COMMENT"
                            i += 2
                            continue
                        # 引号开始
                        elif ch == "'":
                            state = "SINGLE_QUOTE"
                            current_parts.append(ch)
                        elif ch == '"':
                            state = "DOUBLE_QUOTE"
                            current_parts.append(ch)
                        elif ch == "`":
                            state = "BACKTICK"
                            current_parts.append(ch)
                        # PG Dollar Quote 开始
                        elif ch == "$":
                            match = re.match(r"^\$([a-zA-Z_0-9]*)\$", line[i:])
                            if match:
                                dollar_tag = match.group(1)
                                tag_full = f"${dollar_tag}$"
                                state = "DOLLAR_QUOTE"
                                current_parts.append(tag_full)
                                i += len(tag_full)
                                continue
                            else:
                                current_parts.append(ch)
                        else:
                            # 检查是否匹配当前 delimiter
                            delim_len = len(delimiter)
                            if line[i : i + delim_len] == delimiter:
                                current_parts.append(line[i : i + delim_len])
                                stmt = "".join(current_parts).strip()
                                if stmt:
                                    yield stmt
                                current_parts = []
                                i += delim_len
                                continue
                            else:
                                current_parts.append(ch)

                    elif state == "SINGLE_QUOTE":
                        if ch == "\\":
                            current_parts.append(ch)
                            if i + 1 < n:
                                current_parts.append(line[i + 1])
                                i += 2
                                continue
                        elif ch == "'":
                            state = "DEFAULT"
                            current_parts.append(ch)
                        else:
                            current_parts.append(ch)

                    elif state == "DOUBLE_QUOTE":
                        if ch == "\\":
                            current_parts.append(ch)
                            if i + 1 < n:
                                current_parts.append(line[i + 1])
                                i += 2
                                continue
                        elif ch == '"':
                            state = "DEFAULT"
                            current_parts.append(ch)
                        else:
                            current_parts.append(ch)

                    elif state == "BACKTICK":
                        if ch == "\\":
                            current_parts.append(ch)
                            if i + 1 < n:
                                current_parts.append(line[i + 1])
                                i += 2
                                continue
                        elif ch == "`":
                            state = "DEFAULT"
                            current_parts.append(ch)
                        else:
                            current_parts.append(ch)

                    elif state == "BLOCK_COMMENT":
                        if ch == "*" and i + 1 < n and line[i + 1] == "/":
                            state = "DEFAULT"
                            i += 2
                            continue
                        # 块注释字符直接忽略，不追加到语句中

                    elif state == "DOLLAR_QUOTE":
                        tag_full = f"${dollar_tag}$"
                        if line[i:].startswith(tag_full):
                            state = "DEFAULT"
                            current_parts.append(tag_full)
                            i += len(tag_full)
                            continue
                        else:
                            current_parts.append(ch)

                    i += 1

        # 返回最后残余部分（如果文件末尾没有 delimiter 且仍有字符）
        stmt = "".join(current_parts).strip()
        if stmt:
            yield stmt
