"""SQL 方言转换器——在不同数据库之间转换 SQL 文件（流式架构）。

用法：
    python convert.py <input.sql> [-o OUTPUT]
                                  [--source-mode {mysql,...}] [--target-mode {kingbase,...}]
                                  [--encoding ENC] [--overwrite] [-v]

默认输出：<input 主名>_convert.<扩展>，同目录。
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path

from converter.registry import get_dialect
from converter.dialects.base import BaseDialect
from converter.pipeline import Pipeline
from converter.rules import ALL_STAGES
from sql_parser import parse_statement_to_schema, sort_tables_by_fk, TableBlock, _extract_identifiers
from reader.sql_reader import SQLReader
from reader.classifier import classify_statement, StatementType
from writer.sql_writer import SQLWriter
from parser.insert_stream import iter_insert_rows

_pipeline = Pipeline(ALL_STAGES)

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_RUNTIME = 3


def default_output_path(input_path: Path, target_mode: str) -> Path:
    """在 input 同目录生成 <主名>_<target-mode>_<时间戳>.<扩展>。"""
    import datetime
    stem = input_path.stem
    suffix = input_path.suffix
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return input_path.with_name(f"{stem}_{target_mode}_{ts}{suffix}")


# MySQL 专属特征
_MYSQL_SNIFF_PATS = [
    re.compile(r"`\w+`"),  # 反引号包围的标识符
    re.compile(r"\bENGINE\s*=\s*\w+", re.IGNORECASE),
    re.compile(r"\bAUTO_INCREMENT\s*=\s*\d+", re.IGNORECASE),
    re.compile(r"\bDEFAULT\s+CHARSET\s*=", re.IGNORECASE),
]

# Oracle 专属特征
_ORACLE_SNIFF_PATS = [
    re.compile(r"\bVARCHAR2\b", re.IGNORECASE),
    re.compile(r"\bNUMBER\b", re.IGNORECASE),
    re.compile(r"\bROWNUM\b", re.IGNORECASE),
    re.compile(r"\bSYSDATE\b", re.IGNORECASE),
]

# Kingbase / PostgreSQL 共用特征（Kingbase 基于 PG）
_PG_SNIFF_PATS = [
    re.compile(r"\bCOMMENT\s+ON\b", re.IGNORECASE),    # COMMENT ON TABLE/COLUMN（PG 家族特有）
    re.compile(r"\bCASCADE\b", re.IGNORECASE),          # DROP TABLE ... CASCADE
    re.compile(r"\bSERIAL\b", re.IGNORECASE),           # SERIAL / BIGSERIAL
    re.compile(r"\bBYTEA\b", re.IGNORECASE),            # PG 二进制类型
    re.compile(r"\bBOOLEAN\b", re.IGNORECASE),          # PG 布尔类型
    re.compile(r"::\w+"),                                # ::type 类型转换
    re.compile(r"\bRETURNING\b", re.IGNORECASE),
]

# Kingbase 专属特征
_KINGBASE_SNIFF_PATS = [
    re.compile(r"\bWITHOUT\s+SYSTEM\s+OIDS\b", re.IGNORECASE),
    re.compile(r"\bWITHOUT\s+OIDS\b", re.IGNORECASE),
    re.compile(r"\bSYS_REFCURSOR\b", re.IGNORECASE),
]

# PostgreSQL 专属特征
_PGSQL_SNIFF_PATS = [
    re.compile(r"\bILIKE\b", re.IGNORECASE),
    re.compile(r"\bpg_catalog\b", re.IGNORECASE),
    re.compile(r"\bCREATE\s+EXTENSION\b", re.IGNORECASE),
]

# SQLite 专属特征
_SQLITE_SNIFF_PATS = [
    re.compile(r"\bPRAGMA\b", re.IGNORECASE),
    re.compile(r"\bsqlite_\w+\b", re.IGNORECASE),
    re.compile(r"\bWITHOUT\s+ROWID\b", re.IGNORECASE),
    re.compile(r"\bAUTOINCREMENT\b", re.IGNORECASE),  # SQLite 是连写，MySQL 是 AUTO_INCREMENT
]


def sniff_source_dialect(file_path: Path, limit_lines: int = 1000) -> tuple[str, float]:
    """流式读取 SQL 文件前 N 行，通过特征词正则匹配自动识别源 SQL 方言。

    返回 (方言名, 置信度百分比)。默认降级为 'mysql'。
    """
    mysql_score = 0
    oracle_score = 0
    kingbase_score = 0
    pgsql_score = 0
    sqlite_score = 0

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= limit_lines:
                    break

                # 累加各方言命中分数
                for pat in _MYSQL_SNIFF_PATS:
                    if pat.search(line):
                        mysql_score += 1
                for pat in _ORACLE_SNIFF_PATS:
                    if pat.search(line):
                        oracle_score += 1
                for pat in _PG_SNIFF_PATS:
                    if pat.search(line):
                        kingbase_score += 1
                        pgsql_score += 1
                for pat in _KINGBASE_SNIFF_PATS:
                    if pat.search(line):
                        kingbase_score += 1
                for pat in _PGSQL_SNIFF_PATS:
                    if pat.search(line):
                        pgsql_score += 1
                for pat in _SQLITE_SNIFF_PATS:
                    if pat.search(line):
                        sqlite_score += 1
    except OSError:
        pass

    # 比较分数
    scores = {"mysql": mysql_score, "oracle": oracle_score, "kingbase": kingbase_score, "pgsql": pgsql_score, "sqlite": sqlite_score}
    max_dialect = max(scores, key=scores.get)
    total = sum(scores.values())

    # 若无明显特征，默认降级为 mysql
    if scores[max_dialect] == 0:
        return "mysql", 0.0

    # PG 家族平票时优先 pgsql（kingbase 基于 PG，pgsql 特征更明确）
    if scores["kingbase"] == scores["pgsql"] and max_dialect == "kingbase":
        max_dialect = "pgsql"

    # 置信度 = 最高分 / 总分（若有多个方言命中，置信度降低）
    confidence = (scores[max_dialect] / total * 100) if total > 0 else 0.0
    return max_dialect, confidence


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在不同数据库之间转换 SQL 文件"
    )
    parser.add_argument("input", help="待转换 Rar 的 .sql 文件路径")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出文件路径；缺省为 <input 主名>_convert.<扩展>",
    )
    parser.add_argument(
        "--source-mode",
        default=None,
        help="源数据库类型（必填），如 mysql、oracle、pgsql 等",
    )
    parser.add_argument(
        "--target-mode",
        default=None,
        help="目标数据库类型（必填），如 kingbase、mysql 等",
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


def _stream_inserts_to_writer(writer: SQLWriter, tmp_file: Path, table: TableBlock, target_dialect: BaseDialect) -> None:
    """从磁盘缓存临时文件流式读取并翻译 INSERT 语句，批量写入目标。"""
    insert_pat = re.compile(
        r"""INSERT\s+INTO\s+(?:`(\w+)`|"(\w+)"|(\w+))\s*(?:\(([^)]*)\))?\s*VALUES\s*""",
        re.IGNORECASE | re.VERBOSE | re.DOTALL,
    )

    # 临时文件可能很大，使用 SQLReader 流式按语句读取
    reader = SQLReader(tmp_file, encoding="utf-8")
    for insert_stmt in reader.iter_statements():
        m = insert_pat.search(insert_stmt)
        if not m:
            continue

        cols_str = ""
        cols_captured = m.group(4)
        if cols_captured:
            cols_str = f" ({', '.join(target_dialect.quote_identifier(c) for c in _extract_identifiers(cols_captured))})"

        # 流式解析 Values 的行
        row_generator = iter_insert_rows(insert_stmt)

        batch: list[str] = []
        for row in row_generator:
            formatted_values: list[str] = []
            for val in row:
                if val.upper() == "NULL":
                    formatted_values.append("NULL")
                else:
                    formatted_values.append(val)
            batch.append(f"({', '.join(formatted_values)})")

            # 达到 1000 行后流式刷入磁盘，避免内存堆积
            if len(batch) >= 1000:
                writer.write(f"INSERT INTO {target_dialect.quote_identifier(table.name)}{cols_str} VALUES")
                writer.write(",\n".join(batch) + ";")
                batch = []

        if batch:
            writer.write(f"INSERT INTO {target_dialect.quote_identifier(table.name)}{cols_str} VALUES")
            writer.write(",\n".join(batch) + ";")


def convert(input_path: Path, output_path: Path, source_mode: str, target_mode: str,
            encoding: str = "utf-8", database: str | None = None) -> dict[str, int]:
    """流式转换主入口：DDL 内存构建 & 拓扑排序，DML 磁盘暂存流式翻译。"""
    source_dialect = get_dialect(source_mode, database)
    target_dialect = get_dialect(target_mode, database)

    tables: list[TableBlock] = []
    table_map: dict[str, TableBlock] = {}
    counters: dict[str, int] = {}

    reader = SQLReader(input_path, encoding=encoding)

    # 匹配 INSERT INTO 表名
    insert_table_pat = re.compile(
        r"""INSERT\s+INTO\s+(?:`(\w+)`|"(\w+)"|(\w+))""",
        re.IGNORECASE | re.VERBOSE
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # 阶段 1: 流式读取、翻译规则运行、分类分流
        for raw_stmt in reader.iter_statements():
            # 运行正则 Pipeline 规则（此时 statement 仍然是单条语句，内存开销极小）
            stmt, counters_delta = _pipeline.run(raw_stmt, source_dialect, target_dialect)

            # 累加命中计数器
            for k, v in counters_delta.items():
                counters[k] = counters.get(k, 0) + v

            stmt_type = classify_statement(stmt)

            if stmt_type == StatementType.DML:
                m = insert_table_pat.search(stmt)
                if m:
                    tbl_name = m.group(1) or m.group(2) or m.group(3)
                    tbl_key = tbl_name.lower()
                    # 仅在表已被声明（存在于 table_map 中）时，才保留其 DML 导入数据
                    if any(tbl_key == k.lower() for k in table_map):
                        tmp_file = temp_dir_path / f"dml_{tbl_key}.tmp"
                        with open(tmp_file, "a", encoding="utf-8") as tmp_f:
                            tmp_f.write(stmt + "\n")

            else:
                # DDL, COMMENT, INDEX 或其他辅助语句均在内存中解析并构建 DDL 依赖图
                parse_statement_to_schema(stmt, table_map, tables, database)

        # 阶段 2: 拓扑排序
        sorted_tables = sort_tables_by_fk(tables)

        # 阶段 3: 流式组装输出至临时 SQL 文件
        temp_sql_path = output_path.with_suffix(output_path.suffix + ".tmp_stream")
        with SQLWriter(temp_sql_path, encoding=encoding) as writer:
            for table in sorted_tables:
                label = target_dialect.format_table_label(table)
                writer.write("-- ============================================")
                writer.write(f"-- 表名: {label} 开始")
                writer.write("-- ============================================")
                writer.write("")

                # 步骤1: 删除旧表
                writer.write("-- --------------------------------------------")
                writer.write("-- 步骤1: 删除旧表")
                writer.write("-- --------------------------------------------")
                writer.write(target_dialect.format_drop_table(table))
                writer.write("")

                # 步骤2: 表结构
                writer.write("-- --------------------------------------------")
                writer.write("-- 步骤2: 表结构")
                writer.write("-- --------------------------------------------")
                writer.write(target_dialect.format_create_table(table))
                writer.write("")

                # 步骤3: 索引
                writer.write("-- --------------------------------------------")
                writer.write("-- 步骤3: 索引")
                writer.write("-- --------------------------------------------")
                extra_indexes = target_dialect.format_indexes(table)
                if extra_indexes:
                    for idx_stmt in extra_indexes:
                        writer.write(idx_stmt)
                else:
                    writer.write("-- 无额外索引")
                writer.write("")

                # 步骤4: 外键
                writer.write("-- --------------------------------------------")
                writer.write("-- 步骤4: 外键")
                writer.write("-- --------------------------------------------")
                fks = target_dialect.format_foreign_keys(table)
                if fks:
                    for fk_stmt in fks:
                        writer.write(fk_stmt)
                else:
                    writer.write("-- 无外键")
                writer.write("")

                # 步骤5: 数据导入
                writer.write("-- --------------------------------------------")
                writer.write("-- 步骤5: 数据导入")
                writer.write("-- --------------------------------------------")

                tbl_key = table.name.lower()
                tmp_file = temp_dir_path / f"dml_{tbl_key}.tmp"
                if tmp_file.exists():
                    _stream_inserts_to_writer(writer, tmp_file, table, target_dialect)
                else:
                    writer.write("-- 无数据")
                    writer.write("")

                writer.write("-- ============================================")
                writer.write(f"-- 表名: {label} 结束")
                writer.write("-- ============================================")
                writer.write("")

        # 阶段 4: 调用方言写入最终文件（解决 SQLite 的 DB 执行问题，其他方言直接 rename）
        if target_dialect.family == "sqlite":
            sql_content = temp_sql_path.read_text(encoding="utf-8")
            target_dialect.write_output(sql_content, output_path)
            temp_sql_path.unlink(missing_ok=True)
        else:
            import os
            if output_path.exists():
                output_path.unlink()
            os.rename(temp_sql_path, output_path)

    return counters


def die(msg: str, code: int) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # 校验 source-mode 不能为空
    if not args.source_mode or not args.source_mode.strip():
        die("Error: --source-mode is required. Please specify the source database type, e.g. --source-mode mysql", EXIT_USAGE)

    # 校验 target-mode 不能为空
    if not args.target_mode or not args.target_mode.strip():
        die("Error: --target-mode is required. Please specify the target database type, e.g. --target-mode kingbase", EXIT_USAGE)

    input_path = Path(args.input)
    if not input_path.exists():
        die(f"Error: input file not found: {input_path}", EXIT_USAGE)
    if input_path.is_dir():
        die(f"Error: input path is a directory: {input_path}", EXIT_USAGE)

    source_mode = args.source_mode.strip()

    output_path = Path(args.output) if args.output else default_output_path(input_path, args.target_mode)
    if output_path.exists() and not args.overwrite:
        die(
            f"Error: output exists, use --overwrite to replace: {output_path}",
            EXIT_USAGE,
        )

    # 流式计算总行数，避免一次性加载大文件
    line_count = 0
    try:
        with open(input_path, "r", encoding=args.encoding, errors="ignore") as f:
            for _ in f:
                line_count += 1
    except OSError as e:
        die(f"Error: cannot read {input_path}: {e}", EXIT_USAGE)

    # 转换
    try:
        counters = convert(
            input_path=input_path,
            output_path=output_path,
            source_mode=source_mode,
            target_mode=args.target_mode,
            encoding=args.encoding,
            database=args.database
        )
    except Exception as e:
        die(f"Error: rule application failed: {e}", EXIT_RUNTIME)

    # 获取实际写入的路径
    dialect = get_dialect(args.target_mode, args.database)
    if dialect.family == "sqlite":
        written_path = output_path.with_suffix(".db")
    else:
        written_path = output_path

    applied_rules = sum(1 for n in counters.values() if n > 0)
    print(
        f"Converted {line_count} lines, applied {applied_rules} rules, "
        f"wrote to {written_path}"
    )
    if args.verbose:
        print("Rule hit counts:")
        for name, n in sorted(counters.items()):
            if n > 0:
                print(f"  {name:<32} {n:>6}")

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
