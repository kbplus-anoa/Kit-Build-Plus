"""路由层的公共依赖：每线程一个数据库连接 + 一把写锁。

为什么每线程一个连接：sqlite3 的语句缓存按连接共享，同一段 SQL 在两个线程
上并发执行会串行交出对方的行（实测可复现）。一连接跨线程不安全，所以每线程
各自持有一条，读不再需要加锁。

内存库例外：`:memory:` 每条连接都是一个独立的空库，每线程各开一条会各看各的
空库（并发请求直接 500）。所以内存库全程共用一条连接，仅供单线程测试；
要并发就用文件库。

两把锁刻意分开：
- `_conn_lock` 只为"首次建表"服务，可重入，避免路由持锁时再取连接而自锁；
- `_write_lock` 只在写操作期间持有，串行化 SQLite 写入（写仍只允许一个）。
"""

import threading

import kbp.api.bootstrap


_conn_lock = threading.RLock()
_write_lock = threading.RLock()
_local = threading.local()
_forced = None
_shared = None
_schema_ready = False


def get_conn():
    """本线程的连接；首次调用时建表，之后复用。持写锁时也可安全调用。"""
    if _forced is not None:
        return _forced
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _open()
        _local.conn = conn
    return conn


def _open():
    global _schema_ready, _shared
    with _conn_lock:
        if kbp.api.bootstrap.db_path() == ":memory:":
            if _shared is None:
                _shared = kbp.api.bootstrap.open_db()
            _schema_ready = True
            return _shared
        if not _schema_ready:
            conn = kbp.api.bootstrap.open_db()
            _schema_ready = True
            return conn
    return kbp.api.bootstrap.connect()


def reset_conn(conn=None):
    """测试用：注入一条固定连接（全线程共用），None 表示恢复每线程连接。"""
    global _forced, _shared, _schema_ready
    with _conn_lock:
        _forced = conn
        _local.conn = None
        _shared = None
        _schema_ready = conn is not None


def db_lock() -> threading.RLock:
    """写操作期间持有的锁；可重入，允许内部再调 get_conn。"""
    return _write_lock
