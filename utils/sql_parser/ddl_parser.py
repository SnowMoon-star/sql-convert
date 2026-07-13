"""基于 Lexer Token 流的手写 SQL DDL 解析器 — 摆脱正则，更健壮地解析表、列、索引和约束。"""
from __future__ import annotations
import re
from pathlib import Path
from model import ColumnDef, IndexDef, ForeignKeyDef, TableBlock

from utils.sql_parser.lexer import (
    Lexer, Token, T_KEYWORD, T_IDENTIFIER, T_QUOTED_IDENTIFIER,
    T_STRING, T_NUMBER, T_PUNCTUATION, T_COMMENT, T_EOF
)


def clean_id(val: str) -> str:
    """去除标识符外侧的引号或反引号。"""
    return val.strip('"``').strip()


def reconstruct_type(parts: list[str]) -> str:
    """智能拼接列类型及其修饰 Token，消除小括号和逗号前后的冗余空格。"""
    res = []
    for val in parts:
        if not res:
            res.append(val)
            continue
        prev = res[-1]
        if val in ("(", ")", ",", ".") or prev in ("(", ".", ","):
            res.append(val)
        else:
            res.append(" " + val)
    return "".join(res)


class TokenStream:
    """轻量级 Token 流辅助类。"""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        if self.pos + offset >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos + offset]

    def consume(self) -> Token:
        t = self.peek()
        self.pos += 1
        return t

    def match(self, type_name: str, value: str | None = None) -> bool:
        t = self.peek()
        if t.type == type_name:
            if value is None or t.value.upper() == value.upper():
                self.pos += 1
                return True
        return False

    def is_eof(self) -> bool:
        return self.peek().type == T_EOF or self.pos >= len(self.tokens)


def _collect_identifiers_in_parens(stream: TokenStream) -> list[str]:
    """收集括号内的标识符列表，并能正确处理和剥离嵌套小括号（如列前缀长度(10)）与 ASC/DESC 关键字。"""
    ids = []
    if not stream.match(T_PUNCTUATION, "("):
        return ids

    seg_tokens: list[list[Token]] = []
    current_seg: list[Token] = []
    paren_depth = 1

    while not stream.is_eof():
        tok = stream.consume()
        if tok.type == T_PUNCTUATION and tok.value == "(":
            paren_depth += 1
            current_seg.append(tok)
        elif tok.type == T_PUNCTUATION and tok.value == ")":
            paren_depth -= 1
            if paren_depth == 0:
                if current_seg:
                    seg_tokens.append(current_seg)
                break
            current_seg.append(tok)
        elif tok.type == T_PUNCTUATION and tok.value == "," and paren_depth == 1:
            if current_seg:
                seg_tokens.append(current_seg)
                current_seg = []
        else:
            current_seg.append(tok)

    for seg in seg_tokens:
        for t in seg:
            if t.type in (T_IDENTIFIER, T_QUOTED_IDENTIFIER):
                ids.append(clean_id(t.value))
                break
    return ids


def _parse_create_table_body(body_tokens: list[Token], block: TableBlock) -> None:
    """解析建表语句括号内部的字段和约束。"""
    # 按最外层的逗号进行切分段
    segments: list[list[Token]] = []
    current_seg: list[Token] = []
    paren_depth = 0

    for tok in body_tokens:
        if tok.type == T_PUNCTUATION and tok.value == "(":
            paren_depth += 1
            current_seg.append(tok)
        elif tok.type == T_PUNCTUATION and tok.value == ")":
            paren_depth -= 1
            current_seg.append(tok)
        elif tok.type == T_PUNCTUATION and tok.value == "," and paren_depth == 0:
            if current_seg:
                segments.append(current_seg)
                current_seg = []
        else:
            current_seg.append(tok)
    if current_seg:
        segments.append(current_seg)

    # 依次解析每段
    for seg in segments:
        stream = TokenStream(seg)
        if stream.is_eof():
            continue

        # 1. 主键
        if stream.match(T_KEYWORD, "PRIMARY"):
            if stream.match(T_KEYWORD, "KEY"):
                block.primary_key = _collect_identifiers_in_parens(stream)
            continue

        # 2. 外键或 CONSTRAINT
        is_fk = False
        constraint_name = None
        if stream.match(T_KEYWORD, "CONSTRAINT"):
            t_name = stream.consume()
            if t_name.type in (T_IDENTIFIER, T_QUOTED_IDENTIFIER):
                constraint_name = clean_id(t_name.value)
            is_fk = True

        if stream.match(T_KEYWORD, "FOREIGN") and stream.match(T_KEYWORD, "KEY"):
            is_fk = True

        if is_fk:
            # 提取外键字段
            columns = _collect_identifiers_in_parens(stream)
            # 提取引用的表与字段
            if stream.match(T_KEYWORD, "REFERENCES"):
                ref_tbl_tok = stream.consume()
                ref_table = clean_id(ref_tbl_tok.value)
                ref_columns = _collect_identifiers_in_parens(stream)

                on_delete = None
                on_update = None
                # 解析 ON DELETE / ON UPDATE
                while not stream.is_eof():
                    if stream.match(T_KEYWORD, "ON"):
                        if stream.match(T_KEYWORD, "DELETE"):
                            act_toks = []
                            while not stream.is_eof() and stream.peek().type == T_KEYWORD:
                                act_toks.append(stream.consume().value)
                            on_delete = " ".join(act_toks) if act_toks else None
                        elif stream.match(T_KEYWORD, "UPDATE"):
                            act_toks = []
                            while not stream.is_eof() and stream.peek().type == T_KEYWORD:
                                act_toks.append(stream.consume().value)
                            on_update = " ".join(act_toks) if act_toks else None
                        else:
                            break
                    else:
                        stream.consume()

                block.foreign_keys.append(ForeignKeyDef(
                    name=constraint_name,
                    columns=columns,
                    ref_table=ref_table,
                    ref_columns=ref_columns,
                    on_delete=on_delete,
                    on_update=on_update
                ))
            continue

        # 3. 索引段
        is_index = False
        is_unique = False
        stream.pos = 0  # 重置以便识别开头
        
        if stream.match(T_KEYWORD, "UNIQUE"):
            is_unique = True
            if stream.match(T_KEYWORD, "KEY") or stream.match(T_KEYWORD, "INDEX"):
                is_index = True
        elif stream.match(T_KEYWORD, "KEY") or stream.match(T_KEYWORD, "INDEX"):
            is_index = True

        if is_index:
            idx_name_tok = stream.consume()
            idx_name = clean_id(idx_name_tok.value)
            columns = _collect_identifiers_in_parens(stream)

            idx_comment = None
            while not stream.is_eof():
                if stream.match(T_KEYWORD, "COMMENT"):
                    cmt_tok = stream.consume()
                    if cmt_tok.type in (T_STRING, T_QUOTED_IDENTIFIER):
                        idx_comment = cmt_tok.value.strip("'\"")
                else:
                    stream.consume()

            block.indexes.append(IndexDef(
                name=idx_name,
                columns=columns,
                unique=is_unique,
                comment=idx_comment
            ))
            continue

        # 4. 普通列定义
        stream.pos = 0
        col_name_tok = stream.consume()
        col_name = clean_id(col_name_tok.value)

        type_parts = []
        comment = None
        while not stream.is_eof():
            if stream.match(T_KEYWORD, "COMMENT"):
                cmt_tok = stream.consume()
                if cmt_tok.type in (T_STRING, T_QUOTED_IDENTIFIER):
                    comment = cmt_tok.value.strip("'\"")
            else:
                type_parts.append(stream.consume().value)

        block.columns.append(ColumnDef(
            name=col_name,
            type_=reconstruct_type(type_parts),
            comment=comment
        ))


def parse_statement_to_schema(
    sql: str,
    table_map: dict[str, TableBlock],
    tables: list[TableBlock],
    database: str | None = None,
) -> None:
    """流式解析单条 DDL/DML/COMMENT 语句，并在此阶段利用 Token AST 对模型补充更新。"""
    lexer = Lexer(sql)
    stream = TokenStream(lexer.tokens)

    # 1. CREATE TABLE 解析
    if stream.match(T_KEYWORD, "CREATE") and stream.match(T_KEYWORD, "TABLE"):
        stream.match(T_KEYWORD, "IF")  # 略过 IF NOT EXISTS
        stream.match(T_KEYWORD, "NOT")
        stream.match(T_KEYWORD, "EXISTS")

        tbl_tok = stream.consume()
        table_name = clean_id(tbl_tok.value)

        # 进入主建表括号
        if stream.match(T_PUNCTUATION, "("):
            body_tokens = []
            paren_depth = 1
            while not stream.is_eof():
                tok = stream.consume()
                if tok.type == T_PUNCTUATION and tok.value == "(":
                    paren_depth += 1
                elif tok.type == T_PUNCTUATION and tok.value == ")":
                    paren_depth -= 1
                    if paren_depth == 0:
                        break
                body_tokens.append(tok)

            block = TableBlock(database=database, name=table_name, comment=None)
            _parse_create_table_body(body_tokens, block)

            # 解析建表括号外侧的选项 (如 ENGINE, COMMENT, DEFAULT CHARSET)
            while not stream.is_eof():
                if stream.match(T_KEYWORD, "COMMENT"):
                    # 支持 COMMENT = 'xxx' 或 COMMENT 'xxx'
                    stream.match(T_PUNCTUATION, "=")
                    cmt_tok = stream.consume()
                    if cmt_tok.type in (T_STRING, T_QUOTED_IDENTIFIER):
                        block.comment = cmt_tok.value.strip("'\"")
                elif stream.match(T_KEYWORD, "ENGINE"):
                    stream.match(T_PUNCTUATION, "=")
                    stream.consume()  # 跳过 engine 名
                elif stream.match(T_KEYWORD, "DEFAULT") or stream.match(T_KEYWORD, "CHARSET"):
                    # 忽略
                    stream.consume()
                else:
                    stream.consume()

            if table_name not in table_map:
                tables.append(block)
                table_map[table_name] = block
        return

    # 2. ALTER TABLE ADD CONSTRAINT FOREIGN KEY 解析
    if stream.match(T_KEYWORD, "ALTER") and stream.match(T_KEYWORD, "TABLE"):
        tbl_tok = stream.consume()
        table_name = clean_id(tbl_tok.value)

        if stream.match(T_KEYWORD, "ADD"):
            constraint_name = None
            if stream.match(T_KEYWORD, "CONSTRAINT"):
                c_tok = stream.consume()
                constraint_name = clean_id(c_tok.value)

            if stream.match(T_KEYWORD, "FOREIGN") and stream.match(T_KEYWORD, "KEY"):
                columns = _collect_identifiers_in_parens(stream)
                if stream.match(T_KEYWORD, "REFERENCES"):
                    ref_tbl_tok = stream.consume()
                    ref_table = clean_id(ref_tbl_tok.value)
                    ref_columns = _collect_identifiers_in_parens(stream)

                    on_delete = None
                    on_update = None
                    while not stream.is_eof():
                        if stream.match(T_KEYWORD, "ON"):
                            if stream.match(T_KEYWORD, "DELETE"):
                                act = []
                                while not stream.is_eof() and stream.peek().type == T_KEYWORD:
                                    act.append(stream.consume().value)
                                on_delete = " ".join(act) if act else None
                            elif stream.match(T_KEYWORD, "UPDATE"):
                                act = []
                                while not stream.is_eof() and stream.peek().type == T_KEYWORD:
                                    act.append(stream.consume().value)
                                on_update = " ".join(act) if act else None
                            else:
                                break
                        else:
                            stream.consume()

                    if table_name in table_map:
                        table_map[table_name].foreign_keys.append(ForeignKeyDef(
                            name=constraint_name,
                            columns=columns,
                            ref_table=ref_table,
                            ref_columns=ref_columns,
                            on_delete=on_delete,
                            on_update=on_update
                        ))
            
            # 3. ALTER TABLE ADD [UNIQUE] KEY/INDEX 解析
            else:
                stream.pos = 0  # 重定位到 ALTER TABLE name
                stream.match(T_KEYWORD, "ALTER")
                stream.match(T_KEYWORD, "TABLE")
                stream.consume()
                stream.match(T_KEYWORD, "ADD")

                is_unique = False
                is_index = False
                if stream.match(T_KEYWORD, "UNIQUE"):
                    is_unique = True

                if stream.match(T_KEYWORD, "KEY") or stream.match(T_KEYWORD, "INDEX"):
                    is_index = True

                if is_index:
                    idx_name_tok = stream.consume()
                    idx_name = clean_id(idx_name_tok.value)
                    columns = _collect_identifiers_in_parens(stream)

                    if table_name in table_map:
                        table_map[table_name].indexes.append(IndexDef(
                            name=idx_name,
                            columns=columns,
                            unique=is_unique,
                            comment=None
                        ))
        return

    # 4. COMMENT ON TABLE / COLUMN 解析
    if stream.match(T_KEYWORD, "COMMENT") and stream.match(T_KEYWORD, "ON"):
        if stream.match(T_KEYWORD, "TABLE"):
            tbl_tok = stream.consume()
            table_name = clean_id(tbl_tok.value)
            if stream.match(T_KEYWORD, "IS"):
                cmt_tok = stream.consume()
                comment = cmt_tok.value.strip("'\"")
                if table_name in table_map:
                    table_map[table_name].comment = comment
        elif stream.match(T_KEYWORD, "COLUMN"):
            # COMMENT ON COLUMN tbl.col IS 'cmt'
            col_full_tok = stream.consume()
            parts = col_full_tok.value.split(".")
            if len(parts) == 2:
                table_name = clean_id(parts[0])
                col_name = clean_id(parts[1])
            else:
                # 兼容被 Lexer 分离为 PUNCTUATION "." 的场景
                table_name = clean_id(col_full_tok.value)
                if stream.match(T_PUNCTUATION, "."):
                    col_tok = stream.consume()
                    col_name = clean_id(col_tok.value)
                else:
                    return

            if stream.match(T_KEYWORD, "IS"):
                cmt_tok = stream.consume()
                comment = cmt_tok.value.strip("'\"")
                if table_name in table_map:
                    for col in table_map[table_name].columns:
                        if col.name == col_name:
                            col.comment = comment
                            break
        return


def parse_tables(sql: str, database: str | None = None) -> list[TableBlock]:
    """批量解析 DDL 脚本文件内容，兼容 E2E 和原有测试套件。"""
    tables: list[TableBlock] = []
    table_map: dict[str, TableBlock] = {}

    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as f:
        f.write(sql)
        tmp_path = Path(f.name)

    try:
        from reader.sql_reader import SQLReader
        reader = SQLReader(tmp_path)
        for stmt in reader.iter_statements():
            parse_statement_to_schema(stmt.text, table_map, tables, database)
    finally:
        tmp_path.unlink(missing_ok=True)

    return tables
