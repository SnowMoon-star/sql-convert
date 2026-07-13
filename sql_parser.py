"""SQL 结构解析器——从 SQL 文本中提取表、列、索引、外键、INSERT 数据。

输入是经过正则规则处理后的 SQL 文本。输出结构化的 TableBlock 列表，
供格式化器按 5 步骤格式输出。
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

from model import ColumnDef, IndexDef, ForeignKeyDef, InsertBlock, TableBlock


# ---------------------------------------------------------------------------
# 正则常量
# ---------------------------------------------------------------------------

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

# 匹配 INSERT INTO `table` (...) VALUES 或 INSERT INTO `table` VALUES
_INSERT_PAT = re.compile(
    r"""
    INSERT\s+INTO\s+
    (?:`(\w+)`|"(\w+)"|(\w+))  # 表名
    \s*(?:\(([^)]*)\))?         # 可选列名列表
    \s*VALUES\s*(.+?);          # VALUES 及值
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)

# 匹配 PRIMARY KEY (cols)
_PK_PAT = re.compile(
    r"""PRIMARY\s+KEY\s*\(([^)]+)\)""",
    re.IGNORECASE,
)

# 匹配 KEY/INDEX name (cols) — 不包含 PRIMARY 和 UNIQUE 和 FOREIGN
_KEY_PAT = re.compile(
    r"""(?:^|\s)KEY\s+(`(\w+)`|"(\w+)"|(\w+))\s*\(([^)]+)\)""",
    re.IGNORECASE,
)
_INDEX_PAT = re.compile(
    r"""(?:^|\s)INDEX\s+(`(\w+)`|"(\w+)"|(\w+))\s*\(([^)]+)\)""",
    re.IGNORECASE,
)

# 匹配 UNIQUE KEY name (cols)
_UNIQUE_KEY_PAT = re.compile(
    r"""UNIQUE\s+KEY\s+(`(\w+)`|"(\w+)"|(\w+))\s*\(([^)]+)\)""",
    re.IGNORECASE,
)
_UNIQUE_INDEX_PAT = re.compile(
    r"""UNIQUE\s+INDEX\s+(`(\w+)`|"(\w+)"|(\w+))\s*\(([^)]+)\)""",
    re.IGNORECASE,
)

# 匹配 FOREIGN KEY (col) REFERENCES table (col) [ON DELETE ...] [ON UPDATE ...]
_FK_INLINE_PAT = re.compile(
    r"""
    (?:CONSTRAINT\s+(`(\w+)`|"(\w+)"|(\w+))\s+)?  # 可选约束名
    FOREIGN\s+KEY\s*\(([^)]+)\)\s*
    REFERENCES\s+(?:`(\w+)`|"(\w+)"|(\w+))\s*\(([^)]+)\)\s*
    (?:ON\s+DELETE\s+(\w+(?:\s+\w+)*))?\s*           # CASCADE / SET NULL / NO ACTION
    (?:ON\s+UPDATE\s+(\w+(?:\s+\w+)*))?              # CASCADE / SET NULL / NO ACTION
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 匹配独立 ALTER TABLE t ADD CONSTRAINT ... FOREIGN KEY ...
_ALTER_FK_PAT = re.compile(
    r"""
    ALTER\s+TABLE\s+(?:`(\w+)`|"(\w+)"|(\w+))\s+
    ADD\s+CONSTRAINT\s+(?:`(\w+)`|"(\w+)"|(\w+))\s+
    FOREIGN\s+KEY\s*\(([^)]+)\)\s*
    REFERENCES\s+(?:`(\w+)`|"(\w+)"|(\w+))\s*\(([^)]+)\)\s*
    (?:ON\s+DELETE\s+(\w+(?:\s+\w+)*))?\s*
    (?:ON\s+UPDATE\s+(\w+(?:\s+\w+)*))?
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 匹配独立 ALTER TABLE t ADD [UNIQUE] KEY/INDEX ...
_ALTER_INDEX_PAT = re.compile(
    r"""
    ALTER\s+TABLE\s+(?:`(\w+)`|"(\w+)"|(\w+))\s+
    ADD\s+(UNIQUE\s+)?(?:KEY|INDEX)\s+
    (?:`(\w+)`|"(\w+)"|(\w+))\s*\(([^)]+)\)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 匹配 DROP TABLE IF EXISTS `name`
_DROP_TABLE_PAT = re.compile(
    r"""DROP\s+TABLE\s+IF\s+EXISTS\s+(?:`(\w+)`|"(\w+)"|(\w+))\s*;""",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

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
    while i < len(body):
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
    while i < len(text):
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


# ---------------------------------------------------------------------------
# 解析函数
# ---------------------------------------------------------------------------

def _parse_columns_and_constraints(body: str, block: TableBlock) -> None:
    """解析 CREATE TABLE body 内的列定义和约束。"""
    parts = _split_by_top_level_commas(body)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        part_upper = part.upper().lstrip()

        # 主键
        if part_upper.startswith('PRIMARY KEY'):
            m = _PK_PAT.search(part)
            if m:
                block.primary_key = _extract_identifiers(m.group(1))
            continue

        # 外键（可能在 CONSTRAINT 或直接 FOREIGN KEY）
        if part_upper.startswith('CONSTRAINT') or part_upper.startswith('FOREIGN KEY'):
            _parse_inline_fk(part, block)
            continue

        # 唯一索引
        if part_upper.startswith('UNIQUE KEY') or part_upper.startswith('UNIQUE INDEX'):
            _parse_inline_index(part, block, unique=True)
            continue

        # 普通索引
        if part_upper.startswith('KEY ') or part_upper.startswith('INDEX '):
            _parse_inline_index(part, block, unique=False)
            continue

        # 检查约束 CHECK
        if part_upper.startswith('CHECK') or part_upper.startswith('CONSTRAINT'):
            # 可能是 constraint 开头但不是 FK（上面已经处理了 FK）
            continue

        # 列定义
        _parse_column_def(part, block)


def _parse_column_def(part: str, block: TableBlock) -> None:
    """解析单个列定义。"""
    m = _COL_START_PAT.match(part)
    if not m:
        return

    name = m.group(1) or m.group(2) or m.group(3)
    # 类型+约束 = 从标识符之后到行尾（或 COMMENT 之前）
    rest = part[m.end():].strip()

    # 提取 COMMENT
    comment = _extract_comment(rest)
    if comment:
        # 从 rest 中移除 COMMENT 部分，保持类型+约束干净
        rest = _COMMENT_PAT.sub('', rest).strip()

    # 类型声明保持原样（已含 NOT NULL, DEFAULT, AUTO_INCREMENT 等）
    block.columns.append(ColumnDef(name=name, type_=rest, comment=comment))


def _parse_inline_fk(part: str, block: TableBlock) -> None:
    """解析 CREATE TABLE 内的外键定义。"""
    m = _FK_INLINE_PAT.search(part)
    if not m:
        return

    # 约束名：group(2) 反引号, group(3) 双引号, group(4) 无引号
    constraint_name = m.group(2) or m.group(3) or m.group(4)
    # 本表字段
    columns = _extract_identifiers(m.group(5))
    # 关联表名：group(6) 反引号, group(7) 双引号, group(8) 无引号
    ref_table = m.group(6) or m.group(7) or m.group(8)
    # 关联字段
    ref_columns = _extract_identifiers(m.group(9))
    on_delete = m.group(10).strip() if m.group(10) else None
    on_update = m.group(11).strip() if m.group(11) else None

    block.foreign_keys.append(ForeignKeyDef(
        name=constraint_name,
        columns=columns,
        ref_table=ref_table,
        ref_columns=ref_columns,
        on_delete=on_delete,
        on_update=on_update,
    ))


def _parse_inline_index(part: str, block: TableBlock, *, unique: bool) -> None:
    """解析 CREATE TABLE 内的索引定义（KEY/INDEX/UNIQUE KEY）。"""
    if unique:
        m = _UNIQUE_KEY_PAT.search(part) or _UNIQUE_INDEX_PAT.search(part)
    else:
        m = _KEY_PAT.search(part) or _INDEX_PAT.search(part)

    if not m:
        return

    # 索引名：反引号/双引号/无引号
    # 对于 UNIQUE: group(2) 反引号, group(3) 双引号, group(4) 无引号
    # 对于 KEY/INDEX: 结构类似
    idx_name = m.group(2) or m.group(3) or m.group(4)
    columns = _extract_identifiers(m.group(5))
    comment = _extract_comment(part)

    block.indexes.append(IndexDef(
        name=idx_name,
        columns=columns,
        unique=unique,
        comment=comment,
    ))


def _parse_inserts(sql: str, table_name: str, block: TableBlock) -> None:
    """提取指定表的所有 INSERT INTO 语句。

    每条 INSERT 独立存储其列名和值行，避免不同 INSERT 之间的列顺序冲突。
    """
    for m in _INSERT_PAT.finditer(sql):
        t_name = m.group(1) or m.group(2) or m.group(3)
        if t_name.lower() != table_name.lower():
            continue

        # 列名列表（本 INSERT 独有）
        cols_str = m.group(4)
        columns = _extract_identifiers(cols_str) if cols_str else []

        # VALUES 部分
        values_str = m.group(5).strip()
        value_rows = _split_insert_values(values_str)

        if value_rows:
            block.inserts.append(InsertBlock(columns=columns, values=value_rows))


def _split_insert_values(values_str: str) -> list[list[str]]:
    """将 INSERT VALUES 部分解析为二维值列表。

    处理多行格式: (v1, v2),\n(v3, v4)。
    使用 while 循环以支持转义字符双步跳跃（i += 2），
    避免 `\'` 等转义序列错误翻转引号状态。
    """
    rows: list[list[str]] = []
    depth = 0
    in_single = False
    in_double = False
    start = -1

    i = 0
    while i < len(values_str):
        ch = values_str[i]

        # 转义字符：跳过自身及下一个字符，防止 \' 翻转引号状态
        if ch == '\\' and (in_single or in_double):
            i += 2
            continue

        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == '(' and not in_single and not in_double:
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == ')' and not in_single and not in_double:
            depth -= 1
            if depth == 0 and start >= 0:
                row_str = values_str[start:i]
                rows.append(_parse_value_row(row_str))
                start = -1

        i += 1

    return rows


def _parse_value_row(row_str: str) -> list[str]:
    """解析单行值列表 (v1, v2, ...)，处理引号和转义。"""
    values: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    i = 0

    while i < len(row_str):
        ch = row_str[i]

        if ch == '\\' and in_single:
            # MySQL 转义：\' 等
            current.append(ch)
            if i + 1 < len(row_str):
                current.append(row_str[i + 1])
                i += 2
                continue

        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
        elif ch == ',' and not in_single and not in_double:
            val = ''.join(current).strip()
            values.append(val)
            current = []
        else:
            current.append(ch)

        i += 1

    # 最后一个值
    val = ''.join(current).strip()
    if val:
        values.append(val)

    return values


# 匹配 COMMENT ON TABLE "xxx" IS 'yyy'
_COMMENT_ON_TABLE_PAT = re.compile(
    r"""COMMENT\s+ON\s+TABLE\s+(?:`(\w+)`|"(\w+)"|(\w+))\s+IS\s+'([^']*)'\s*;?""",
    re.IGNORECASE | re.DOTALL,
)

# 匹配 COMMENT ON COLUMN "xxx"."yyy" IS 'zzz'
_COMMENT_ON_COL_PAT = re.compile(
    r"""COMMENT\s+ON\s+COLUMN\s+(?:`(\w+)`|"(\w+)"|(\w+))\s*\.\s*(?:`(\w+)`|"(\w+)"|(\w+))\s+IS\s+'([^']*)'\s*;?""",
    re.IGNORECASE | re.DOTALL,
)


def _parse_comment_on(sql: str, table_map: dict[str, TableBlock]) -> None:
    """解析 COMMENT ON TABLE / COMMENT ON COLUMN 语句，补充注释到 TableBlock。"""
    # 表注释
    for m in _COMMENT_ON_TABLE_PAT.finditer(sql):
        table_name = m.group(1) or m.group(2) or m.group(3)
        comment = m.group(4)
        if table_name in table_map:
            table_map[table_name].comment = comment

    # 列注释
    for m in _COMMENT_ON_COL_PAT.finditer(sql):
        table_name = m.group(1) or m.group(2) or m.group(3)
        col_name = m.group(4) or m.group(5) or m.group(6)
        comment = m.group(7)
        if table_name in table_map:
            for col in table_map[table_name].columns:
                if col.name == col_name:
                    col.comment = comment
                    break


def _parse_standalone_fks(sql: str, table_map: dict[str, TableBlock]) -> None:
    """解析独立的 ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY 语句。"""
    for m in _ALTER_FK_PAT.finditer(sql):
        t_name = m.group(1) or m.group(2) or m.group(3)
        if t_name not in table_map:
            continue

        constraint_name = m.group(4) or m.group(5) or m.group(6)
        columns = _extract_identifiers(m.group(7))
        ref_table = m.group(8) or m.group(9) or m.group(10)
        ref_columns = _extract_identifiers(m.group(11))
        on_delete = m.group(12).strip() if m.group(12) else None
        on_update = m.group(13).strip() if m.group(13) else None

        table_map[t_name].foreign_keys.append(ForeignKeyDef(
            name=constraint_name,
            columns=columns,
            ref_table=ref_table,
            ref_columns=ref_columns,
            on_delete=on_delete,
            on_update=on_update,
        ))


def _parse_standalone_indexes(sql: str, table_map: dict[str, TableBlock]) -> None:
    """解析独立的 ALTER TABLE ... ADD [UNIQUE] KEY/INDEX 语句。"""
    for m in _ALTER_INDEX_PAT.finditer(sql):
        t_name = m.group(1) or m.group(2) or m.group(3)
        if t_name not in table_map:
            continue

        unique = m.group(4) is not None
        idx_name = m.group(5) or m.group(6) or m.group(7)
        columns = _extract_identifiers(m.group(8))

        table_map[t_name].indexes.append(IndexDef(
            name=idx_name,
            columns=columns,
            unique=unique,
            comment=None,
        ))


# ---------------------------------------------------------------------------
# 主解析入口
# ---------------------------------------------------------------------------

def _parse_orphan_tables(
    sql: str,
    table_map: dict[str, TableBlock],
    tables: list[TableBlock],
    database: str | None,
) -> None:
    """查找没有 DROP TABLE 的孤儿 CREATE TABLE 语句，追加到 tables 中。"""
    pos = 0
    known = {n.lower() for n in table_map}

    while True:
        m = _CREATE_TABLE_PAT.search(sql, pos)
        if not m:
            break

        table_name = m.group(1) or m.group(2) or m.group(3)
        if table_name.lower() in known:
            pos = m.end()
            continue

        # 找到这个 CREATE TABLE 的块范围
        paren_start = sql.find('(', m.end() - 1)
        if paren_start == -1:
            pos = m.end()
            continue

        paren_end = _find_matching_paren(sql, paren_start)
        if paren_end == -1:
            pos = m.end()
            continue

        # 块结束于分号
        create_end = paren_end + 1
        semi_pos = sql.find(';', create_end)
        if semi_pos != -1:
            create_end = semi_pos + 1

        # 找到下一个语句作为块边界（下一个 CREATE TABLE 或 DROP TABLE）
        next_boundary = len(sql)
        for pat in [_CREATE_TABLE_PAT, _DROP_TABLE_PAT]:
            nm = pat.search(sql, create_end)
            if nm and nm.start() < next_boundary:
                next_boundary = nm.start()

        block_sql = sql[m.start():next_boundary]
        table_body = sql[paren_start + 1:paren_end]

        block = TableBlock(database=database, name=table_name, comment=None)

        after_paren = sql[paren_end + 1:semi_pos] if semi_pos != -1 else ""
        tc_m = _TABLE_COMMENT_PAT.search(after_paren)
        if tc_m:
            block.comment = tc_m.group(2)

        _parse_columns_and_constraints(table_body, block)
        _parse_inserts(block_sql, table_name, block)

        tables.append(block)
        table_map[table_name] = block
        known.add(table_name.lower())
        pos = create_end


def parse_tables(sql: str, database: str | None = None) -> list[TableBlock]:
    """解析 SQL 文本，返回所有表的结构化信息。

    以 DROP TABLE IF EXISTS 为块边界分割文本，每块内解析：
    1. CREATE TABLE 语句 → 提取表结构、列、主键、内联索引、内联外键
    2. INSERT INTO 语句 → 提取数据（仅限该块内）
    3. ALTER TABLE 语句 → 提取独立索引和外键

    块外的 INSERT 数据（如 LOCK TABLES 块中的数据）会被忽略，
    避免数据重复和归属错误。
    """
    tables: list[TableBlock] = []
    table_map: dict[str, TableBlock] = {}

    # 找到所有 DROP TABLE IF EXISTS 位置作为块边界
    drop_matches = list(_DROP_TABLE_PAT.finditer(sql))

    if drop_matches:
        # 有 DROP TABLE：按块分割
        blocks: list[tuple[int, int, str | None]] = []  # (start, end, table_name)
        for i, dm in enumerate(drop_matches):
            name = dm.group(1) or dm.group(2) or dm.group(3)
            start = dm.start()
            end = drop_matches[i + 1].start() if i + 1 < len(drop_matches) else len(sql)
            blocks.append((start, end, name))

        for block_start, block_end, drop_table_name in blocks:
            block_sql = sql[block_start:block_end]

            # 在该块内找 CREATE TABLE
            ct_m = _CREATE_TABLE_PAT.search(block_sql)
            if not ct_m:
                continue

            table_name = ct_m.group(1) or ct_m.group(2) or ct_m.group(3)
            paren_start = block_sql.find('(', ct_m.end() - 1)
            if paren_start == -1:
                continue

            paren_end = _find_matching_paren(block_sql, paren_start)
            if paren_end == -1:
                continue

            # CREATE TABLE 结束位置
            create_end = paren_end + 1
            semi_pos = block_sql.find(';', create_end)
            if semi_pos != -1:
                create_end = semi_pos + 1

            table_body = block_sql[paren_start + 1:paren_end]

            block = TableBlock(database=database, name=table_name, comment=None)

            # 表 COMMENT
            after_paren = block_sql[paren_end + 1:semi_pos] if semi_pos != -1 else block_sql[paren_end + 1:create_end]
            tc_m = _TABLE_COMMENT_PAT.search(after_paren)
            if tc_m:
                block.comment = tc_m.group(2)

            # 解析列和约束
            _parse_columns_and_constraints(table_body, block)

            # 只在该块内提取 INSERT 数据
            _parse_inserts(block_sql, table_name, block)

            if table_name not in table_map:
                tables.append(block)
                table_map[table_name] = block

        # 第二遍：查找没有 DROP TABLE 的孤儿 CREATE TABLE
        _parse_orphan_tables(sql, table_map, tables, database)

    else:
        # 无 DROP TABLE：按 CREATE TABLE 位置分割
        pos = 0
        ct_matches: list[re.Match] = []
        while True:
            m = _CREATE_TABLE_PAT.search(sql, pos)
            if not m:
                break
            ct_matches.append(m)
            pos = m.end()

        # 确定每个 CREATE TABLE 的块范围
        for i, m in enumerate(ct_matches):
            table_name = m.group(1) or m.group(2) or m.group(3)
            block_start = m.start()
            block_end = ct_matches[i + 1].start() if i + 1 < len(ct_matches) else len(sql)
            block_sql = sql[block_start:block_end]

            paren_start = block_sql.find('(', m.end() - block_start - 1)
            if paren_start == -1:
                paren_start = block_sql.find('(')

            if paren_start == -1:
                continue

            paren_end = _find_matching_paren(block_sql, paren_start)
            if paren_end == -1:
                continue

            create_end = paren_end + 1
            semi_pos = block_sql.find(';', create_end)
            if semi_pos != -1:
                create_end = semi_pos + 1

            table_body = block_sql[paren_start + 1:paren_end]

            block = TableBlock(database=database, name=table_name, comment=None)

            after_paren = block_sql[paren_end + 1:semi_pos] if semi_pos != -1 else block_sql[paren_end + 1:create_end]
            tc_m = _TABLE_COMMENT_PAT.search(after_paren)
            if tc_m:
                block.comment = tc_m.group(2)

            _parse_columns_and_constraints(table_body, block)
            _parse_inserts(block_sql, table_name, block)

            if table_name not in table_map:
                tables.append(block)
                table_map[table_name] = block

    _parse_standalone_fks(sql, table_map)
    _parse_standalone_indexes(sql, table_map)
    _parse_comment_on(sql, table_map)

    return tables


def parse_statement_to_schema(
    sql: str,
    table_map: dict[str, TableBlock],
    tables: list[TableBlock],
    database: str | None = None,
) -> None:
    """流式解析单条 DDL/DML/COMMENT 语句并更新到 table_map/tables 中。"""
    # 1. 查找 CREATE TABLE
    ct_m = _CREATE_TABLE_PAT.search(sql)
    if ct_m:
        table_name = ct_m.group(1) or ct_m.group(2) or ct_m.group(3)
        paren_start = sql.find('(', ct_m.end() - 1)
        if paren_start == -1:
            paren_start = sql.find('(')
        if paren_start != -1:
            paren_end = _find_matching_paren(sql, paren_start)
            if paren_end != -1:
                table_body = sql[paren_start + 1:paren_end]
                block = TableBlock(database=database, name=table_name, comment=None)

                # 表 COMMENT
                semi_pos = sql.find(';', paren_end + 1)
                after_paren = sql[paren_end + 1:semi_pos] if semi_pos != -1 else sql[paren_end + 1:]
                tc_m = _TABLE_COMMENT_PAT.search(after_paren)
                if tc_m:
                    block.comment = tc_m.group(2)

                _parse_columns_and_constraints(table_body, block)

                if table_name not in table_map:
                    tables.append(block)
                    table_map[table_name] = block
        return

    # 2. 其他独立约束/索引/注释语句（会对已解析的表结构做追加或修改）
    _parse_standalone_fks(sql, table_map)
    _parse_standalone_indexes(sql, table_map)
    _parse_comment_on(sql, table_map)



# ---------------------------------------------------------------------------
# FK 依赖排序
# ---------------------------------------------------------------------------

def _topological_sort(deps: dict[str, list[str]]) -> list[str]:
    """Kahn 拓扑排序：deps[name] = [该表所依赖的其他表]。

    返回表名列表，无依赖者在前。循环依赖或外部引用时保持原顺序。
    使用 deque.popleft() 代替 list.pop(0)，将队列操作从 O(n) 降为 O(1)。
    """
    # 入度
    in_degree: dict[str, int] = {name: 0 for name in deps}
    dependents: dict[str, list[str]] = {name: [] for name in deps}

    for name, refs in deps.items():
        for ref in refs:
            if ref in deps:
                dependents.setdefault(ref, [])
                dependents[ref].append(name)
                in_degree[name] += 1

    # 入度为 0 的入队（deque 保证 popleft 为 O(1)）
    queue: deque[str] = deque(n for n, d in in_degree.items() if d == 0)
    result: list[str] = []

    while queue:
        name = queue.popleft()
        result.append(name)
        for dependent in dependents.get(name, []):
            if dependent in in_degree:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

    # 循环依赖或外部引用：保持原顺序追加
    for name in deps:
        if name not in result:
            result.append(name)

    return result


def sort_tables_by_fk(tables: list[TableBlock]) -> list[TableBlock]:
    """按 FK 依赖排序表，只考虑当前 SQL 中存在的表间依赖。

    - 全部无外键 → 保持原始顺序
    - FK 引用外部表（不在当前 SQL 中）→ 视为已满足的依赖，忽略
    - FK 引用内部表 → 被引用表先输出
    - 循环依赖 → 降级保持原顺序
    """
    if not tables:
        return tables

    known_names = {t.name.lower() for t in tables}

    # 构建 deps：只计算引用目标在已知表集合中的 FK
    deps: dict[str, list[str]] = {}
    for t in tables:
        refs: list[str] = []
        for fk in t.foreign_keys:
            if fk.ref_table.lower() in known_names:
                refs.append(fk.ref_table.lower())
        deps[t.name.lower()] = list(set(refs))

    # 无内部依赖 → 保持原顺序
    if not any(deps.values()):
        return tables

    sorted_names = _topological_sort(deps)
    name_to_table = {t.name.lower(): t for t in tables}
    return [name_to_table[n] for n in sorted_names if n in name_to_table]
