"""SQL 流式读取器 — 从 SQL 文件中流式提取单条语句。"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Iterator

from core.diagnostics import Statement
from reader.classifier import classify_statement


class SQLReader:
    """SQL 文件流式读取与语句切分器。"""

    def __init__(self, file_path: str | Path, encoding: str = "utf-8"):
        self.file_path = Path(file_path)
        self.encoding = encoding

    def iter_statements(self) -> Iterator[Statement]:
        """流式遍历文件，生成单条完整的 SQL Statement 实体（包装了物理行列和偏移）。

        能够处理并剔除：
        - 注释（行注释 --、# 和块注释 /* */）
        并能够处理：
        - 各种引号（单引号、双引号、反引号）及转义字符
        - PostgreSQL Dollar Quote ($tag$...$tag$)
        - MySQL DELIMITER 自定义结束符
        """
        if not self.file_path.exists():
            return

        state = "DEFAULT"  # DEFAULT, SINGLE_QUOTE, DOUBLE_QUOTE, BACKTICK, BLOCK_COMMENT, DOLLAR_QUOTE, MYSQL_VERSION_COMMENT
        dollar_tag = ""
        delimiter = ";"
        current_parts: list[str] = []

        stmt_start_line = -1
        stmt_start_offset = -1
        current_line = 0
        current_offset = 0

        with open(self.file_path, "r", encoding=self.encoding, errors="ignore") as f:
            for line in f:
                current_line += 1

                # 在默认状态下，检查是否是 MySQL DELIMITER 声明
                if state == "DEFAULT":
                    stripped = line.strip()
                    if stripped.upper().startswith("DELIMITER "):
                        parts = stripped.split(None, 1)
                        if len(parts) > 1:
                            delimiter = parts[1].strip()
                        current_offset += len(line)
                        continue

                i = 0
                n = len(line)
                while i < n:
                    ch = line[i]
                    char_offset = current_offset + i

                    if state == "DEFAULT":
                        # 跳过前导空白以确定语句的真正起止点
                        if not current_parts and ch.isspace():
                            i += 1
                            continue

                        # 行注释：直接忽略本行剩余部分
                        if ch == "-" and i + 1 < n and line[i + 1] == "-":
                            break
                        elif ch == "#":
                            break
                        # 块注释或条件注释开始
                        elif ch == "/" and i + 1 < n and line[i + 1] == "*":
                            if i + 2 < n and line[i + 2] == "!":
                                state = "MYSQL_VERSION_COMMENT"
                                if not current_parts:
                                    stmt_start_line = current_line
                                    stmt_start_offset = char_offset
                                current_parts.append("/*!")
                                i += 3
                                continue
                            else:
                                state = "BLOCK_COMMENT"
                                i += 2
                                continue

                        # 如果当前语句的记录未开始，在此处记录起始元数据
                        if not current_parts:
                            stmt_start_line = current_line
                            stmt_start_offset = char_offset

                        # 引号开始
                        if ch == "'":
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
                                stmt_text = "".join(current_parts).strip()
                                if stmt_text:
                                    yield Statement(
                                        text=stmt_text,
                                        statement_type=classify_statement(stmt_text),
                                        start_line=stmt_start_line,
                                        end_line=current_line,
                                        offset=stmt_start_offset,
                                        source_file=self.file_path
                                    )
                                current_parts = []
                                stmt_start_line = -1
                                stmt_start_offset = -1
                                i += delim_len
                                continue
                            else:
                                current_parts.append(ch)

                    elif state == "SINGLE_QUOTE":
                        if not current_parts:
                            stmt_start_line = current_line
                            stmt_start_offset = char_offset
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
                        if not current_parts:
                            stmt_start_line = current_line
                            stmt_start_offset = char_offset
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
                        if not current_parts:
                            stmt_start_line = current_line
                            stmt_start_offset = char_offset
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

                    elif state == "MYSQL_VERSION_COMMENT":
                        if not current_parts:
                            stmt_start_line = current_line
                            stmt_start_offset = char_offset
                        if ch == "*" and i + 1 < n and line[i + 1] == "/":
                            state = "DEFAULT"
                            current_parts.append("*/")
                            i += 2
                            continue
                        else:
                            current_parts.append(ch)

                    elif state == "DOLLAR_QUOTE":
                        if not current_parts:
                            stmt_start_line = current_line
                            stmt_start_offset = char_offset
                        tag_full = f"${dollar_tag}$"
                        if line[i:].startswith(tag_full):
                            state = "DEFAULT"
                            current_parts.append(tag_full)
                            i += len(tag_full)
                            continue
                        else:
                            current_parts.append(ch)

                    i += 1

                # 累加行末物理偏移（包含换行符长度）
                current_offset += len(line)

        # 返回最后残余部分
        stmt_text = "".join(current_parts).strip()
        if stmt_text:
            yield Statement(
                text=stmt_text,
                statement_type=classify_statement(stmt_text),
                start_line=stmt_start_line if stmt_start_line != -1 else current_line,
                end_line=current_line,
                offset=stmt_start_offset if stmt_start_offset != -1 else current_offset,
                source_file=self.file_path
            )
