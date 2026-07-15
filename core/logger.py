"""SQL 转换器日志组件 — 支持 INFO, WARN, ERROR, DEBUG, TRACE。"""
from __future__ import annotations
import logging
import logging.handlers
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


class DailyAndSizeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """按天和文件大小双重限制的滚动日志切割处理器。"""

    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, delay=False):
        import logging.handlers
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=delay)
        import time
        self.current_date = time.strftime("%Y-%m-%d")

    def shouldRollover(self, record):
        import time
        # 1. 跨天校验检测
        new_date = time.strftime("%Y-%m-%d")
        if new_date != self.current_date:
            self.current_date = new_date
            return True
        # 2. 体积限制校验检测
        return super().shouldRollover(record)


def setup_logger(verbose: bool = False, debug: bool = False, trace: bool = False) -> logging.Logger:
    """初始化并配置全局 Logger 级别与格式，支持控制台彩色与滚动文件双重输出。"""
    import logging.handlers
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
    
    # 1. 输出至终端的彩色日志流
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    formatter = ConsoleFormatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # 2. 输出至物理文件的双重滚动日志流
    try:
        from utils.config_manager import config
        log_file = config.get("logger.file_path", "data/logs/sql_convert.log")
        max_bytes = config.get("logger.max_bytes", 10 * 1024 * 1024)
        backup_count = config.get("logger.backup_count", 7)
    except Exception:
        log_file = "data/logs/sql_convert.log"
        max_bytes = 10 * 1024 * 1024
        backup_count = 7
        
    if log_file:
        from pathlib import Path
        log_path = Path(log_file)
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = DailyAndSizeRotatingFileHandler(
                filename=str(log_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s", 
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # 即使文件写入失败（如无磁盘权限），也应放行终端日志以防系统卡死
            print(f"Failed to setup file log handler: {e}", file=sys.stderr)
            
    return logger


def get_logger() -> logging.Logger:
    """获取当前的全局 Logger。"""
    return logging.getLogger("sql_convert")
