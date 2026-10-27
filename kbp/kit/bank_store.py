"""题库落库：把冻结的目标图按（教材, 版本号）与内容指纹存进 target_map 表。

一张图一个版本号，指纹唯一；已投用的版本由 lock 与调用方共同守住，不许覆盖。
"""

import json
import sqlite3

import kbp.contracts.targetbank
import kbp.contracts.targetmap
import kbp.contracts.triple

SCHEMA = """
CREATE TABLE IF NOT EXISTS target_map (
    material_id INTEGER NOT NULL,
    map_version TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    vocab_id TEXT NOT NULL,
    vocab_version TEXT NOT NULL,
    source TEXT NOT NULL,
    in_use INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    batch_id TEXT NOT NULL DEFAULT '',
    connections TEXT NOT NULL,
    concepts TEXT NOT NULL,
    propositions TEXT NOT NULL,
    PRIMARY KEY (material_id, map_version)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tm_fp ON target_map(material_id, fingerprint);
CREATE INDEX IF NOT EXISTS idx_tm_vocab
    ON target_map(material_id, vocab_version, created_at);
"""


class BankError(RuntimeError):
    """题库操作失败：版本重号、同一张图重复入库等。"""


def ensure(conn: sqlite3.Connection) -> None:
    """建表，供装配层把多个 feature 的表放进同一个库。"""
    conn.executescript(SCHEMA)


def register(conn: sqlite3.Connection, entry) -> None:
    """登记一份冻结图；版本号与指纹都不许重复。"""
    reason = kbp.contracts.targetbank.check_entry(entry)
    if reason:
        raise BankError(reason)
    if version_exists(conn, entry.material_id, entry.target_map.map_version):
        raise BankError("版本号已存在，不可覆盖: " + entry.target_map.map_version)
    if by_fingerprint(conn, entry.material_id, entry.target_map.fingerprint):
        raise BankError("同一张图已在库: " + entry.target_map.fingerprint)
    conn.execute(
        "INSERT INTO target_map (material_id, map_version, fingerprint, vocab_id,"
        " vocab_version, source, in_use, created_at, batch_id, connections,"
        " concepts, propositions) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        _row(entry))
    conn.commit()


def by_fingerprint(conn: sqlite3.Connection, material_id: int, fingerprint: str):
    """按内容指纹查同一张图；指纹为空视为查不到。"""
    if not fingerprint:
        return None
    cur = conn.execute("SELECT * FROM target_map WHERE material_id = ?"
                       " AND fingerprint = ?", (material_id, fingerprint))
    return _entry(cur.fetchone())


def latest(conn: sqlite3.Connection, material_id: int, vocab_version: str):
    """该教材该词表版本下最新入库的一张图。"""
    cur = conn.execute(
        "SELECT * FROM target_map WHERE material_id = ? AND vocab_version = ?"
        " ORDER BY created_at DESC, rowid DESC LIMIT 1",
        (material_id, vocab_version))
    return _entry(cur.fetchone())


def version_exists(conn: sqlite3.Connection, material_id: int,
                   map_version: str) -> bool:
    """该教材下这个版本号是否已占用。"""
    cur = conn.execute("SELECT 1 FROM target_map WHERE material_id = ?"
                       " AND map_version = ? LIMIT 1",
                       (material_id, map_version))
    return cur.fetchone() is not None


def versions(conn: sqlite3.Connection, material_id: int) -> tuple[str, ...]:
    """该教材已占用的版本号，按入库先后；用于分配新版本。"""
    cur = conn.execute("SELECT map_version FROM target_map WHERE material_id = ?"
                       " ORDER BY rowid", (material_id,))
    return tuple(row[0] for row in cur.fetchall())


def mark_in_use(conn: sqlite3.Connection, material_id: int,
                map_version: str) -> None:
    """标记为已投用；此后该版本拒改，也不再被重抽覆盖。"""
    if not version_exists(conn, material_id, map_version):
        raise BankError("版本不存在: " + map_version)
    conn.execute("UPDATE target_map SET in_use = 1 WHERE material_id = ?"
                 " AND map_version = ?", (material_id, map_version))
    conn.commit()


def _row(entry) -> tuple:
    target = entry.target_map
    return (entry.material_id, target.map_version, target.fingerprint,
            target.vocab.vocab_id, target.vocab.vocab_version, entry.source,
            int(entry.in_use), entry.created_at, entry.batch_id,
            _pack_connections(target), _pack_concepts(target),
            _pack_props(target))


def _entry(row):
    if row is None:
        return None
    vocab = kbp.contracts.triple.Vocab(
        vocab_id=row[3], vocab_version=row[4],
        connections=tuple(json.loads(row[9])))
    target = kbp.contracts.targetmap.TargetMap(
        map_version=row[1], vocab=vocab,
        concepts=tuple(_concept(raw) for raw in json.loads(row[10])),
        propositions=tuple(_prop(raw) for raw in json.loads(row[11])),
        fingerprint=row[2])
    return kbp.contracts.targetbank.BankEntry(
        material_id=row[0], vocab_version=row[4], source=row[5],
        in_use=bool(row[6]), created_at=row[7], target_map=target,
        batch_id=row[8])


def _pack_connections(target) -> str:
    return json.dumps(list(target.vocab.connections), ensure_ascii=False)


def _pack_concepts(target) -> str:
    return json.dumps([{"id": c.concept_id, "label": c.label}
                       for c in target.concepts], ensure_ascii=False)


def _pack_props(target) -> str:
    return json.dumps([{"head": p.head_id, "connection": p.connection,
                        "tail": p.tail_id} for p in target.propositions],
                      ensure_ascii=False)


def _concept(raw) -> kbp.contracts.targetmap.Concept:
    return kbp.contracts.targetmap.Concept(concept_id=raw["id"],
                                           label=raw["label"])


def _prop(raw) -> kbp.contracts.targetmap.Proposition:
    return kbp.contracts.targetmap.Proposition(
        head_id=raw["head"], connection=raw["connection"], tail_id=raw["tail"])
