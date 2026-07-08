"""规则包 — 汇总所有阶段规则。"""
from converter.rules.cleanup import CLEANUP_RULES
from converter.rules.identifier import IDENTIFIER_RULES
from converter.rules.type_mapping import TYPE_MAPPING_RULES
from converter.rules.modifier import MODIFIER_RULES
from converter.rules.constraint import CONSTRAINT_RULES
from converter.rules.postprocess import POSTPROCESS_RULES

ALL_STAGES: list[list] = [
    CLEANUP_RULES,
    IDENTIFIER_RULES,
    TYPE_MAPPING_RULES,
    MODIFIER_RULES,
    CONSTRAINT_RULES,
    POSTPROCESS_RULES,
]