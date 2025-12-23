"""
完整的日志系统模块
支持文件日志、日志轮转、控制台输出和前端推送
"""
import os
import sys
import logging
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# 日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


# ============ 日志格式 ============

class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'

    def format(self, record):
        # 添加颜色
        if record.levelno in logging._levelToName:
            level_name = logging._levelToName[record.levelno]
            if level_name in self.COLORS:
                record.levelname = f"{self.COLORS[level_name]}{level_name}{self.RESET}"
        return super().format(record)


# ============ 日志管理器 ============

class LoggerManager:
    """日志管理器（单例模式）"""

    _instance: Optional['LoggerManager'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._loggers = {}
        self._frontend_callback = None

        # 创建根日志器
        self._setup_root_logger()

    def _setup_root_logger(self):
        """配置根日志器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # 清除已有的处理器
        root_logger.handlers.clear()

        # 创建控制台处理器（带颜色）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    def setup_file_logging(
        self,
        level: str = "INFO",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        use_time_rotation: bool = False
    ):
        """
        配置文件日志

        Args:
            level: 日志级别
            max_bytes: 单个日志文件最大字节数
            backup_count: 保留的备份文件数量
            use_time_rotation: 是否使用时间轮转（按天）
        """
        root_logger = logging.getLogger()

        # 移除旧的文件处理器
        for handler in root_logger.handlers[:]:
            if isinstance(handler, (RotatingFileHandler, TimedRotatingFileHandler)):
                root_logger.removeHandler(handler)

        # 日志级别映射
        log_level = getattr(logging, level.upper(), logging.INFO)

        if use_time_rotation:
            # 按天轮转
            log_file = LOG_DIR / "app.log"
            file_handler = TimedRotatingFileHandler(
                filename=log_file,
                when='midnight',
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.suffix = "%Y-%m-%d"
        else:
            # 按大小轮转
            log_file = LOG_DIR / "app.log"
            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )

        file_handler.setLevel(log_level)

        # 文件日志格式（不带颜色）
        file_formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # 创建错误日志单独文件
        error_handler = RotatingFileHandler(
            filename=LOG_DIR / "error.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

    def set_frontend_callback(self, callback):
        """
        设置前端日志推送回调

        Args:
            callback: 回调函数，接收 (level, message) 参数
        """
        self._frontend_callback = callback

    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志器

        Args:
            name: 日志器名称（通常使用 __name__）

        Returns:
            Logger 实例
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]


# ============ 全局日志管理器实例 ============

_manager = LoggerManager()


def setup_file_logging(
    level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    use_time_rotation: bool = False
):
    """
    配置文件日志（便捷函数）

    Args:
        level: 日志级别
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的备份文件数量
        use_time_rotation: 是否使用时间轮转（按天）
    """
    _manager.setup_file_logging(level, max_bytes, backup_count, use_time_rotation)


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志器（便捷函数）

    Args:
        name: 日志器名称，默认为调用模块名

    Returns:
        Logger 实例
    """
    if name is None:
        # 获取调用者的模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'automediabot')
    return _manager.get_logger(name)


def set_frontend_callback(callback):
    """
    设置前端日志推送回调（便捷函数）

    Args:
        callback: 回调函数，接收 (level, message) 参数
    """
    _manager.set_frontend_callback(callback)


# ============ 兼容旧代码的日志函数 ============

class FrontendHandler(logging.Handler):
    """前端推送日志处理器"""

    def emit(self, record):
        """发送日志到前端"""
        if _manager._frontend_callback:
            try:
                # 映射日志级别
                level_map = {
                    logging.DEBUG: 'info',
                    logging.INFO: 'info',
                    logging.WARNING: 'warning',
                    logging.ERROR: 'error',
                    logging.CRITICAL: 'error'
                }
                level = level_map.get(record.levelno, 'info')
                message = self.format(record)
                _manager._frontend_callback(level, message)
            except Exception:
                pass  # 避免日志记录本身导致错误


_frontend_handler: Optional[FrontendHandler] = None


def add_log(level: str, message: str):
    """
    全局日志记录函数（兼容旧代码，同时支持前端推送）

    Args:
        level: 日志级别 (info, success, warning, error)
        message: 日志消息
    """
    global _frontend_handler

    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "id": int(datetime.now().timestamp() * 1000),
        "time": timestamp,
        "level": level,
        "message": message
    }

    # 兼容旧代码：存入运行时状态
    from .config import runtime_state, LOG_LIMIT
    runtime_state["logs"].insert(0, log_entry)
    if len(runtime_state["logs"]) > LOG_LIMIT:
        runtime_state["logs"].pop()

    # 同时使用标准日志系统
    logger = get_logger('automediabot')
    level_map = {
        'info': logging.INFO,
        'success': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'debug': logging.DEBUG,
        'critical': logging.CRITICAL
    }
    log_level = level_map.get(level.lower(), logging.INFO)

    # 添加特殊标记用于 success 级别
    if level.lower() == 'success':
        message = f"[SUCCESS] {message}"

    logger.log(log_level, message)


def enable_frontend_logging():
    """启用前端日志推送（需要在应用启动时调用）"""
    global _frontend_handler
    if _frontend_handler is not None:
        return

    _frontend_handler = FrontendHandler()
    _frontend_handler.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger().addHandler(_frontend_handler)


def disable_frontend_logging():
    """禁用前端日志推送"""
    global _frontend_handler
    if _frontend_handler is not None:
        logging.getLogger().removeHandler(_frontend_handler)
        _frontend_handler = None
