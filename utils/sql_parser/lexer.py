from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Iterator

# 定义 Token 类型常量
T_KEYWORD = "KEYWORD"
T_IDENTIFIER = "IDENTIFIER"
T_QUOTED_IDENTIFIER = "QUOTED_IDENTIFIER"
T_STRING = "STRING"
T_NUMBER = "NUMBER"
T_PUNCTUATION = "PUNCTUATION"
T_COMMENT = "COMMENT"
T_EOF = "EOF"

# 常见的 SQL 关键字集合（不区分大小写）
KEYWORDS = {
    "CREATE", "TABLE", "ALTER", "ADD", "CONSTRAINT", "PRIMARY", "KEY", "FOREIGN",
    "REFERENCES", "UNIQUE", "INDEX", "COMMENT", "ON", "COLUMN", "IS", "NOT",
    "NULL", "DEFAULT", "AUTO_INCREMENT", "ON", "DELETE", "UPDATE", "CASCADE",
    "SET", "RESTRICT", "NO", "ACTION", "DROP", "IF", "EXISTS", "CHECK", "ENGINE",
    "CHARSET", "COLLATE", "AUTOINCREMENT"
}


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type}, {repr(self.value)}, L{self.line}:C{self.column})"


class Lexer:
    """带行列坐标的轻量级 SQL DDL 词法分析器。"""

    def __init__(self, text: str):
        self.text = text
        self.tokens: list[Token] = []
        self._tokenize()

    def _tokenize(self) -> None:
        # Token 匹配大正则，组合各词法类别
        token_spec = [
            ("COMMENT_BLOCK", r"/\*.*?\*/"),                              # 块注释
            ("COMMENT_LINE", r"(?:--|#)[^\n]*"),                          # 单行注释
            ("STRING", r"'[^'\\]*(?:\\.[^'\\]*)*'"),                      # 单引号字符串（支持转义）
            ("STRING_DOUBLE", r'"[^"\\]*(?:\\.[^"\\]*)*"'),                # 双引号字符串 / 标识符
            ("QUOTED_ID", r"`[^`]*`"),                                    # 反引号标识符
            ("NUMBER", r"\d+(?:\.\d+)?"),                                 # 数字
            ("PUNCTUATION", r"[(),.;=]"),                                 # 标点符号
            ("ID", r"[a-zA-Z_][a-zA-Z0-9_]*"),                            # 标识符/关键字
            ("NEWLINE", r"\n"),                                           # 换行
            ("SKIP", r"[ \t\r]+"),                                        # 空白跳过
            ("MISMATCH", r"."),                                           # 其它未匹配字符
        ]
        master_pat = re.compile("|".join(f"(?P<{name}>{pat})" for name, pat in token_spec), re.DOTALL)

        line = 1
        line_start = 0
        
        for m in master_pat.finditer(self.text):
            kind = m.lastgroup
            value = m.group(kind)
            column = m.start() - line_start + 1

            if kind == "NEWLINE":
                line += 1
                line_start = m.end()
                continue
            elif kind == "SKIP":
                continue
            elif kind in ("COMMENT_BLOCK", "COMMENT_LINE"):
                # 如果是条件注释的开头，我们可能需要保留，但在 DDL 解析中注释一般可以被过滤或单独处理
                # 在此保留为 T_COMMENT，以便 Parser 在需要提取表/列注释时进行分析
                self.tokens.append(Token(T_COMMENT, value, line, column))
            elif kind == "STRING":
                self.tokens.append(Token(T_STRING, value, line, column))
            elif kind == "STRING_DOUBLE":
                # 双引号在 SQL 中有时是字符串，有时是引用标识符，这由 Parser 决定。
                # 在这里，我们将有双引号的作为 T_QUOTED_IDENTIFIER
                self.tokens.append(Token(T_QUOTED_IDENTIFIER, value, line, column))
            elif kind == "QUOTED_ID":
                self.tokens.append(Token(T_QUOTED_IDENTIFIER, value, line, column))
            elif kind == "NUMBER":
                self.tokens.append(Token(T_NUMBER, value, line, column))
            elif kind == "PUNCTUATION":
                self.tokens.append(Token(T_PUNCTUATION, value, line, column))
            elif kind == "ID":
                # 检查是否为关键字
                val_upper = value.upper()
                if val_upper in KEYWORDS:
                    self.tokens.append(Token(T_KEYWORD, val_upper, line, column))
                else:
                    self.tokens.append(Token(T_IDENTIFIER, value, line, column))
            elif kind == "MISMATCH":
                # 未匹配字符通常可以作为符号/标识符，不直接崩溃
                self.tokens.append(Token(T_PUNCTUATION, value, line, column))

        # 挂载 EOF Token
        self.tokens.append(Token(T_EOF, "", line, len(self.text) - line_start + 1))

    def iter_tokens(self) -> Iterator[Token]:
        return iter(self.tokens)
