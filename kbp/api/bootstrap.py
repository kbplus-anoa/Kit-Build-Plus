"""装配层：把各 feature 的目录接入导入路径，并把它们的表建进同一个库。

feature 之间互不 import，所以只有这里知道"谁跟谁要拼在一起"。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE_DIRS = ("ingest", "extract", "kit", "rebuild", "score", "quiz", "export")


def install_paths() -> None:
    """把 contract-share 与各 feature 目录加入 sys.path，幂等。"""
    for layer in ("contract-share", "ui-share") + FEATURE_DIRS:
        path = ROOT / layer
        if path.is_dir():
            entry = str(path)
            if entry not in sys.path:
                sys.path.insert(0, entry)


def db_path() -> str:
    """数据库路径，默认仓库根 tmp/kb.sqlite3；测试可注入 :memory:。"""
    import os
    return os.environ.get("KBP_DB_PATH", str(ROOT.parent / "tmp" / "kb.sqlite3"))


def create_schema(conn) -> None:
    """在给定连接上建齐所有 feature 需要的表。"""
    install_paths()
    import draft_store
    import quiz_store
    import store as kit_store
    import kbp.api.config_store
    import kbp.extract.discard_store
    import kbp.extract.threshold_store
    import kbp.kit.bank_store
    kit_store.ensure(conn)
    kbp.kit.bank_store.ensure(conn)
    draft_store.ensure(conn)
    quiz_store.ensure(conn)
    kbp.api.config_store.ensure(conn)
    kbp.extract.threshold_store.ensure(conn)
    kbp.extract.discard_store.ensure(conn)


def open_db():
    """打开数据库并建齐表，返回连接。"""
    import sqlite3
    path = db_path()
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    create_schema(conn)
    return conn
