"""SQL 方言转换器——在不同数据库之间转换 SQL 文件。

用法：
    python convert.py <input.sql> [-o OUTPUT]
                                  [--source-mode {mysql,...}] [--target-mode {kingbase,...}]
                                  [--encoding ENC] [--overwrite] [-v]

默认输出：<input 主名>_convert.<扩展>，同目录。
"""

import argparse
import re
import sys
from pathlib import Path

from converter.registry import get_dialect
from converter.dialects.base import BaseDialect
from converter.pipeline import Pipeline
from converter.rules import ALL_STAGES
from sql_parser import parse_tables, sort_tables_by_fk

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


# ---------------------------------------------------------------------------
# 规则应用（已迁移至 converter.pipeline.Pipeline）
# ---------------------------------------------------------------------------


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


def format_structured_output(tables: list, dialect: BaseDialect) -> str:
    """将解析后的表列表格式化为 5 步骤结构化 SQL 输出。"""
    parts: list[str] = []

    for table in tables:
        label = dialect.format_table_label(table)
        parts.append("-- ============================================")
        parts.append(f"-- 表名: {label} 开始")
        parts.append("-- ============================================")
        parts.append("")

        # 步骤1: 删除旧表
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤1: 删除旧表")
        parts.append("-- --------------------------------------------")
        parts.append(dialect.format_drop_table(table))
        parts.append("")

        # 步骤2: 表结构
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤2: 表结构")
        parts.append("-- --------------------------------------------")
        parts.append(dialect.format_create_table(table))
        parts.append("")

        # 步骤3: 索引
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤3: 索引")
        parts.append("-- --------------------------------------------")
        extra_indexes = dialect.format_indexes(table)
        if extra_indexes:
            parts.extend(extra_indexes)
        else:
            parts.append("-- 无额外索引")
        parts.append("")

        # 步骤4: 外键
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤4: 外键")
        parts.append("-- --------------------------------------------")
        fks = dialect.format_foreign_keys(table)
        if fks:
            parts.extend(fks)
        else:
            parts.append("-- 无外键")
        parts.append("")

        # 步骤5: 数据导入
        parts.append("-- --------------------------------------------")
        parts.append("-- 步骤5: 数据导入")
        parts.append("-- --------------------------------------------")
        parts.extend(dialect.format_inserts(table))
        parts.append("")

        parts.append("-- ============================================")
        parts.append(f"-- 表名: {label} 结束")
        parts.append("-- ============================================")
        parts.append("")

    return "\n".join(parts)


def convert(text: str, source_mode: str, target_mode: str,
            database: str | None = None) -> tuple[str, dict[str, int]]:
    """转换主入口：Pipeline → 解析表结构 → FK排序 → 格式化输出。"""
    source_dialect = get_dialect(source_mode, database)
    target_dialect = get_dialect(target_mode, database)
    text, counters = _pipeline.run(text, source_dialect, target_dialect)
    tables = parse_tables(text, database)
    tables = sort_tables_by_fk(tables)
    text = format_structured_output(tables, target_dialect)
    return text, counters


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
        converted, counters = convert(text, source_mode, args.target_mode, args.database)
    except Exception as e:
        die(f"Error: rule application failed: {e}", EXIT_RUNTIME)

    # 使用方言策略写入输出
    try:
        dialect = get_dialect(args.target_mode, args.database)
        written_path = dialect.write_output(converted, output_path)
    except Exception as e:
        die(f"Error: cannot write output: {e}", EXIT_RUNTIME)

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
