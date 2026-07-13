"""Logger 的单元测试。"""
import logging
import unittest
from core.logger import setup_logger, get_logger, TRACE_LEVEL


class TestLogger(unittest.TestCase):
    """验证全局 Logger 级别转换及 TRACE 等级行为。"""

    def test_logger_levels(self):
        """测试不同级别初始化时的 Logger level。"""
        # 1. 默认仅 Warning 级别
        logger = setup_logger(verbose=False, debug=False, trace=False)
        self.assertEqual(logger.level, logging.WARNING)

        # 2. Verbose 对应 Info 级别
        logger = setup_logger(verbose=True, debug=False, trace=False)
        self.assertEqual(logger.level, logging.INFO)

        # 3. Debug 对应 Debug 级别
        logger = setup_logger(verbose=False, debug=True, trace=False)
        self.assertEqual(logger.level, logging.DEBUG)

        # 4. Trace 对应自定义 TRACE 级别 (5)
        logger = setup_logger(verbose=False, debug=False, trace=True)
        self.assertEqual(logger.level, TRACE_LEVEL)

    def test_trace_logging(self):
        """测试 Trace 级别的专属日志方法。"""
        logger = setup_logger(verbose=False, debug=False, trace=True)
        # 验证 logger 拥有 trace 方法并且可以被调用（不抛错）
        try:
            logger.trace("这是一条跟踪日志")
        except AttributeError as e:
            self.fail(f"Logger 实例没有注入 trace 方法: {e}")


if __name__ == "__main__":
    unittest.main()
