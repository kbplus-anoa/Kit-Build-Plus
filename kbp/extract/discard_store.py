"""机器侧丢弃留档：模型给了但按词表规则不收的候选（D12）。

与人工裁定留档分开：那边记的是人怎么判，这边记的是机器怎么丢。
按原文指纹分组，同一段原文抽几次就留几次，不覆盖。
"""

import sqlite3

import kbp.contracts.extraction
import kbp.contracts.triple

SCHEMA = """
CREATE TABLE IF NOT EXISTS discarded_candidate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text_sha256 TEXT NOT NULL,
    vocab_id TEXT NOT NULL,
    vocab_version TEXT NOT NULL,
    head TEXT NOT NULL,
    connection TEXT NOT NULL,
    tail TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dc_text
    ON discarded_candidate(text_sha256, created_at);
"""

FIELDS = ("head", "connection", "tail", "reason")


class DiscardError(ValueError):
    """丢弃留档写入被拒。"""


def ensure(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def save(conn: sqlite3.Connection, text_sha256: str,
         vocab: kbp.contracts.triple.Vocab,
         discards: tuple[kbp.contracts.extraction.DiscardedCandidate, ...],
         created_at: str) -> int:
    """写一批丢弃；没有丢弃就不写。返回写入条数。"""
    if not discards:
        return 0
    if not text_sha256:
        raise DiscardError("原文指纹为空，无法留档")
    rows = [(text_sha256, vocab.vocab_id, vocab.vocab_version,
             d.head, d.connection, d.tail, d.reason, created_at)
            for d in discards]
    conn.executemany(
        "INSERT INTO discarded_candidate (text_sha256, vocab_id, "
        "vocab_version, head, connection, tail, reason, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    return len(rows)


def by_text(conn: sqlite3.Connection, text_sha256: str) -> tuple:
    """按原文指纹读回丢弃，按入库先后；每条为 (head, connection, tail, reason)。"""
    if not text_sha256:
        return ()
    got = conn.execute(
        "SELECT head, connection, tail, reason FROM discarded_candidate "
        "WHERE text_sha256 = ? ORDER BY id", (text_sha256,)).fetchall()
    return tuple(tuple(row) for row in got)


def count(conn: sqlite3.Connection) -> int:
    """全库丢弃总数，供核对。"""
    return conn.execute("SELECT COUNT(*) FROM discarded_candidate").fetchone()[0]
