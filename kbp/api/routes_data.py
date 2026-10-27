"""数据路由：测验作答与 CSV 导出。导出按库检索，前端不再逐行攒数。"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response


import kbp.export.csv_writer
import kbp.api.deps
import kbp.contracts.exportcsv
import kbp.quiz.grade
import kbp.export.question_table
import kbp.quiz.quiz_store
import kbp.rebuild.draft_store
import kbp.contracts.quizsheet
import kbp.export.row_store
import kbp.export.subject_table
from kbp.api.schemas import QuizIn, QuizOut

router = APIRouter(prefix="/api", tags=["数据"])


def _question(q) -> kbp.contracts.quizsheet.Question:
    return kbp.contracts.quizsheet.Question(question_id=q.question_id, stem=q.stem,
                                            choices=tuple(q.choices),
                                            answer_index=q.answer_index, qtype=q.qtype,
                                            content_dimension=q.content_dimension)


@router.post("/quiz", response_model=QuizOut)
def save_quiz(body: QuizIn) -> QuizOut:
    """保存题套与作答，返回百分制分数，并落下题级导出快照。"""
    questions = tuple(_question(q) for q in body.questions)
    try:
        for q in questions:
            kbp.quiz.grade.check_question(q)
    except kbp.quiz.grade.QuizError as exc:
        raise HTTPException(400, str(exc))
    answers = tuple(kbp.contracts.quizsheet.Answer(question_id=a.question_id,
                                                   choice_index=a.choice_index,
                                                   time_point=body.time_point)
                    for a in body.answers)
    seq = kbp.rebuild.draft_store.next_seq(
        kbp.api.deps.get_conn(), body.participant_id, body.material_id,
        body.time_point)
    record = kbp.contracts.quizsheet.QuizRecord(
        quiz_id=body.quiz_id, participant_id=body.participant_id,
        material_id=body.material_id, time_point=body.time_point,
        submit_seq=seq, answers=answers)
    try:
        kbp.quiz.grade.check_record(record, questions)
    except kbp.quiz.grade.QuizError as exc:
        raise HTTPException(400, str(exc))
    with kbp.api.deps.db_lock():
        conn = kbp.api.deps.get_conn()
        try:
            kbp.quiz.quiz_store.save_set(conn, body.quiz_id, questions)
        except kbp.quiz.quiz_store.QuizStoreError as exc:
            raise HTTPException(409, str(exc))
        kbp.quiz.quiz_store.save_record(conn, body.quiz_id, record, questions)
        for row in _question_rows(record, questions, body.target_map_version):
            kbp.export.row_store.save_question(conn, row)
    return QuizOut(quiz_id=body.quiz_id, time_point=body.time_point,
                   percent=kbp.quiz.grade.percent(questions, record),
                   answered=len(answers))


def _question_rows(record, questions, map_version: str) -> tuple:
    """作答 → 题级快照；只有答过的题成行，未答不算 0 分。"""
    rows = []
    for answer in record.answers:
        question = next(q for q in questions
                        if q.question_id == answer.question_id)
        rows.append(kbp.contracts.exportcsv.QuestionRow(
            participant_id=record.participant_id,
            material_id=record.material_id, time_point=record.time_point,
            submit_seq=record.submit_seq, target_map_version=map_version,
            question_id=question.question_id,
            correct=1 if kbp.quiz.grade.is_correct(question, answer) else 0,
            score=None, qtype=question.qtype,
            content_dimension=question.content_dimension))
    return tuple(rows)


@router.get("/export/subject")
def export_subject(
        participant_id: Annotated[list[int] | None, Query()] = None,
        material_id: Annotated[list[int] | None, Query()] = None,
        time_point: Annotated[list[str] | None, Query()] = None) -> Response:
    """被试级 CSV：按被试、教材、时点筛选，空条件即全选。"""
    rows = kbp.export.row_store.subjects(
        kbp.api.deps.get_conn(), _values(participant_id), _values(material_id),
        _values(time_point))
    blob = _blob(rows, kbp.export.subject_table.build)
    return _csv(blob, "subject_" + _today() + ".csv")


@router.get("/export/question")
def export_question(
        participant_id: Annotated[list[int] | None, Query()] = None,
        material_id: Annotated[list[int] | None, Query()] = None,
        time_point: Annotated[list[str] | None, Query()] = None) -> Response:
    """题级 CSV：同一套筛选条件，long 格式。"""
    rows = kbp.export.row_store.questions(
        kbp.api.deps.get_conn(), _values(participant_id), _values(material_id),
        _values(time_point))
    blob = _blob(rows, kbp.export.question_table.build)
    return _csv(blob, "question_" + _today() + ".csv")


def _values(raw):
    return tuple(raw) if raw else ()


def _blob(rows, build) -> bytes:
    """没有记录就报 404；行不合法报 400，不导出半坏文件。"""
    if not rows:
        raise HTTPException(404, "没有符合条件的记录")
    try:
        return kbp.export.csv_writer.to_csv(build(rows))
    except Exception as exc:
        raise HTTPException(400, str(exc))


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def _csv(blob: bytes, name: str) -> Response:
    return Response(content=blob, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition":
                             'attachment; filename="' + name + '"'})
