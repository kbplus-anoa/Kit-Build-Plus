"""数据路由：测验作答与 CSV 导出。"""

from fastapi import APIRouter, HTTPException, Response


import kbp.export.csv_writer
import kbp.api.deps
import kbp.contracts.exportcsv
import kbp.quiz.grade
import kbp.export.question_table
import kbp.quiz.quiz_store
import kbp.contracts.quizsheet
import kbp.export.subject_table
from kbp.api.schemas import QuestionExportIn, QuizIn, QuizOut, SubjectExportIn

router = APIRouter(prefix="/api", tags=["数据"])


def _question(q) -> kbp.contracts.quizsheet.Question:
    return kbp.contracts.quizsheet.Question(question_id=q.question_id, stem=q.stem,
                                            choices=tuple(q.choices),
                                            answer_index=q.answer_index, qtype=q.qtype,
                                            content_dimension=q.content_dimension)


@router.post("/quiz", response_model=QuizOut)
def save_quiz(body: QuizIn) -> QuizOut:
    """保存题套与作答，返回百分制分数。"""
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
    record = kbp.contracts.quizsheet.QuizRecord(
        quiz_id=body.quiz_id, participant_id=body.participant_id,
        material_id=body.material_id, session=body.session,
        time_point=body.time_point, answers=answers)
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
    return QuizOut(quiz_id=body.quiz_id, time_point=body.time_point,
                   percent=kbp.quiz.grade.percent(questions, record),
                   answered=len(answers))


@router.post("/export/subject")
def export_subject(body: SubjectExportIn) -> Response:
    """被试级 CSV，UTF-8 带 BOM。"""
    rows = tuple(kbp.contracts.exportcsv.SubjectRow(
        participant_id=r.participant_id, material_id=r.material_id,
        target_map_version=r.target_map_version, session=r.session,
        mode=r.mode, condition=r.condition, is_practice=r.is_practice,
        correct_propositions=r.correct_propositions,
        total_propositions=r.total_propositions,
        n_lacking=r.n_lacking, n_excessive=r.n_excessive,
        n_leaving=r.n_leaving, n_reversed=r.n_reversed,
        possibly_inaccurate=r.possibly_inaccurate, map_size=r.map_size,
        map_node_count=r.map_node_count, signal_isolated=r.signal_isolated,
        signal_coverage=r.signal_coverage,
        signal_concentration=r.signal_concentration,
        signal_baseline=r.signal_baseline) for r in body.rows)
    try:
        payload = kbp.export.subject_table.build(rows)
        blob = kbp.export.csv_writer.to_csv(payload)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return _csv(blob, "subject.csv")


@router.post("/export/question")
def export_question(body: QuestionExportIn) -> Response:
    """题级 CSV，long 格式，UTF-8 带 BOM。"""
    rows = tuple(kbp.contracts.exportcsv.QuestionRow(
        participant_id=r.participant_id, material_id=r.material_id,
        target_map_version=r.target_map_version, session=r.session,
        question_id=r.question_id, time_point=r.time_point,
        correct=r.correct, score=r.score, qtype=r.qtype,
        content_dimension=r.content_dimension) for r in body.rows)
    try:
        payload = kbp.export.question_table.build(rows)
        blob = kbp.export.csv_writer.to_csv(payload)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return _csv(blob, "question.csv")


def _csv(blob: bytes, name: str) -> Response:
    return Response(content=blob, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition":
                             'attachment; filename="' + name + '"'})
