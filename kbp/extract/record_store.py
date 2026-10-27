import json
import sqlite3
from dataclasses import asdict

import kbp.contracts.extractconfig
import kbp.contracts.extraction
import kbp.contracts.triple

SCHEMA = """
CREATE TABLE IF NOT EXISTS extraction_record (
    batch_id TEXT PRIMARY KEY,
    vocab_id TEXT NOT NULL,
    vocab_version TEXT NOT NULL,
    connections TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    base_url TEXT NOT NULL,
    timeout_s INTEGER NOT NULL,
    max_chars INTEGER NOT NULL,
    enabled INTEGER NOT NULL,
    text_sha256 TEXT NOT NULL,
    chars INTEGER NOT NULL,
    sections INTEGER NOT NULL,
    raw TEXT NOT NULL,
    triples TEXT NOT NULL,
    discards TEXT NOT NULL,
    created_at TEXT NOT NULL,
    map_version TEXT NOT NULL DEFAULT '',
    fingerprint TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_er_text ON extraction_record (text_sha256);
"""

_COLUMNS = ("batch_id, vocab_id, vocab_version, connections, provider, model, "
            "base_url, timeout_s, max_chars, enabled, text_sha256, chars, "
            "sections, raw, triples, discards, created_at, map_version, "
            "fingerprint")
_HOLES = ", ".join(["?"] * 19)


class RecordError(ValueError):
    """抽取留档不可写（批次为空、批次重复、批次不存在）。"""


def ensure(conn: sqlite3.Connection) -> None:
    """建表；已存在则不动。"""
    conn.executescript(SCHEMA)
    conn.commit()


def save(conn: sqlite3.Connection,
         record: kbp.contracts.extraction.ExtractionRecord) -> None:
    """写一条留档；同一批次重复写拒绝，不覆盖。"""
    if not record.batch_id:
        raise RecordError("批次标识为空，无法留档")
    if load(conn, record.batch_id) is not None:
        raise RecordError("批次已存在，不可覆盖: " + record.batch_id)
    conn.execute("INSERT INTO extraction_record (" + _COLUMNS + ") "
                 "VALUES (" + _HOLES + ")", _values(record))
    conn.commit()


def load(conn: sqlite3.Connection,
         batch_id: str) -> kbp.contracts.extraction.ExtractionRecord | None:
    """按批次读回；没有返回 None。"""
    if not batch_id:
        return None
    row = conn.execute("SELECT " + _COLUMNS + " FROM extraction_record "
                       "WHERE batch_id = ?", (batch_id,)).fetchone()
    return _record(row) if row else None


def by_text(conn: sqlite3.Connection,
            text_sha256: str) -> tuple:
    """同一份原文的全部抽取批次，按入库先后；没有返回空元组。"""
    if not text_sha256:
        return ()
    got = conn.execute("SELECT " + _COLUMNS + " FROM extraction_record "
                       "WHERE text_sha256 = ? ORDER BY rowid",
                       (text_sha256,)).fetchall()
    return tuple(_record(row) for row in got)


def attach_map(conn: sqlite3.Connection, batch_id: str, map_version: str,
               fingerprint: str) -> None:
    """留档与冻结图对账：回填版本号与指纹；批次不存在拒绝。"""
    changed = conn.execute(
        "UPDATE extraction_record SET map_version = ?, fingerprint = ? "
        "WHERE batch_id = ?", (map_version, fingerprint, batch_id)).rowcount
    if not changed:
        raise RecordError("批次不存在: " + batch_id)
    conn.commit()


def count(conn: sqlite3.Connection) -> int:
    """留档条数。"""
    return int(conn.execute("SELECT COUNT(*) FROM extraction_record "
                            ).fetchone()[0])


def _values(record) -> tuple:
    config = record.config
    vocab = record.vocab
    return (record.batch_id, vocab.vocab_id, vocab.vocab_version,
            json.dumps(list(vocab.connections), ensure_ascii=False),
            config.provider, config.model, config.base_url, config.timeout_s,
            config.max_chars, int(config.enabled), record.text_sha256,
            record.chars, record.sections, record.raw,
            _dump(record.triples), _dump(record.discards), record.created_at,
            record.map_version, record.fingerprint)


def _record(row) -> kbp.contracts.extraction.ExtractionRecord:
    vocab = kbp.contracts.triple.Vocab(
        vocab_id=row[1], vocab_version=row[2],
        connections=tuple(json.loads(row[3])))
    config = kbp.contracts.extractconfig.ExtractConfig(
        provider=row[4], model=row[5], base_url=row[6], timeout_s=row[7],
        max_chars=row[8], enabled=bool(row[9]))
    return kbp.contracts.extraction.ExtractionRecord(
        batch_id=row[0], vocab=vocab, config=config, text_sha256=row[10],
        chars=row[11], sections=row[12], raw=row[13],
        triples=tuple(kbp.contracts.triple.TripleCandidate(**item)
                      for item in json.loads(row[14])),
        created_at=row[16],
        map_version=row[17], fingerprint=row[18],
        discards=tuple(kbp.contracts.extraction.DiscardedCandidate(**item)
                       for item in json.loads(row[15])))


def _dump(items) -> str:
    return json.dumps([asdict(item) for item in items], ensure_ascii=False)
