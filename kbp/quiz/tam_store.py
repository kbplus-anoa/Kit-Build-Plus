"""TAM 作答落库：一人一题一行，重答覆盖，α 随时可从库重算。

早期 α 由调用方把整份作答 POST 上来现算，算完就散，事后无法核对是谁的数据。
现在作答先落库，报告只从库读，重复作答以最后一次为准。
"""

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS tam_answer (
    participant_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    score REAL NOT NULL,
    answered_at TEXT NOT NULL,
    PRIMARY KEY (participant_id, item_id)
);
CREATE INDEX IF NOT EXISTS idx_tam_answer_item ON tam_answer(item_id);
"""


def ensure(conn: sqlite3.Connection) -> None:
    """建表；已存在则不动。"""
    conn.executescript(SCHEMA)
    conn.commit()


def save(conn: sqlite3.Connection, participant_id: int, item_id: str,
         score: float, answered_at: str) -> None:
    """写一题作答；同一人同一题覆盖旧值，改答不留两行。"""
    conn.execute(
        "INSERT INTO tam_answer VALUES (?, ?, ?, ?)"
        " ON CONFLICT(participant_id, item_id) DO UPDATE SET"
        " score=excluded.score, answered_at=excluded.answered_at",
        (participant_id, item_id, float(score), answered_at))
    conn.commit()


def save_all(conn: sqlite3.Connection, participant_id: int,
             scores, answered_at: str) -> int:
    """整卷写入，scores 为（题号, 得分）序列；返回写入条数。"""
    rows = [(participant_id, item_id, float(score), answered_at)
            for item_id, score in scores]
    conn.executemany(
        "INSERT INTO tam_answer VALUES (?, ?, ?, ?)"
        " ON CONFLICT(participant_id, item_id) DO UPDATE SET"
        " score=excluded.score, answered_at=excluded.answered_at",
        rows)
    conn.commit()
    return len(rows)


def rows(conn: sqlite3.Connection) -> tuple:
    """全部作答，按被试与题号排序；元组形状同契约里的 ScoreRow。"""
    cur = conn.execute(
        "SELECT participant_id, item_id, score FROM tam_answer"
        " ORDER BY participant_id, item_id")
    return tuple((p, item, float(score)) for p, item, score in cur.fetchall())


def count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM tam_answer").fetchone()[0])
