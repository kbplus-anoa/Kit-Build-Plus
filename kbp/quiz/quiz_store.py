import json
import sqlite3
from pathlib import Path

import kbp.quiz.grade
import kbp.contracts.quizsheet

SCHEMA = """
CREATE TABLE IF NOT EXISTS quiz_set (
    quiz_id TEXT PRIMARY KEY,
    questions TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS answer (
    quiz_id TEXT NOT NULL,
    participant_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    time_point TEXT NOT NULL,
    submit_seq INTEGER NOT NULL,
    question_id TEXT NOT NULL,
    choice_index INTEGER NOT NULL,
    is_correct INTEGER NOT NULL,
    PRIMARY KEY (quiz_id, participant_id, material_id, time_point, submit_seq,
                 question_id)
);
CREATE INDEX IF NOT EXISTS idx_answer_pt ON answer(participant_id,
                                                  material_id, time_point);
"""


class QuizStoreError(RuntimeError):
    """测验存储错误。"""


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


def save_set(conn: sqlite3.Connection,
             quiz_id: str, questions) -> None:
    """保存一套题；同一 quiz_id 已存在且内容不同则拒绝覆盖。"""
    payload = json.dumps([_question_dict(q) for q in questions],
                         ensure_ascii=False)
    cur = conn.execute("SELECT questions FROM quiz_set WHERE quiz_id = ?",
                       (quiz_id,))
    row = cur.fetchone()
    if row is None:
        conn.execute("INSERT INTO quiz_set VALUES (?, ?)", (quiz_id, payload))
    elif row[0] != payload:
        raise QuizStoreError("同一 quiz_id 的题目被改写: " + quiz_id)
    conn.commit()


def load_set(conn: sqlite3.Connection, quiz_id: str) -> tuple:
    """读回整套题，保持保存时的顺序。"""
    cur = conn.execute("SELECT questions FROM quiz_set WHERE quiz_id = ?",
                       (quiz_id,))
    row = cur.fetchone()
    if row is None:
        raise QuizStoreError("题套不存在: " + quiz_id)
    return tuple(_question_obj(raw) for raw in json.loads(row[0]))


def save_record(conn: sqlite3.Connection, quiz_id: str,
                record: kbp.contracts.quizsheet.QuizRecord, questions) -> int:
    """逐题写入作答与判对结果，返回写入条数。同一次作答整份替换。"""
    rows = [(quiz_id, record.participant_id, record.material_id,
             record.time_point, record.submit_seq,
             a.question_id, a.choice_index,
             1 if _right(questions, a) else 0) for a in record.answers]
    conn.execute(
        "DELETE FROM answer WHERE quiz_id = ? AND participant_id = ?"
        " AND material_id = ? AND time_point = ? AND submit_seq = ?",
        (quiz_id, record.participant_id, record.material_id,
         record.time_point, record.submit_seq))
    conn.executemany(
        "INSERT INTO answer VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(quiz_id, participant_id, material_id, time_point,"
        " submit_seq, question_id) DO UPDATE SET"
        " choice_index=excluded.choice_index, is_correct=excluded.is_correct",
        rows)
    conn.commit()
    return len(rows)


def next_seq(conn: sqlite3.Connection, quiz_id: str, participant_id: int,
             material_id: int, time_point: str) -> int:
    """同一套题同一被试同一教材同一时点的作答序号：已有则沿用，否则为 1。

    重测沿用同一序号即覆盖，与该时点只保留一次作答的口径一致；不与
    重建提交共用计数器，否则两边序号会互相错位。
    """
    cur = conn.execute(
        "SELECT MAX(submit_seq) FROM answer WHERE quiz_id = ?"
        " AND participant_id = ? AND material_id = ? AND time_point = ?",
        (quiz_id, participant_id, material_id, time_point))
    row = cur.fetchone()
    return 1 if row is None or row[0] is None else int(row[0])


def _right(questions, answer) -> bool:
    """判对只走 kbp.quiz.grade.is_correct，避免两处规则分叉。"""
    for q in questions:
        if q.question_id == answer.question_id:
            return kbp.quiz.grade.is_correct(q, answer)
    return False


def load_answers(conn: sqlite3.Connection, participant_id: int,
                 material_id: int, time_point: str,
                 submit_seq: int) -> tuple:
    """读回某人在某时点第几次提交的逐题作答，按题号顺序。"""
    cur = conn.execute(
        "SELECT question_id, choice_index FROM answer"
        " WHERE participant_id = ? AND material_id = ? AND time_point = ?"
        " AND submit_seq = ? ORDER BY question_id",
        (participant_id, material_id, time_point, submit_seq))
    return tuple((r[0], r[1]) for r in cur.fetchall())


def _question_dict(q) -> dict:
    return {"question_id": q.question_id, "stem": q.stem,
            "choices": list(q.choices), "answer_index": q.answer_index,
            "qtype": q.qtype, "content_dimension": q.content_dimension}


def _question_obj(raw: dict) -> kbp.contracts.quizsheet.Question:
    return kbp.contracts.quizsheet.Question(question_id=raw["question_id"], stem=raw["stem"],
                                            choices=tuple(raw["choices"]),
                                            answer_index=raw["answer_index"],
                                            qtype=raw["qtype"],
                                            content_dimension=raw["content_dimension"])
