"""规则引擎 — Rule 数据类 + Pipeline 编排器。"""
from __future__ import annotations
import re
from dataclasses import dataclass
from converter.dialects.base import BaseDialect
from converter.pipeline.rule_context import RuleContext

@dataclass
class Rule:
    """一条转换规则。"""
    name: str
    capability: str
    pattern: re.Pattern
    target_capability: str = ""  # 若设置，则要求目标拥有该能力（默认行为是目标没有 capability）
    replacement: str = ""
    scope: str = "line"
    skip_insert: bool = True
    desc: str = ""


def rule_applies(rule: Rule, source: BaseDialect, target: BaseDialect) -> bool:
    """源有该能力，目标没有 → 规则生效。
    如果设置了 target_capability，则要求目标有该能力（而非没有）。"""
    if rule.target_capability:
        return (
            rule.capability in source.capabilities
            and rule.target_capability in target.capabilities
        )
    return (
        rule.capability in source.capabilities
        and rule.capability not in target.capabilities
    )


def _is_insert_line(line: str) -> bool:
    return line.lstrip()[:11].upper().startswith("INSERT INTO")


def _apply_global(text: str, rule: Rule) -> tuple[str, int]:
    new_text, n = rule.pattern.subn(rule.replacement, text)
    return new_text, n


def _apply_line(text: str, rule: Rule, repl: str = "") -> tuple[str, int]:
    replacement = repl if repl else rule.replacement
    total = 0
    has_skip = rule.skip_insert
    out_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if has_skip and _is_insert_line(line):
            out_lines.append(line)
            continue
        new_line, n = rule.pattern.subn(replacement, line)
        total += n
        out_lines.append(new_line)
    return "".join(out_lines), total


class Pipeline:
    """规则管线 — 按阶段顺序执行规则。"""

    def __init__(self, stages: list[list[Rule]]):
        self.stages = stages

    def run(self, text: str, source: BaseDialect, target: BaseDialect) -> tuple[str, dict[str, int]]:
        counters: dict[str, int] = {}

        # 阶段1-6: Rule-based 规则阶段
        for stage in self.stages:
            for rule in stage:
                if not rule_applies(rule, source, target):
                    continue

                # 特殊：normalize_delimiter 使用 lambda
                if rule.name == "normalize_delimiter":
                    text, n = rule.pattern.subn(
                        lambda m: m.group(2).replace(m.group(1), ";").strip() + ";\n",
                        text
                    )
                    counters[rule.name] = counters.get(rule.name, 0) + n
                    continue

                # 特殊：identifier 规则用目标引号
                if rule.name in ("convert_backtick_quote", "convert_double_quote"):
                    repl = target.identifier_quote + r"\1" + target.identifier_quote
                    if rule.scope == "global":
                        text, n = rule.pattern.subn(repl, text)
                    else:
                        text, n = _apply_line(text, rule, repl)
                    counters[rule.name] = counters.get(rule.name, 0) + n
                    continue

                # 标准规则
                if rule.scope == "global":
                    text, n = _apply_global(text, rule)
                else:
                    text, n = _apply_line(text, rule)
                counters[rule.name] = counters.get(rule.name, 0) + n

        # 阶段7: 类型映射（Canonical Type Mapping，在所有 Rule 之后运行）
        from converter.mappings.types import map_types
        text, n = map_types(text, source, target)
        counters["_type_mapping"] = counters.get("_type_mapping", 0) + n

        # 阶段8: 函数映射（Canonical Function Mapping）
        from converter.mappings.functions import map_functions
        text, n = map_functions(text, source, target)
        counters["_func_mapping"] = counters.get("_func_mapping", 0) + n

        return text, counters
