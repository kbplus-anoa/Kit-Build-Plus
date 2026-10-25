"""路由层的公共依赖：一个进程级数据库连接 + 一把写锁。

两把锁刻意分开：
- `_conn_lock` 只为"首次创建连接"服务，可重入，避免路由持锁时再取连接而自锁；
- `_write_lock` 只在写操作期间持有，串行化 SQLite 写入。
"""

import threading

from bootstrap import install_paths, open_db

install_paths()

_conn_lock = threading.RLock()
_write_lock = threading.RLock()
_conn = None


def get_conn():
    """进程内复用同一连接。持写锁时也可安全调用。"""
    global _conn
    with _conn_lock:
        if _conn is None:
            _conn = open_db()
        return _conn


def reset_conn(conn=None):
    """测试用：替换或关闭当前连接。"""
    global _conn
    with _conn_lock:
        _conn = conn


def db_lock() -> threading.RLock:
    """写操作期间持有的锁；可重入，允许内部再调 get_conn。"""
    return _write_lock
