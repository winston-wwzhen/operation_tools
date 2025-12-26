"""
轻量级日志工具模块
提供独立的日志缓冲区管理，避免循环导入问题

此模块不依赖 config 或 logger，可在任何地方安全导入使用
"""
import threading
from datetime import datetime
from typing import List, Dict, Optional

# 日志缓冲区限制
LOG_LIMIT = 100

# 线程安全的日志缓冲区
_log_buffer: List[Dict] = []
_log_lock = threading.Lock()

# 日志级别到标准 logging 的映射
LEVEL_MAP = {
    'info': 'INFO',
    'success': 'INFO',
    'warning': 'WARNING',
    'error': 'ERROR',
    'debug': 'DEBUG',
    'critical': 'CRITICAL'
}


def add_log_to_buffer(level: str, message: str) -> Dict:
    """
    添加日志到内存缓冲区（线程安全）

    Args:
        level: 日志级别 (info, success, warning, error, debug, critical)
        message: 日志消息

    Returns:
        创建的日志条目字典
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "id": int(datetime.now().timestamp() * 1000),
        "time": timestamp,
        "level": level,
        "message": message
    }

    with _log_lock:
        _log_buffer.insert(0, log_entry)
        if len(_log_buffer) > LOG_LIMIT:
            _log_buffer.pop()

    return log_entry


def get_logs() -> List[Dict]:
    """
    获取所有日志（线程安全，返回副本）

    Returns:
        日志列表的副本（按插入顺序倒序）
    """
    with _log_lock:
        return _log_buffer.copy()


def get_log_buffer() -> List[Dict]:
    """
    获取日志缓冲区引用

    注意：直接返回缓冲区引用，不适用于跨线程场景
    主要用于 config.runtime_state 的初始化

    Returns:
        日志缓冲区引用
    """
    return _log_buffer


def clear_logs() -> None:
    """清空日志缓冲区"""
    with _log_lock:
        _log_buffer.clear()


def get_log_count() -> int:
    """
    获取当前日志数量

    Returns:
        日志条目数量
    """
    with _log_lock:
        return len(_log_buffer)


def get_logs_by_level(level: str) -> List[Dict]:
    """
    按级别筛选日志

    Args:
        level: 日志级别

    Returns:
        匹配的日志列表
    """
    level_lower = level.lower()
    with _log_lock:
        return [log for log in _log_buffer if log['level'].lower() == level_lower]


def get_recent_logs(count: int = 10) -> List[Dict]:
    """
    获取最近的 N 条日志

    Args:
        count: 返回的日志数量

    Returns:
        最近的日志列表
    """
    with _log_lock:
        return _log_buffer[:count].copy()


# 用于 runtime_state 的初始化
# 在 config.py 中这样使用：
# runtime_state["logs"] = get_log_buffer()
# 这样 runtime_state 和 _log_buffer 指向同一个列表对象
