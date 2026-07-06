"""SQL 方言转换器——在不同数据库之间转换 SQL 文件。

用法：
    python convert.py <input.sql> [-o OUTPUT]
                                  [--source-mode {mysql,...}] [--target-mode {kingbase,...}]
                                  [--encoding ENC] [--overwrite] [-v]

默认输出：<input 主名>_convert.<扩展>，同目录。
"""

import argparse
import os
import re
import sys
from pathlib import Path

from rules import RULES
from sql_parser import parse_tables, sort_tables_by_fk

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_RUNTIME = 3


def default_output_path(input_path: Path) -> Path:
    """在 input 同目录生成 <主名>_convert.<扩展>；无扩展名则直接追加 _convert。"""
    stem = input_path.stem
    suffix = input_path.suffix
    return input_path.with_name(f"{stem}_convert{suffix}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在不同数据库之间转换 SQL 文件"
    )
    parser.add_argument("input", help="待转换的 .sql 文件路径")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出文件路径；缺省为 <input 主名>_convert.<扩展>",
    )
    parser.add_argument(
        "--source-mode",
        default="mysql",
        help="源数据库类型，默认 mysql",
    )
    parser.add_argument(
        "--target-mode",
        default="kingbase",
        help="目标数据库类型，默认 kingbase",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="读写文件编码，默认 utf-8",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="输出文件已存在时是否覆盖",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="打印每条规则命中次数",
    )
    parser.add_argument(
        "--database",
        default=None,
        help="数据库名，用于输出中的表标识符 `数据库名`.`表名`",
    )
    return parser.parse_args(argv)


def is_insert_line(line: str) -> bool:
    """判断一行是否为 INSERT 数据行（大小写不敏感）。"""
    return line.lstrip()[:11].upper().startswith("INSERT INTO")


def filter_rules(source_mode: str, target_mode: str) -> list[dict]:
    """返回适用 source_mode → target_mode 的规则子集。

    规则 source_mode=["*"] 或 target_mode=["*"] 表示通配。
    """
    filtered: list[dict] = []
    for rule in RULES:
        src_ok = rule["source_mode"] == ["*"] or source_mode in rule["source_mode"]
        tgt_ok = rule["target_mode"] == ["*"] or target_mode in rule["target_mode"]
        if src_ok and tgt_ok:
            filtered.append(rule)
    return filtered


# ---------------------------------------------------------------------------
# 规则应用
# ---------------------------------------------------------------------------


def apply_global_rules(text: str, counters: dict[str, int], rules: list[dict]) -> str:
    """对整段文本依次应用所有 scope=global 规则。"""
    for rule in rules:
        if rule["scope"] != "global":
            continue
        pattern: re.Pattern = rule["pattern"]
        replacement = rule["replacement"]
        new_text, n = pattern.subn(replacement, text)
        counters[rule["name"]] = counters.get(rule["name"], 0) + n
        text = new_text
    return text


def apply_line_rules(text: str, counters: dict[str, int], rules: list[dict]) -> str:
    """按行应用所有 scope=line 规则；INSERT 行按 skip_insert 跳过。"""
    line_rules = [r for r in rules if r["scope"] == "line"]
    if not line_rules:
        return text

    out_lines: list[str] = []
    # splitlines(keepends=True) 保留原有换行，避免结尾丢换行或多加
    for line in text.splitlines(keepends=True):
        skip_because_insert = is_insert_line(line)
        for rule in line_rules:
            if skip_because_insert and rule["skip_insert"]:
                continue
            pattern: re.Pattern = rule["pattern"]
            new_line, n = pattern.subn(rule["replacement"], line)
            counters[rule["name"]] = counters.get(rule["name"], 0) + n
            line = new_line
        out_lines.append(line)
    return "".join(out_lines)


# ---------------------------------------------------------------------------
# 结构化输出格式化
# ---------------------------------------------------------------------------


def _escape_comment(text: str) -> str:
    """转义注释文本中的特殊字符（单引号、各类换行符）。

    处理实际控制字符和字面转义序列（如源数据中已转义的 \\r\\n）。
    """
    # 单引号转义
    text = text.replace("'", "\\'")
    # 实际换行控制字符
    text = text.replace("\r\n", " ")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    # 字面转义序列（如 "abc\r\ndef" 在源 SQL 中可能是字面字符串）
    text = text.replace("\\r\\n", " ")
    text = text.replace("\\n", " ")
    text = text.replace("\\r", " ")
    return text


def _table_label(table) -> str:
    """生成带数据库名的表标识符用于注释头。"""
    if table.database:
        return f"`{table.database}`.`{table.name}`"
    return f"`{table.name}`"


def format_structured_output(tables: list) -> str:
    """将解析后的表列表格式化为 5 步骤结构化 SQL 输出。"""
    parts: list[str] = []

    for table in tables:
        label = _table_label(table)
        parts.append("-- ============================================")
        parts.append(f"-- 表名: {label} 开始")
        parts.append("-- ============================================")
        parts.append("")

        # 步骤1: 删除旧表
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤1: 删除旧表")
        parts.append("-- --------------------------------------------")
        parts.append(f"DROP TABLE IF EXISTS `{table.name}` CASCADE;")
        parts.append("")

        # 步骤2: 表结构
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤2: 表结构")
        parts.append("-- --------------------------------------------")
        _format_create_table(table, parts)

        # 步骤3: 索引
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤3: 索引")
        parts.append("-- --------------------------------------------")
        _format_indexes(table, parts)

        # 步骤4: 外键
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤4: 外键")
        parts.append("-- --------------------------------------------")
        _format_foreign_keys(table, parts)

        # 步骤5: 数据导入
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤5: 数据导入")
        parts.append("-- --------------------------------------------")
        _format_inserts(table, parts)

        parts.append("")
        parts.append("-- ============================================")
        parts.append(f"-- 表名: {label} 结束")
        parts.append("-- ============================================")
        parts.append("")

    return "\n".join(parts)


def _format_create_table(table, parts: list[str]) -> None:
    """格式化 CREATE TABLE 语句。"""
    lines: list[str] = []
    lines.append(f"CREATE TABLE `{table.name}` (")

    # 列定义
    col_lines: list[str] = []
    for col in table.columns:
        col_str = f"  `{col.name}` {col.type_}"
        if col.comment:
            col_str += f" COMMENT '{_escape_comment(col.comment)}'"
        col_lines.append(col_str)

    # 主键
    if table.primary_key:
        pk_cols = ", ".join(f"`{c}`" for c in table.primary_key)
        col_lines.append(f"  PRIMARY KEY ({pk_cols})")

    lines.append(",\n".join(col_lines))
    lines.append(")")
    if table.comment:
        lines[-1] += f" COMMENT='{_escape_comment(table.comment)}'"
    lines[-1] += ";"

    parts.extend(lines)
    parts.append("")


def _format_indexes(table, parts: list[str]) -> None:
    """格式化索引为 ALTER TABLE 语句。主键已在 CREATE TABLE 中，此处只输出额外索引。"""
    extra_indexes = table.indexes

    if not extra_indexes:
        parts.append("-- 无额外索引")
        parts.append("")
        return

    for idx in extra_indexes:
        key_type = "UNIQUE KEY" if idx.unique else "KEY"
        cols = ", ".join(f"`{c}`" for c in idx.columns)
        stmt = f"ALTER TABLE `{table.name}` ADD {key_type} `{idx.name}` ({cols})"
        if idx.comment:
            stmt += f" COMMENT '{_escape_comment(idx.comment)}'"
        stmt += ";"
        parts.append(stmt)
    parts.append("")


def _format_foreign_keys(table, parts: list[str]) -> None:
    """格式化外键为 ALTER TABLE 语句。"""
    if not table.foreign_keys:
        parts.append("-- 无外键")
        parts.append("")
        return

    for fk in table.foreign_keys:
        cols = ", ".join(f"`{c}`" for c in fk.columns)
        ref_cols = ", ".join(f"`{c}`" for c in fk.ref_columns)
        stmt = (
            f"ALTER TABLE `{table.name}` ADD CONSTRAINT `{fk.name or 'fk_' + table.name}` "
            f"FOREIGN KEY ({cols}) REFERENCES `{fk.ref_table}` ({ref_cols})"
        )
        if fk.on_delete:
            stmt += f" ON DELETE {fk.on_delete}"
        if fk.on_update:
            stmt += f" ON UPDATE {fk.on_update}"
        stmt += ";"
        parts.append(stmt)
    parts.append("")


def _format_inserts(table, parts: list[str]) -> None:
    """格式化 INSERT 数据。每条原始 INSERT 独立输出，保持各自列顺序。"""
    if not table.inserts:
        parts.append("-- 无数据")
        parts.append("")
        return

    for insert_block in table.inserts:
        # 列名列表（本条 INSERT 独有）
        if insert_block.columns:
            cols_str = ", ".join(f"`{c}`" for c in insert_block.columns)
        else:
            cols_str = ""

        # 值行
        value_lines: list[str] = []
        for row in insert_block.values:
            formatted_values: list[str] = []
            for val in row:
                if val.upper() == "NULL":
                    formatted_values.append("NULL")
                else:
                    formatted_values.append(val)
            value_lines.append(f"({', '.join(formatted_values)})")

        if cols_str:
            parts.append(f"INSERT INTO `{table.name}` ({cols_str}) VALUES")
        else:
            parts.append(f"INSERT INTO `{table.name}` VALUES")

        # 多行值用逗号分隔
        parts.append(",\n".join(value_lines) + ";")


def convert(text: str, source_mode: str, target_mode: str, database: str | None = None) -> tuple[str, dict[str, int]]:
    """转换主入口：过滤规则 → global → line → 解析表结构 → FK排序 → 格式化输出。"""
    rules = filter_rules(source_mode, target_mode)
    counters: dict[str, int] = {r["name"]: 0 for r in rules}
    text = apply_global_rules(text, counters, rules)
    text = apply_line_rules(text, counters, rules)
    tables = parse_tables(text, database)
    tables = sort_tables_by_fk(tables)
    text = format_structured_output(tables)
    return text, counters


def die(msg: str, code: int) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        die(f"Error: input file not found: {input_path}", EXIT_USAGE)
    if input_path.is_dir():
        die(f"Error: input path is a directory: {input_path}", EXIT_USAGE)

    output_path = Path(args.output) if args.output else default_output_path(input_path)
    if output_path.exists() and not args.overwrite:
        die(
            f"Error: output exists, use --overwrite to replace: {output_path}",
            EXIT_USAGE,
        )

    # 读输入
    try:
        text = input_path.read_text(encoding=args.encoding)
    except UnicodeDecodeError as e:
        die(
            f"Error: failed to decode {input_path} as {args.encoding}: {e}\n"
            f"Hint: try --encoding gbk",
            EXIT_RUNTIME,
        )
    except OSError as e:
        die(f"Error: cannot read {input_path}: {e}", EXIT_USAGE)

    line_count = text.count("\n") + (0 if text.endswith("\n") or not text else 1)

    # 转换
    try:
        converted, counters = convert(text, args.source_mode, args.target_mode, args.database)
    except Exception as e:
        die(f"Error: rule application failed: {e}", EXIT_RUNTIME)

    # 原子写入：先写 tmp，成功后 os.replace
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        tmp_path.write_text(converted, encoding=args.encoding)
        os.replace(tmp_path, output_path)
    except OSError as e:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        die(f"Error: cannot write {output_path}: {e}", EXIT_RUNTIME)

    applied_rules = sum(1 for n in counters.values() if n > 0)
    print(
        f"Converted {line_count} lines, applied {applied_rules} rules, "
        f"wrote to {output_path}"
    )
    if args.verbose:
        print("Rule hit counts:")
        for rule in RULES:
            n = counters.get(rule["name"], 0)
            print(f"  {rule['name']:<32} {n:>6}   {rule['desc']}")

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
