"""MySQL → Kingbase SQL 转换器。

用法：
    python convert.py <input.sql> [-o OUTPUT] [--mode {mysql}]
                                  [--encoding ENC] [--overwrite] [-v]

默认输出：<input 主名>_convert.<扩展>，同目录。
"""

import argparse
import os
import re
import sys
from pathlib import Path

from rules import RULES

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
        description="将 mysqldump 导出的 SQL 转换为 Kingbase MySQL 兼容模式可导入的 SQL"
    )
    parser.add_argument("input", help="待转换的 mysqldump .sql 文件路径")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出文件路径；缺省为 <input 主名>_convert.<扩展>",
    )
    parser.add_argument(
        "--mode",
        choices=["mysql"],
        default="mysql",
        help="Kingbase 兼容模式；当前仅支持 mysql",
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
    return parser.parse_args(argv)


def is_insert_line(line: str) -> bool:
    """判断一行是否为 INSERT 数据行（大小写不敏感）。"""
    return line.lstrip()[:11].upper().startswith("INSERT INTO")


def apply_global_rules(text: str, counters: dict[str, int]) -> str:
    """对整段文本依次应用所有 scope=global 规则。"""
    for rule in RULES:
        if rule["scope"] != "global":
            continue
        pattern: re.Pattern = rule["pattern"]
        replacement = rule["replacement"]
        new_text, n = pattern.subn(replacement, text)
        counters[rule["name"]] = counters.get(rule["name"], 0) + n
        text = new_text
    return text


def apply_line_rules(text: str, counters: dict[str, int]) -> str:
    """按行应用所有 scope=line 规则；INSERT 行按 skip_insert 跳过。"""
    line_rules = [r for r in RULES if r["scope"] == "line"]
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


def convert(text: str) -> tuple[str, dict[str, int]]:
    """转换主入口：先 global，后 line。返回 (转换后文本, 每规则命中次数)。"""
    counters: dict[str, int] = {r["name"]: 0 for r in RULES}
    text = apply_global_rules(text, counters)
    text = apply_line_rules(text, counters)
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
        converted, counters = convert(text)
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
