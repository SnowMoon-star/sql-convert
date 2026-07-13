"""SQL 转换器异常继承体系。"""
from __future__ import annotations


class ConversionException(Exception):
    """SQL 转换异常基类。"""
    pass


class ParseException(ConversionException):
    """SQL 语法/语义解析错误。"""
    pass


class RuleException(ConversionException):
    """转换规则匹配/替换应用错误。"""
    pass


class CompatibilityException(ConversionException):
    """目标端不支持的高级数据库语法特性错误。"""
    pass


class GeneratorException(ConversionException):
    """从 AST 还原 SQL 文本失败错误。"""
    pass
