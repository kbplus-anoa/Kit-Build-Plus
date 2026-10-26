import json
import sqlite3
from pathlib import Path

import kbp.contracts.adjudication
import kbp.contracts.triple

SCHEMA = """
CREATE TABLE IF NOT EXISTS vocab (
    vocab_id TEXT NOT NULL,
    vocab_version TEXT NOT NULL,
    connections TEXT NOT NULL,
    PRIMARY KEY (vocab_id, vocab_version)
);
CREATE TABLE IF NOT EXISTS adjudication (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    vocab_id TEXT NOT NULL,
    vocab_version TEXT NOT NULL,
    head TEXT NOT NULL,
    connection TEXT NOT NULL,
    tail TEXT NOT NULL,
    confidence REAL NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_batch ON adjudication(batch_id);
"""


class StoreError(RuntimeError):
    """存储层错误，多为数据不合法。"""


def connect(db_path: str) -> sqlite3.Connection:
    """打开或新建库并按需建表；父目录不存在时先建。"""
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    ensure(conn)
    return conn


def ensure(conn: sqlite3.Connection) -> None:
    """在已有连接上建表，供装配层把多个 feature 的表放进同一个库。"""
    conn.executescript(SCHEMA)


def save(conn: sqlite3.Connection, log: kbp.contracts.adjudication.AdjudicationLog) -> int:
    """整批写入裁定记录，返回写入条数。同一批次不可覆盖，词表不可被改写。"""
    if _exists(conn, log.batch_id):
        raise StoreError("批次已存在，不可覆盖: " + log.batch_id)
    _save_vocab(conn, log.vocab)
    rows = [_row(log, item) for item in log.items]
    conn.executemany(
        "INSERT INTO adjudication (batch_id, vocab_id, vocab_version, head,"
        " connection, tail, confidence, decision, reason)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    return len(rows)


def _exists(conn: sqlite3.Connection, batch_id: str) -> bool:
    cur = conn.execute("SELECT 1 FROM adjudication WHERE batch_id = ? LIMIT 1",
                       (batch_id,))
    return cur.fetchone() is not None


def _save_vocab(conn: sqlite3.Connection, vocab: kbp.contracts.triple.Vocab) -> None:
    """词表按（id, 版本）唯一；已存在时必须完全一致，否则拒绝。"""
    cur = conn.execute("SELECT connections FROM vocab WHERE vocab_id = ?"
                       " AND vocab_version = ?",
                       (vocab.vocab_id, vocab.vocab_version))
    row = cur.fetchone()
    payload = json.dumps(list(vocab.connections), ensure_ascii=False)
    if row is None:
        conn.execute("INSERT INTO vocab (vocab_id, vocab_version, connections)"
                     " VALUES (?, ?, ?)",
                     (vocab.vocab_id, vocab.vocab_version, payload))
    elif row[0] != payload:
        raise StoreError("词表已存在且内容不同，不可静默改写: "
                         + vocab.vocab_id + " " + vocab.vocab_version)


def _row(log, item):
    cand = item.candidate
    return (log.batch_id, log.vocab.vocab_id, log.vocab.vocab_version,
            cand.head, cand.connection, cand.tail, cand.confidence,
            item.decision, item.reason)


def load(conn: sqlite3.Connection, batch_id: str) -> kbp.contracts.adjudication.AdjudicationLog:
    """按批次读回完整裁定记录，顺序与写入一致。"""
    cur = conn.execute(
        "SELECT vocab_id, vocab_version, head, connection, tail, confidence,"
        " decision, reason FROM adjudication WHERE batch_id = ? ORDER BY id",
        (batch_id,))
    rows = cur.fetchall()
    if not rows:
        raise StoreError("批次不存在: " + batch_id)
    vocab = _load_vocab(conn, rows[0][0], rows[0][1])
    items = tuple(_item(r) for r in rows)
    return kbp.contracts.adjudication.AdjudicationLog(batch_id=batch_id, vocab=vocab,
                                                      items=items)


def _load_vocab(conn: sqlite3.Connection, vocab_id: str,
                vocab_version: str) -> kbp.contracts.triple.Vocab:
    cur = conn.execute("SELECT connections FROM vocab WHERE vocab_id = ?"
                       " AND vocab_version = ?", (vocab_id, vocab_version))
    row = cur.fetchone()
    if row is None:
        raise StoreError("词表不存在: " + vocab_id)
    return kbp.contracts.triple.Vocab(vocab_id=vocab_id, vocab_version=vocab_version,
                                      connections=tuple(json.loads(row[0])))


def _item(row) -> kbp.contracts.adjudication.Adjudication:
    cand = kbp.contracts.triple.TripleCandidate(head=row[2], connection=row[3],
                                                tail=row[4], confidence=row[5])
    return kbp.contracts.adjudication.Adjudication(candidate=cand, decision=row[6],
                                                   reason=row[7])


def batches(conn: sqlite3.Connection) -> tuple[str, ...]:
    """列出已存批次，按写入先后。"""
    cur = conn.execute("SELECT batch_id FROM adjudication"
                       " GROUP BY batch_id ORDER BY MIN(id)")
    return tuple(r[0] for r in cur.fetchall())
