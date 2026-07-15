"""SQL 方言转换器——在不同数据库之间转换 SQL 文件（带流式转换架构与 HTML 转换报告）。"""
from __future__ import annotations
import argparse
import re
import sys
import tempfile
from pathlib import Path

from converter.registry import get_dialect
from converter.dialects.base import BaseDialect
from converter.pipeline import Pipeline
from converter.rules import ALL_STAGES
from reader.sql_reader import SQLReader
from reader.classifier import classify_statement, StatementType
from writer.sql_writer import SQLWriter
from parser.insert_stream import iter_insert_rows

# 从新拆分的 utils 模块中导入
from utils.sql_parser import parse_statement_to_schema, sort_tables_by_fk
from utils.sql_parser.tokenizer import _extract_identifiers
from utils.report import ConversionReport
from utils.compat import check_compatibility

# 引入诊断、日志与异常体系
from core.diagnostics import Statement, Severity, Diagnostic
from core.logger import get_logger, setup_logger
from core.exceptions import ConversionException, ParseException, RuleException

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

# Kingbase / PostgreSQL 共用特征
_PG_SNIFF_PATS = [
    re.compile(r"\bCOMMENT\s+ON\b", re.IGNORECASE),    # COMMENT ON TABLE/COLUMN
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
    re.compile(r"\bAUTOINCREMENT\b", re.IGNORECASE),
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

    scores = {"mysql": mysql_score, "oracle": oracle_score, "kingbase": kingbase_score, "pgsql": pgsql_score, "sqlite": sqlite_score}
    max_dialect = max(scores, key=scores.get)
    total = sum(scores.values())

    if scores[max_dialect] == 0:
        return "mysql", 0.0

    if scores["kingbase"] == scores["pgsql"] and max_dialect == "kingbase":
        max_dialect = "pgsql"

    confidence = (scores[max_dialect] / total * 100) if total > 0 else 0.0
    return max_dialect, confidence


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
        default=None,
        help="源数据库类型（可选），如 mysql、oracle、pgsql 等",
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
        help="打印每条规则命中次数，且日志级别设为 INFO",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="打印调试级别日志输出",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="打印极详尽的跟踪日志输出",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="当某条 SQL 转换/解析失败时跳过并继续，不中断转换",
    )
    parser.add_argument(
        "--database",
        default=None,
        help="数据库名，用于输出中的表标识符 `数据库名`.`表名`",
    )
    return parser.parse_args(argv)


def _stream_inserts_to_writer(writer: SQLWriter, tmp_file: Path, table, target_dialect: BaseDialect) -> None:
    """从磁盘缓存临时文件流式读取并翻译 INSERT 语句，批量写入目标。"""
    insert_pat = re.compile(
        r"""INSERT\s+INTO\s+(?:`(\w+)`|"(\w+)"|(\w+))\s*(?:\(([^)]*)\))?\s*VALUES\s*""",
        re.IGNORECASE | re.VERBOSE | re.DOTALL,
    )

    reader = SQLReader(tmp_file, encoding="utf-8")
    for insert_stmt in reader.iter_statements():
        m = insert_pat.search(insert_stmt.text)
        if not m:
            continue

        cols_str = ""
        cols_captured = m.group(4)
        if cols_captured:
            cols_str = f" ({', '.join(target_dialect.quote_identifier(c) for c in _extract_identifiers(cols_captured))})"

        row_generator = iter_insert_rows(insert_stmt.text)

        batch: list[str] = []
        for row in row_generator:
            formatted_values: list[str] = []
            for val in row:
                if val.upper() == "NULL":
                    formatted_values.append("NULL")
                else:
                    formatted_values.append(val)
            batch.append(f"({', '.join(formatted_values)})")

            if len(batch) >= 1000:
                writer.write(f"INSERT INTO {target_dialect.quote_identifier(table.name)}{cols_str} VALUES")
                writer.write(",\n".join(batch) + ";")
                batch = []

        if batch:
            writer.write(f"INSERT INTO {target_dialect.quote_identifier(table.name)}{cols_str} VALUES")
            writer.write(",\n".join(batch) + ";")


def convert(input_path: Path, output_path: Path, source_mode: str, target_mode: str,
            encoding: str = "utf-8", database: str | None = None,
            report: ConversionReport | None = None,
            continue_on_error: bool = False) -> dict[str, int]:
    """流式转换主入口：DDL 内存构建 & 拓扑排序，DML 磁盘暂存流式翻译。"""
    logger = get_logger()
    source_dialect = get_dialect(source_mode, database)
    target_dialect = get_dialect(target_mode, database)

    tables = []
    table_map = {}
    counters = {}
    global_statements = []

    reader = SQLReader(input_path, encoding=encoding)

    # 匹配 INSERT INTO 表名
    insert_table_pat = re.compile(
        r"""INSERT\s+INTO\s+(?:`(\w+)`|"(\w+)"|(\w+))""",
        re.IGNORECASE | re.VERBOSE
    )

    if report:
        report.start()

    last_line = 0
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # 阶段 1: 流式读取、翻译规则运行、分类分流
        for raw_stmt in reader.iter_statements():
            last_line = raw_stmt.end_line
            # 1. 兼容性特性检索矩阵检验
            if report:
                report.notify_progress(last_line, status="PROCESSING")
                check_compatibility(raw_stmt.text, report)

            logger.trace(f"Processing stmt (Line {raw_stmt.start_line}): {raw_stmt.text[:50]}...")

            stmt_text = raw_stmt.text
            # 特殊处理 MySQL 条件注释 (MYSQL_VERSION_COMMENT)
            is_version_comment = "/*!" in raw_stmt.text
            if is_version_comment:
                logger.debug(f"检测到 MySQL 条件注释: {raw_stmt.text[:80]}...")
                if target_mode == "mysql":
                    global_statements.append(raw_stmt.text)
                    continue
                else:
                    clean_stmt = re.sub(r"/\*!\d*\s*(.*?)\s*\*/", r"\1", raw_stmt.text, flags=re.DOTALL).strip()
                    logger.debug(f"非 MySQL 目标，提取语句体: {clean_stmt}")
                    if "SET NAMES" in clean_stmt.upper() or "CHARACTER SET" in clean_stmt.upper():
                        if target_mode in ("pgsql", "kingbase"):
                            m_enc = re.search(r"SET\s+NAMES\s+'?(\w+)'?", clean_stmt, re.I)
                            enc = "UTF8"
                            if m_enc:
                                raw_enc = m_enc.group(1).lower()
                                if "utf8" in raw_enc:
                                    enc = "UTF8"
                                else:
                                    enc = raw_enc.upper()
                            global_statements.append(f"SET client_encoding = '{enc}';")
                        else:
                            global_statements.append(clean_stmt)
                    continue

            # 普通的 SET / USE 语句在 pipeline 运行前拦截
            upper_clean = stmt_text.upper().strip()
            if upper_clean.startswith("SET ") or upper_clean.startswith("USE "):
                if target_mode == "mysql":
                    global_statements.append(stmt_text)
                else:
                    if "SET NAMES" in upper_clean or "CHARACTER SET" in upper_clean:
                        if target_mode in ("pgsql", "kingbase"):
                            global_statements.append("SET client_encoding = 'UTF8';")
                        else:
                            global_statements.append(stmt_text)
                continue

            try:
                # 2. 运行正则 Pipeline 规则
                stmt_text, counters_delta = _pipeline.run(stmt_text, source_dialect, target_dialect)
                
                # 累加报告中的规则命中数
                if report:
                    report.update_rule_hits(counters_delta)

                for k, v in counters_delta.items():
                    counters[k] = counters.get(k, 0) + v
            except Exception as e:
                rule_err = RuleException(f"应用转换规则失败: {e}")
                if report:
                    report.record_failure(raw_stmt.text, rule_err)
                logger.error(f"[Line {raw_stmt.start_line}] 规则应用异常: {e}")
                if not continue_on_error:
                    raise rule_err
                continue

            stmt_type = classify_statement(stmt_text)

            if stmt_type == StatementType.DML:
                m = insert_table_pat.search(stmt_text)
                if m:
                    tbl_name = m.group(1) or m.group(2) or m.group(3)
                    tbl_key = tbl_name.lower()
                    if any(tbl_key == k.lower() for k in table_map):
                        tmp_file = temp_dir_path / f"dml_{tbl_key}.tmp"
                        with open(tmp_file, "a", encoding="utf-8") as tmp_f:
                            tmp_f.write(stmt_text + "\n")
            else:
                try:
                    parse_statement_to_schema(stmt_text, table_map, tables, database)
                except Exception as e:
                    parse_err = ParseException(f"语法结构解析失败: {e}")
                    if report:
                        report.record_failure(stmt_text, parse_err)
                    logger.error(f"[Line {raw_stmt.start_line}] DDL 结构解析异常: {e}")
                    if not continue_on_error:
                        raise parse_err

        # 阶段 2: 拓扑排序
        sorted_tables = sort_tables_by_fk(tables)

        # 阶段 3: 更新报告中关于 schema 的各项计数指标
        if report:
            report.table_count = len(sorted_tables)
            report.index_count = sum(len(t.indexes) for t in sorted_tables)
            report.constraint_count = sum(
                len(t.foreign_keys) + (1 if t.primary_key else 0)
                for t in sorted_tables
            )

        logger.debug(f"Global statements collected: {global_statements}")
        # 阶段 4: 流式组装输出至临时 SQL 文件
        temp_sql_path = output_path.with_suffix(output_path.suffix + ".tmp_stream")
        with SQLWriter(temp_sql_path, encoding=encoding) as writer:
            if global_statements:
                writer.write("-- --------------------------------------------")
                writer.write("-- 全局环境会话初始化配置")
                writer.write("-- --------------------------------------------")
                for g_stmt in global_statements:
                    writer.write(g_stmt)
                writer.write("")

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

        # 阶段 5: 调用方言写入最终文件（解决 SQLite 的 DB 执行问题，其他方言直接 rename）
        if target_dialect.family == "sqlite":
            sql_content = temp_sql_path.read_text(encoding="utf-8")
            target_dialect.write_output(sql_content, output_path)
            temp_sql_path.unlink(missing_ok=True)
        else:
            import os
            if output_path.exists():
                output_path.unlink()
            os.rename(temp_sql_path, output_path)

    if report:
        report.notify_progress(last_line, status="SUCCESS")
        report.stop()

    return counters


def die(msg: str, code: int) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # 初始化配置 Logger
    setup_logger(verbose=args.verbose, debug=args.debug, trace=args.trace)
    logger = get_logger()

    input_path = Path(args.input)
    if not input_path.exists():
        die(f"Error: input file not found: {input_path}", EXIT_USAGE)
    if input_path.is_dir():
        die(f"Error: input path is a directory: {input_path}", EXIT_USAGE)

    source_mode = args.source_mode
    if not source_mode:
        sniffed_mode, confidence = sniff_source_dialect(input_path)
        source_mode = sniffed_mode
        logger.info(f"自动识别源方言为: {source_mode} (置信度 {confidence:.1f}%)")
    else:
        source_mode = source_mode.strip()

    if not args.target_mode or not args.target_mode.strip():
        die("Error: --target-mode is required. Please specify the target database type, e.g. --target-mode kingbase", EXIT_USAGE)

    output_path = Path(args.output) if args.output else default_output_path(input_path, args.target_mode)
    if output_path.exists() and not args.overwrite:
        die(
            f"Error: output exists, use --overwrite to replace: {output_path}",
            EXIT_USAGE,
        )

    # 实例化报告上下文
    report = ConversionReport()

    line_count = 0
    try:
        with open(input_path, "r", encoding=args.encoding, errors="ignore") as f:
            for _ in f:
                line_count += 1
    except OSError as e:
        die(f"Error: cannot read {input_path}: {e}", EXIT_USAGE)

    logger.info(f"开始转换 SQL 文件，总物理行数: {line_count}")

    # 开始执行转换
    try:
        counters = convert(
            input_path=input_path,
            output_path=output_path,
            source_mode=source_mode,
            target_mode=args.target_mode,
            encoding=args.encoding,
            database=args.database,
            report=report,
            continue_on_error=args.continue_on_error
        )
    except Exception as e:
        die(f"Error: conversion process failed: {e}", EXIT_RUNTIME)

    # 生成 HTML 报告
    try:
        report_path = report.write_report(output_path, source_mode, args.target_mode)
    except Exception as e:
        logger.warning(f"Failed to write HTML report: {e}")
        report_path = None

    dialect = get_dialect(args.target_mode, args.database)
    if dialect.family == "sqlite":
        written_path = output_path.with_suffix(".db")
    else:
        written_path = output_path

    applied_rules = sum(1 for n in counters.values() if n > 0)
    
    # 终端输出转换简易结果
    print("===========================================")
    print("              SQL 转换结束")
    print("===========================================")
    print(f"累计读取代码: {line_count} 行")
    print(f"累计匹配规则: {applied_rules} 个")
    print(f"累计转换耗时: {report.duration:.4f} 秒")
    print(f"告警数量: {len(report.warnings)} 个")
    print(f"错误语句跳过: {len(report.failed_statements)} 个")
    print(f"目标文件输出: {written_path}")
    if report_path:
        print(f"可视化 HTML 报告: {report_path.absolute()}")
    print("===========================================")
    
    if args.verbose:
        print("Rule hit counts:")
        for name, n in sorted(counters.items()):
            if n > 0:
                print(f"  {name:<32} {n:>6}")

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
