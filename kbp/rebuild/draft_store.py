import sqlite3
from pathlib import Path

import kbp.contracts.submission
import kbp.rebuild.draft_rows

SCHEMA = """
CREATE TABLE IF NOT EXISTS draft (
    participant_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    time_point TEXT NOT NULL,
    submit_seq INTEGER NOT NULL,
    target_map_version TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    mode TEXT NOT NULL,
    propositions TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    PRIMARY KEY (participant_id, material_id, time_point, submit_seq)
);
CREATE TABLE IF NOT EXISTS submitted (
    participant_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    time_point TEXT NOT NULL,
    submit_seq INTEGER NOT NULL,
    target_map_version TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    mode TEXT NOT NULL,
    propositions TEXT NOT NULL,
    started_at TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    PRIMARY KEY (participant_id, material_id, time_point, submit_seq)
);
CREATE INDEX IF NOT EXISTS idx_used ON submitted(target_map_version);
CREATE INDEX IF NOT EXISTS idx_used_fp ON submitted(fingerprint);
"""


class DraftError(RuntimeError):
    """草稿操作失败，多为状态不合法。"""


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


def save(conn: sqlite3.Connection, draft: kbp.contracts.submission.Draft) -> None:
    """保存草稿，同一四元键覆盖旧草稿；测验模式已提交则拒绝。"""
    if _locked(conn, draft):
        raise DraftError("测验模式已提交，不可再改草稿")
    conn.execute(
        "INSERT INTO draft VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(participant_id, material_id, time_point, submit_seq)"
        " DO UPDATE SET"
        " target_map_version=excluded.target_map_version,"
        " fingerprint=excluded.fingerprint, mode=excluded.mode,"
        " propositions=excluded.propositions, saved_at=excluded.saved_at",
        kbp.rebuild.draft_rows.draft_row(draft))
    conn.commit()


def load(conn: sqlite3.Connection, participant_id: int, material_id: int,
         time_point: str, submit_seq: int) -> kbp.contracts.submission.Draft:
    """读回草稿；不存在时报错而不是返回空草稿。"""
    cur = conn.execute(
        "SELECT material_id, time_point, submit_seq, target_map_version,"
        " fingerprint, mode, propositions, saved_at FROM draft"
        " WHERE participant_id = ? AND material_id = ?"
        " AND time_point = ? AND submit_seq = ?",
        (participant_id, material_id, time_point, submit_seq))
    row = cur.fetchone()
    if row is None:
        raise DraftError("草稿不存在")
    return kbp.rebuild.draft_rows.draft_from_row(participant_id, row)


def drop(conn: sqlite3.Connection, participant_id: int, material_id: int,
         time_point: str, submit_seq: int) -> None:
    conn.execute("DELETE FROM draft WHERE participant_id = ?"
                 " AND material_id = ? AND time_point = ? AND submit_seq = ?",
                 (participant_id, material_id, time_point, submit_seq))
    conn.commit()


def submit(conn: sqlite3.Connection, sub: kbp.contracts.submission.Submission) -> None:
    """写入提交并删除同键草稿；同一四元键只允许一次，学习模式靠序号区分多次。"""
    if _exists(conn, sub):
        raise DraftError("该四元键已提交，不可重复提交")
    conn.execute("INSERT INTO submitted VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 kbp.rebuild.draft_rows.sub_row(sub))
    conn.execute("DELETE FROM draft WHERE participant_id = ?"
                 " AND material_id = ? AND time_point = ? AND submit_seq = ?",
                 (sub.participant_id, sub.material_id, sub.time_point,
                  sub.submit_seq))
    conn.commit()


def drafts(conn: sqlite3.Connection, participant_id: int,
           material_id: int | None = None) -> list:
    """列出某人的草稿，可按教材筛；同一教材旧序号在前。"""
    sql = ("SELECT material_id, time_point, submit_seq, target_map_version,"
           " fingerprint, mode, propositions, saved_at FROM draft"
           " WHERE participant_id = ?")
    args: list = [participant_id]
    if material_id is not None:
        sql += " AND material_id = ?"
        args.append(material_id)
    sql += " ORDER BY material_id, submit_seq"
    return [kbp.rebuild.draft_rows.draft_from_row(participant_id, row)
            for row in conn.execute(sql, args)]


def submissions(conn: sqlite3.Connection, participant_id: int,
                material_id: int | None = None) -> list:
    """列出某人的提交，可按教材筛；同一教材按提交先后。"""
    sql = ("SELECT material_id, time_point, submit_seq, target_map_version,"
           " fingerprint, mode, propositions, started_at, submitted_at"
           " FROM submitted WHERE participant_id = ?")
    args: list = [participant_id]
    if material_id is not None:
        sql += " AND material_id = ?"
        args.append(material_id)
    sql += " ORDER BY material_id, submit_seq"
    return [kbp.rebuild.draft_rows.sub_from_row(participant_id, row)
            for row in conn.execute(sql, args)]


def next_seq(conn: sqlite3.Connection, participant_id: int, material_id: int,
             time_point: str) -> int:
    """该前三元的下一个提交序号，从 1 起。"""
    cur = conn.execute(
        "SELECT MAX(submit_seq) FROM submitted WHERE participant_id = ?"
        " AND material_id = ? AND time_point = ?",
        (participant_id, material_id, time_point))
    row = cur.fetchone()
    return 1 if not row or row[0] is None else int(row[0]) + 1


def counts(conn: sqlite3.Connection, participant_id: int, material_id: int,
           time_point: str, mode: str) -> int:
    """该前三元在某模式下已提交的次数。"""
    cur = conn.execute(
        "SELECT COUNT(*) FROM submitted WHERE participant_id = ?"
        " AND material_id = ? AND time_point = ? AND mode = ?",
        (participant_id, material_id, time_point, mode))
    return int(cur.fetchone()[0])


def _locked(conn: sqlite3.Connection, obj) -> bool:
    """测验模式同一四元键提交过就锁死；学习模式不锁。"""
    cur = conn.execute(
        "SELECT 1 FROM submitted WHERE participant_id = ?"
        " AND material_id = ? AND time_point = ? AND submit_seq = ?"
        " AND mode = ? LIMIT 1",
        (obj.participant_id, obj.material_id, obj.time_point, obj.submit_seq,
         kbp.contracts.submission.TEST))
    return cur.fetchone() is not None


def _exists(conn: sqlite3.Connection, obj) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM submitted WHERE participant_id = ?"
        " AND material_id = ? AND time_point = ? AND submit_seq = ? LIMIT 1",
        (obj.participant_id, obj.material_id, obj.time_point, obj.submit_seq))
    return cur.fetchone() is not None
