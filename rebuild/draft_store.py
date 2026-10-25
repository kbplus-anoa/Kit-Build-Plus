import json
import sqlite3
from pathlib import Path

import submission

SCHEMA = """
CREATE TABLE IF NOT EXISTS draft (
    participant_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    session INTEGER NOT NULL,
    target_map_version TEXT NOT NULL,
    mode TEXT NOT NULL,
    propositions TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    PRIMARY KEY (participant_id, material_id, session)
);
CREATE TABLE IF NOT EXISTS submitted (
    participant_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    session INTEGER NOT NULL,
    target_map_version TEXT NOT NULL,
    mode TEXT NOT NULL,
    propositions TEXT NOT NULL,
    started_at TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    PRIMARY KEY (participant_id, material_id, session)
);
CREATE INDEX IF NOT EXISTS idx_used ON submitted(target_map_version);
"""


class DraftError(RuntimeError):
    """草稿操作失败，多为状态不合法。"""


def connect(db_path: str) -> sqlite3.Connection:
    """打开或新建库并建表；父目录不存在时先建。"""
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    ensure(conn)
    return conn


def ensure(conn: sqlite3.Connection) -> None:
    """在已有连接上建表，供装配层把多个 feature 的表放进同一个库。"""
    conn.executescript(SCHEMA)


def save(conn: sqlite3.Connection, draft: submission.Draft) -> None:
    """保存草稿，同一（被试, 教材, 场次）覆盖旧草稿。"""
    if _submitted(conn, draft):
        raise DraftError("已提交，不可再改草稿")
    conn.execute(
        "INSERT INTO draft VALUES (?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(participant_id, material_id, session) DO UPDATE SET"
        " target_map_version=excluded.target_map_version, mode=excluded.mode,"
        " propositions=excluded.propositions, saved_at=excluded.saved_at",
        _draft_row(draft))
    conn.commit()


def load(conn: sqlite3.Connection, participant_id: int, material_id: int,
         session: int) -> submission.Draft:
    """读回草稿；不存在时报错而不是返回空草稿。"""
    cur = conn.execute(
        "SELECT target_map_version, mode, propositions, saved_at FROM draft"
        " WHERE participant_id = ? AND material_id = ? AND session = ?",
        (participant_id, material_id, session))
    row = cur.fetchone()
    if row is None:
        raise DraftError("草稿不存在")
    props = tuple(_prop(p) for p in json.loads(row[2]))
    return submission.Draft(map_version=row[0], mode=row[1],
                            propositions=props,
                            participant_id=participant_id,
                            material_id=material_id, session=session,
                            saved_at=row[3])


def drop(conn: sqlite3.Connection, participant_id: int, material_id: int,
         session: int) -> None:
    conn.execute("DELETE FROM draft WHERE participant_id = ?"
                 " AND material_id = ? AND session = ?",
                 (participant_id, material_id, session))
    conn.commit()


def submit(conn: sqlite3.Connection, sub: submission.Submission) -> None:
    """把草稿转成正式提交：写入 submitted 并删除草稿，同一场次只允许一次。"""
    if _submitted(conn, sub):
        raise DraftError("该场次已提交，不可重复提交")
    conn.execute("INSERT INTO submitted VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                 _sub_row(sub))
    conn.execute("DELETE FROM draft WHERE participant_id = ?"
                 " AND material_id = ? AND session = ?",
                 (sub.participant_id, sub.material_id, sub.session))
    conn.commit()


def _submitted(conn: sqlite3.Connection, obj) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM submitted WHERE participant_id = ?"
        " AND material_id = ? AND session = ? LIMIT 1",
        (obj.participant_id, obj.material_id, obj.session))
    return cur.fetchone() is not None


def _draft_row(draft: submission.Draft) -> tuple:
    return (draft.participant_id, draft.material_id, draft.session,
            draft.map_version, draft.mode, _pack(draft.propositions),
            draft.saved_at)


def _sub_row(sub: submission.Submission) -> tuple:
    return (sub.participant_id, sub.material_id, sub.session,
            sub.map_version, sub.mode, _pack(sub.propositions),
            sub.started_at, sub.submitted_at)


def _pack(props) -> str:
    return json.dumps([{"head": p.head_id, "connection": p.connection,
                        "tail": p.tail_id} for p in props],
                      ensure_ascii=False)


def _prop(raw: dict) -> submission.SubmittedProposition:
    return submission.SubmittedProposition(head_id=raw["head"],
                                           connection=raw["connection"],
                                           tail_id=raw["tail"])
