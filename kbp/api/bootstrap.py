"""装配层：把各 feature 的表建进同一个库。

feature 之间互不 import，所以只有这里知道"谁跟谁要拼在一起"。
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_MEM_URI = None


def db_path() -> str:
    """数据库路径，默认仓库根 tmp/kb.sqlite3；测试可注入 :memory:。"""
    import os
    return os.environ.get("KBP_DB_PATH", str(ROOT.parent / "tmp" / "kb.sqlite3"))


def _memory_uri() -> str:
    """内存库改成共享缓存地址：各线程各开连接，看到的仍是同一份表。

    裸 :memory: 每条连接都是独立空库，多线程会各看各的；换成共享缓存后
    每条连接依旧独占语句缓存（串数据的根源），库却是同一个。
    """
    global _MEM_URI
    import uuid
    if _MEM_URI is None:
        _MEM_URI = "file:kbp_%s?mode=memory&cache=shared" % uuid.uuid4().hex
    return _MEM_URI


def reset_memory() -> None:
    """丢掉当前内存库，下次连接得到一个新的空库。"""
    global _MEM_URI
    _MEM_URI = None


def create_schema(conn) -> None:
    """在给定连接上建齐所有 feature 需要的表。"""
    import kbp.api.config_store
    import kbp.kit.store
    import kbp.extract.discard_store
    import kbp.extract.record_store
    import kbp.extract.threshold_store
    import kbp.export.row_store
    import kbp.ingest.materials
    import kbp.kit.bank_store
    import kbp.kit.dev_overlay
    import kbp.rebuild.draft_store
    kbp.kit.store.ensure(conn)
    kbp.kit.bank_store.ensure(conn)
    kbp.kit.dev_overlay.ensure(conn)
    kbp.rebuild.draft_store.ensure(conn)
    kbp.api.config_store.ensure(conn)
    kbp.extract.threshold_store.ensure(conn)
    kbp.extract.discard_store.ensure(conn)
    kbp.extract.record_store.ensure(conn)
    kbp.export.row_store.ensure(conn)
    kbp.ingest.materials.ensure(conn)


def connect():
    """打开连接并设好并发参数，不建表。每线程一个连接时用它。"""
    import sqlite3
    path = db_path()
    if path == ":memory:":
        conn = sqlite3.connect(_memory_uri(), uri=True,
                               check_same_thread=False, timeout=5.0)
    else:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, check_same_thread=False, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def open_db():
    """打开数据库并建齐表，返回连接。"""
    conn = connect()
    create_schema(conn)
    return conn
