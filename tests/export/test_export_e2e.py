"""端到端：作答 → 判分 → 两张 CSV 落盘。

装配层职责：本用例自己把 quiz / score / export 串起来，feature 之间仍互不 import。
"""


import kbp.export.csv_writer as csv_writer  # noqa: E402
import kbp.contracts.exportcsv as exportcsv  # noqa: E402
import kbp.quiz.grade as grade  # noqa: E402
import kbp.export.question_table as question_table  # noqa: E402
import kbp.contracts.quizsheet as quizsheet  # noqa: E402
import kbp.score.score_service as score_service  # noqa: E402
import kbp.contracts.submission as submission  # noqa: E402
import kbp.export.subject_table as subject_table  # noqa: E402
import kbp.contracts.targetmap as targetmap  # noqa: E402
import kbp.contracts.triple as triple  # noqa: E402


def test_作答到两张_CSV(tmp_path):
    qs = (
        quizsheet.Question(question_id="q1", stem="记忆的第一步",
                           choices=("编码", "提取", "遗忘"), answer_index=0,
                           qtype=quizsheet.SINGLE, content_dimension="记忆"),
        quizsheet.Question(question_id="q2", stem="短时记忆容量",
                           choices=("5±2", "7±2", "9±2"), answer_index=1,
                           qtype=quizsheet.SINGLE, content_dimension="记忆"),
    )
    record = quizsheet.QuizRecord(
        quiz_id="z1", participant_id=1, material_id=1, submit_seq=1,
        time_point=submission.PRE,
        answers=(quizsheet.Answer(question_id="q1", choice_index=0,
                                  time_point=submission.PRE),
                 quizsheet.Answer(question_id="q2", choice_index=0,
                                  time_point=submission.PRE)))
    percent = grade.percent(qs, record)
    assert percent == 50.0

    q_rows = []
    for q in qs:
        ans = next(a for a in record.answers if a.question_id == q.question_id)
        q_rows.append(exportcsv.QuestionRow(
            participant_id=1, material_id=1, target_map_version="v1",
            submit_seq=1, question_id=q.question_id,
            time_point=submission.PRE,
            correct=1 if grade.is_correct(q, ans) else 0,
            score=None, qtype=q.qtype,
            content_dimension=q.content_dimension))

    v = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("包括",))
    target = targetmap.TargetMap(
        map_version="v1", vocab=v,
        concepts=(targetmap.Concept(concept_id="c1", label="记忆"),
                  targetmap.Concept(concept_id="c2", label="短时记忆")),
        propositions=(targetmap.Proposition(head_id="c1", connection="包括",
                                            tail_id="c2"),))
    sub = submission.Submission(
        map_version="v1", fingerprint=target.fingerprint,
        mode=submission.TEST,
        propositions=(submission.SubmittedProposition(
            head_id="c1", connection="包括", tail_id="c2"),),
        started_at="", submitted_at="2026-10-25T10:00:00",
        participant_id=1, material_id=1, time_point=submission.POST,
        submit_seq=1)
    scored = score_service.score(target, sub)
    counts = score_service.summary(scored)

    s_row = exportcsv.SubjectRow(
        participant_id=1, material_id=1, time_point="post", submit_seq=1,
        target_map_version="v1", fingerprint=target.fingerprint,
        mode="test", condition="exp", is_practice=0,
        correct_propositions=scored.correct_propositions,
        total_propositions=scored.total_propositions,
        n_lacking=counts["lacking"], n_excessive=counts["excessive"],
        n_leaving=counts["leaving"], n_reversed=counts["reversed"],
        possibly_inaccurate=0, map_size=1, map_node_count=2,
        signal_isolated=0.0, signal_coverage=1.0,
        signal_concentration=1.0, signal_baseline=0.0)

    out_subject = tmp_path / "subject.csv"
    out_question = tmp_path / "question.csv"
    out_subject.write_bytes(csv_writer.to_csv(subject_table.build((s_row,))))
    out_question.write_bytes(
        csv_writer.to_csv(question_table.build(tuple(q_rows))))

    assert out_subject.read_bytes().startswith(b"\xef\xbb\xbf")
    text = out_subject.read_bytes().decode("utf-8-sig")
    assert "participant_id" in text
    assert "1.00000000" in text
    qtext = out_question.read_bytes().decode("utf-8-sig")
    assert "答对" in qtext
    assert len(qtext.strip().splitlines()) == 3
