"""阶段5: 约束/索引适配。"""
import re
from converter.pipeline import Rule
from converter.capabilities import CAP_USING_BTREE, CAP_TYPE_BIT_LITERAL, CAP_TYPE_BIT

CONSTRAINT_RULES: list[Rule] = [
    Rule("strip_using_btree", CAP_USING_BTREE,
         re.compile(r"\s*USING\s+BTREE", re.IGNORECASE),
         replacement="", scope="line", skip_insert=True,
         desc="删除 USING BTREE"),
    Rule("convert_bit_literal", CAP_TYPE_BIT_LITERAL,
         re.compile(r"\bb'(0|1)'", re.IGNORECASE),
         replacement=r"'\1'", scope="line", skip_insert=False,
         desc="将 b'0'/b'1' 二进制字面量转为普通整数"),
    Rule("convert_bit_type", CAP_TYPE_BIT,
         re.compile(r"\bbit\s*\(\s*1\s*\)", re.IGNORECASE),
         replacement="SMALLINT", scope="line", skip_insert=False,
         desc="将 bit(1) 类型转为 SMALLINT"),
]
