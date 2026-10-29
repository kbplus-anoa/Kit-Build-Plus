"""开发者模式对某一批目标图的改写：整份存在库里，读图时盖在原图上。

改的是"这一批看起来是什么样"，不动冻结图本身：target_map 的指纹、版本号
与"学生用过即锁"的语义原样保留；撤销只要删掉这张表里的那一行。
"""

import json
import sqlite3
from dataclasses import dataclass

import kbp.contracts.targetmap
import kbp.contracts.triple

SCHEMA = """
CREATE TABLE IF NOT EXISTS dev_overlay (
    material_id INTEGER NOT NULL,
    map_version TEXT NOT NULL,
    concepts TEXT NOT NULL,
    connections TEXT NOT NULL,
    propositions TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (material_id, map_version)
);
"""


class OverlayError(RuntimeError):
    """叠层不合法：零件为空、越界、自环或重复。"""


@dataclass(frozen=True)
class Overlay:
    """一份开发期改写：概念、连接词与目标命题三块一起换，缺一块即不完整。"""

    concepts: tuple[kbp.contracts.targetmap.Concept, ...]
    connections: tuple[str, ...]
    propositions: tuple[kbp.contracts.targetmap.Proposition, ...]
    updated_at: str = ""  # 最后改写时间，ISO 8601；从库里读回时才有值


def ensure(conn: sqlite3.Connection) -> None:
    """建表，供装配层把多个 feature 的表放进同一个库。"""
    conn.executescript(SCHEMA)


def check(overlay: Overlay) -> str:
    """纯函数：叠层是否成立；返回空串表示成立，否则返回中文原因。"""
    reason = _check_parts(overlay)
    if reason:
        return reason
    return _check_props(overlay)


def _check_parts(overlay: Overlay) -> str:
    if not overlay.concepts:
        return "概念不得为空"
    if not overlay.connections:
        return "连接词不得为空"
    ids = [c.concept_id for c in overlay.concepts]
    if len(set(ids)) != len(ids):
        return "概念 id 重复"
    labels = [c.label.strip() for c in overlay.concepts]
    if not all(labels):
        return "概念字面不得为空"
    if len(set(labels)) != len(labels):
        return "概念字面重复"
    words = list(overlay.connections)
    if len(set(words)) != len(words):
        return "连接词重复"
    if not all(word.strip() for word in words):
        return "连接词不得为空"
    return ""


def _check_props(overlay: Overlay) -> str:
    ids = {c.concept_id for c in overlay.concepts}
    words = set(overlay.connections)
    seen: set[tuple[str, str, str]] = set()
    for prop in overlay.propositions:
        if prop.head_id not in ids or prop.tail_id not in ids:
            return "命题用了不存在的概念: " + prop.head_id + ">" + prop.tail_id
        if prop.connection not in words:
            return "命题用了不存在的连接词: " + prop.connection
        if prop.head_id == prop.tail_id:
            return "命题不允许自环: " + prop.head_id
        key = (prop.head_id, prop.connection, prop.tail_id)
        if key in seen:
            return "命题重复: " + ">".join(key)
        seen.add(key)
    return ""


def load(conn: sqlite3.Connection, material_id: int,
         map_version: str) -> Overlay | None:
    """读回这一批的改写；没改过返回 None。"""
    if not map_version:
        return None
    cur = conn.execute(
        "SELECT concepts, connections, propositions, updated_at"
        " FROM dev_overlay WHERE material_id = ? AND map_version = ?",
        (material_id, map_version))
    row = cur.fetchone()
    if row is None:
        return None
    return Overlay(
        concepts=tuple(_concept(raw) for raw in json.loads(row[0])),
        connections=tuple(json.loads(row[1])),
        propositions=tuple(_prop(raw) for raw in json.loads(row[2])),
        updated_at=row[3])


def save(conn: sqlite3.Connection, material_id: int, map_version: str,
         overlay: Overlay, updated_at: str) -> Overlay:
    """整份覆盖这一批的改写；不成立就抛 OverlayError，库里一个字不动。"""
    if not map_version:
        raise OverlayError("版本号不得为空")
    reason = check(overlay)
    if reason:
        raise OverlayError(reason)
    conn.execute(
        "INSERT INTO dev_overlay (material_id, map_version, concepts,"
        " connections, propositions, updated_at) VALUES (?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(material_id, map_version) DO UPDATE SET"
        " concepts = excluded.concepts, connections = excluded.connections,"
        " propositions = excluded.propositions,"
        " updated_at = excluded.updated_at",
        (material_id, map_version, _pack_concepts(overlay),
         _pack_connections(overlay), _pack_props(overlay), updated_at))
    conn.commit()
    return Overlay(concepts=overlay.concepts,
                   connections=overlay.connections,
                   propositions=overlay.propositions,
                   updated_at=updated_at)


def drop(conn: sqlite3.Connection, material_id: int, map_version: str) -> None:
    """丢掉这一批的改写，回到冻结图原样；本来没有也不算错。"""
    conn.execute("DELETE FROM dev_overlay WHERE material_id = ?"
                 " AND map_version = ?", (material_id, map_version))
    conn.commit()


def apply(target: kbp.contracts.targetmap.TargetMap,
          overlay: Overlay | None) -> kbp.contracts.targetmap.TargetMap:
    """把改写盖在冻结图上；指纹与版本号照旧，批次归属才不会散。"""
    if overlay is None:
        return target
    vocab = kbp.contracts.triple.Vocab(vocab_id=target.vocab.vocab_id,
                                       vocab_version=target.vocab.vocab_version,
                                       connections=overlay.connections)
    return kbp.contracts.targetmap.TargetMap(
        map_version=target.map_version, vocab=vocab,
        concepts=overlay.concepts, propositions=overlay.propositions,
        fingerprint=target.fingerprint)


def _pack_concepts(overlay: Overlay) -> str:
    return json.dumps([{"id": c.concept_id, "label": c.label}
                       for c in overlay.concepts], ensure_ascii=False)


def _pack_connections(overlay: Overlay) -> str:
    return json.dumps(list(overlay.connections), ensure_ascii=False)


def _pack_props(overlay: Overlay) -> str:
    return json.dumps([{"head": p.head_id, "connection": p.connection,
                        "tail": p.tail_id} for p in overlay.propositions],
                      ensure_ascii=False)


def _concept(raw) -> kbp.contracts.targetmap.Concept:
    return kbp.contracts.targetmap.Concept(concept_id=raw["id"],
                                           label=raw["label"])


def _prop(raw) -> kbp.contracts.targetmap.Proposition:
    return kbp.contracts.targetmap.Proposition(
        head_id=raw["head"], connection=raw["connection"], tail_id=raw["tail"])
