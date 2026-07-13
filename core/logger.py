"""SQL 转换器日志组件 — 支持 INFO, WARN, ERROR, DEBUG, TRACE。"""
from __future__ import annotations
import logging
import sys

# 自定义 TRACE 级别 (5)，低于 DEBUG (10)
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


def _trace_log(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kws)


logging.Logger.trace = _trace_log

# 颜色控制字符
COLOR_RESET = "\033[0m"
COLOR_TRACE = "\033[90m"   # 灰色
COLOR_DEBUG = "\033[36m"   # 青色
COLOR_INFO = "\033[32m"    # 绿色
COLOR_WARN = "\033[33m"    # 黄色
COLOR_ERROR = "\033[31m"   # 红色


class ConsoleFormatter(logging.Formatter):
    """带 ANSI 色彩标记的日志格式化器。"""

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelno
        msg = super().format(record)
        
        # 终端不支持颜色时直接返回
        if not sys.stdout.isatty():
            return msg

        if level == TRACE_LEVEL:
            return f"{COLOR_TRACE}{msg}{COLOR_RESET}"
        elif level == logging.DEBUG:
            return f"{COLOR_DEBUG}{msg}{COLOR_RESET}"
        elif level == logging.INFO:
            return f"{COLOR_INFO}{msg}{COLOR_RESET}"
        elif level == logging.WARNING:
            return f"{COLOR_WARN}{msg}{COLOR_RESET}"
        elif level >= logging.ERROR:
            return f"{COLOR_ERROR}{msg}{COLOR_RESET}"
        return msg


def setup_logger(verbose: bool = False, debug: bool = False, trace: bool = False) -> logging.Logger:
    """初始化并配置全局 Logger 级别与格式。"""
    logger = logging.getLogger("sql_convert")
    logger.handlers.clear()
    
    # 确定最低级别
    if trace:
        level = TRACE_LEVEL
    elif debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING  # 默认仅显示警告和错误
        
    logger.setLevel(level)
    
    # 输出至终端
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    formatter = ConsoleFormatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_logger() -> logging.Logger:
    """获取当前的全局 Logger。"""
    return logging.getLogger("sql_convert")
