"""导出快照：提交与作答时落下的两张表，导出只读这里。

历史原因：早期导出由前端逐行攒数再 POST 进来，库里的 submitted 只存命题，
评分与描述统计都不在库，导出便无从查起。现在写入侧（提交、测验）顺手把
22 列与 10 列各存一份，导出按被试、教材、时点检索即可，不再依赖前端。
"""

import sqlite3

import kbp.contracts.exportcsv

SCHEMA = """
CREATE TABLE IF NOT EXISTS subject_row (
    participant_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    time_point TEXT NOT NULL,
    submit_seq INTEGER NOT NULL,
    target_map_version TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    mode TEXT NOT NULL,
    condition TEXT NOT NULL,
    is_practice INTEGER NOT NULL,
    correct_propositions INTEGER NOT NULL,
    total_propositions INTEGER NOT NULL,
    n_lacking INTEGER NOT NULL,
    n_excessive INTEGER NOT NULL,
    n_leaving INTEGER NOT NULL,
    n_reversed INTEGER NOT NULL,
    possibly_inaccurate INTEGER NOT NULL,
    map_size INTEGER NOT NULL,
    map_node_count INTEGER NOT NULL,
    signal_isolated REAL,
    signal_coverage REAL,
    signal_concentration REAL,
    signal_baseline REAL,
    PRIMARY KEY (participant_id, material_id, time_point, submit_seq)
);
CREATE TABLE IF NOT EXISTS question_row (
    participant_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    time_point TEXT NOT NULL,
    submit_seq INTEGER NOT NULL,
    target_map_version TEXT NOT NULL,
    question_id TEXT NOT NULL,
    correct INTEGER NOT NULL,
    score REAL,
    qtype TEXT NOT NULL,
    content_dimension TEXT NOT NULL,
    PRIMARY KEY (participant_id, material_id, time_point, submit_seq,
                 question_id)
);
"""

_SUBJECT_COLUMNS = ("participant_id, material_id, time_point, submit_seq, "
                    "target_map_version, fingerprint, mode, condition, "
                    "is_practice, correct_propositions, total_propositions, "
                    "n_lacking, n_excessive, n_leaving, n_reversed, "
                    "possibly_inaccurate, map_size, map_node_count, "
                    "signal_isolated, signal_coverage, signal_concentration, "
                    "signal_baseline")
_QUESTION_COLUMNS = ("participant_id, material_id, time_point, submit_seq, "
                     "target_map_version, question_id, correct, score, qtype, "
                     "content_dimension")


def ensure(conn: sqlite3.Connection) -> None:
    """建表；已存在则不动。"""
    conn.executescript(SCHEMA)
    conn.commit()


def save_subject(conn: sqlite3.Connection,
                 row: kbp.contracts.exportcsv.SubjectRow) -> None:
    """写一行被试级快照；同一四元键覆盖旧值（学习模式多次提交各有序号）。"""
    conn.execute(
        "INSERT INTO subject_row (" + _SUBJECT_COLUMNS + ") VALUES ("
        + _holes(22) + ") ON CONFLICT(participant_id, material_id, time_point,"
        " submit_seq) DO UPDATE SET"
        " target_map_version=excluded.target_map_version,"
        " fingerprint=excluded.fingerprint, mode=excluded.mode,"
        " condition=excluded.condition, is_practice=excluded.is_practice,"
        " correct_propositions=excluded.correct_propositions,"
        " total_propositions=excluded.total_propositions,"
        " n_lacking=excluded.n_lacking, n_excessive=excluded.n_excessive,"
        " n_leaving=excluded.n_leaving, n_reversed=excluded.n_reversed,"
        " possibly_inaccurate=excluded.possibly_inaccurate,"
        " map_size=excluded.map_size, map_node_count=excluded.map_node_count,"
        " signal_isolated=excluded.signal_isolated,"
        " signal_coverage=excluded.signal_coverage,"
        " signal_concentration=excluded.signal_concentration,"
        " signal_baseline=excluded.signal_baseline",
        _subject_values(row))
    conn.commit()


def clear_questions(conn: sqlite3.Connection, participant_id: int,
                    material_id: int, time_point: str,
                    submit_seq: int) -> None:
    """删掉某次作答的全部题级快照；重测少答时不留旧行。"""
    conn.execute(
        "DELETE FROM question_row WHERE participant_id = ? AND material_id = ?"
        " AND time_point = ? AND submit_seq = ?",
        (participant_id, material_id, time_point, submit_seq))
    conn.commit()


def save_question(conn: sqlite3.Connection,
                  row: kbp.contracts.exportcsv.QuestionRow) -> None:
    """写一行题级快照；同键覆盖旧值。"""
    conn.execute(
        "INSERT INTO question_row (" + _QUESTION_COLUMNS + ") VALUES ("
        + _holes(10) + ") ON CONFLICT(participant_id, material_id, time_point,"
        " submit_seq, question_id) DO UPDATE SET"
        " target_map_version=excluded.target_map_version,"
        " correct=excluded.correct, score=excluded.score,"
        " qtype=excluded.qtype, content_dimension=excluded.content_dimension",
        _question_values(row))
    conn.commit()


def subjects(conn: sqlite3.Connection, participant_ids: tuple = (),
             material_ids: tuple = (), time_points: tuple = ()) -> tuple:
    """按被试、教材、时点筛选；空元组表示该维全选。"""
    sql, params = _filtered("subject_row", _SUBJECT_COLUMNS, participant_ids,
                            material_ids, time_points)
    sql += " ORDER BY participant_id, material_id, time_point, submit_seq"
    return tuple(_subject(row) for row in conn.execute(sql, params).fetchall())


def questions(conn: sqlite3.Connection, participant_ids: tuple = (),
              material_ids: tuple = (), time_points: tuple = ()) -> tuple:
    """题级快照的同一套筛选；行按题号排。"""
    sql, params = _filtered("question_row", _QUESTION_COLUMNS, participant_ids,
                            material_ids, time_points)
    sql += (" ORDER BY participant_id, material_id, time_point, submit_seq,"
            " question_id")
    return tuple(_question(row) for row in conn.execute(sql, params).fetchall())


def count_subjects(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM subject_row").fetchone()[0])


def _filtered(table: str, columns: str, participant_ids, material_ids,
              time_points) -> tuple:
    clauses, params = [], []
    for column, values in (("participant_id", participant_ids),
                           ("material_id", material_ids),
                           ("time_point", time_points)):
        values = tuple(values)
        if values:
            clauses.append(column + " IN (" + _holes(len(values)) + ")")
            params.extend(values)
    sql = "SELECT " + columns + " FROM " + table
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    return sql, params


def _holes(count: int) -> str:
    return ", ".join(["?"] * count)


def _subject_values(row) -> tuple:
    return (row.participant_id, row.material_id, row.time_point,
            row.submit_seq, row.target_map_version, row.fingerprint, row.mode,
            row.condition, row.is_practice, row.correct_propositions,
            row.total_propositions, row.n_lacking, row.n_excessive,
            row.n_leaving, row.n_reversed, row.possibly_inaccurate,
            row.map_size, row.map_node_count, row.signal_isolated,
            row.signal_coverage, row.signal_concentration, row.signal_baseline)


def _question_values(row) -> tuple:
    return (row.participant_id, row.material_id, row.time_point,
            row.submit_seq, row.target_map_version, row.question_id,
            row.correct, row.score, row.qtype, row.content_dimension)


def _subject(raw) -> kbp.contracts.exportcsv.SubjectRow:
    return kbp.contracts.exportcsv.SubjectRow(
        participant_id=raw[0], material_id=raw[1], time_point=raw[2],
        submit_seq=raw[3], target_map_version=raw[4], fingerprint=raw[5],
        mode=raw[6], condition=raw[7], is_practice=raw[8],
        correct_propositions=raw[9], total_propositions=raw[10],
        n_lacking=raw[11], n_excessive=raw[12], n_leaving=raw[13],
        n_reversed=raw[14], possibly_inaccurate=raw[15], map_size=raw[16],
        map_node_count=raw[17], signal_isolated=raw[18],
        signal_coverage=raw[19], signal_concentration=raw[20],
        signal_baseline=raw[21])


def _question(raw) -> kbp.contracts.exportcsv.QuestionRow:
    return kbp.contracts.exportcsv.QuestionRow(
        participant_id=raw[0], material_id=raw[1], time_point=raw[2],
        submit_seq=raw[3], target_map_version=raw[4], question_id=raw[5],
        correct=raw[6], score=raw[7], qtype=raw[8],
        content_dimension=raw[9])
