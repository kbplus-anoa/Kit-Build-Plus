import pytest

import kbp.quiz.grade as grade
import kbp.contracts.quizsheet as quiz


def q(qid="q1", answer=0, choices=("A", "B", "C")):
    return quiz.Question(question_id=qid, stem="题干", choices=choices,
                         answer_index=answer, qtype=quiz.SINGLE,
                         content_dimension="记忆")


def a(qid="q1", choice=0, tp=quiz.PRE):
    return quiz.Answer(question_id=qid, choice_index=choice, time_point=tp)


def test_选对算对():
    assert grade.is_correct(q(), a(choice=0)) is True


def test_选错算错():
    assert grade.is_correct(q(), a(choice=1)) is False


def test_未作答算错():
    assert grade.is_correct(q(), a(choice=-1)) is False


def test_全对得满分():
    qs = (q("q1", 0), q("q2", 1))
    rec = quiz.QuizRecord(quiz_id="z1", participant_id=1, material_id=1,
                          session=1, time_point=quiz.PRE,
                          answers=(a("q1", 0), a("q2", 1)))
    assert grade.percent(qs, rec) == 100.0


def test_全错得零分():
    qs = (q("q1", 0), q("q2", 1))
    rec = quiz.QuizRecord(quiz_id="z1", participant_id=1, material_id=1,
                          session=1, time_point=quiz.PRE,
                          answers=(a("q1", 2), a("q2", 0)))
    assert grade.percent(qs, rec) == 0.0


def test_空卷得零分():
    qs = (q("q1", 0), q("q2", 1))
    rec = quiz.QuizRecord(quiz_id="z1", participant_id=1, material_id=1,
                          session=1, time_point=quiz.PRE, answers=())
    assert grade.percent(qs, rec) == 0.0


def test_漏答按错计():
    qs = (q("q1", 0), q("q2", 1))
    rec = quiz.QuizRecord(quiz_id="z1", participant_id=1, material_id=1,
                          session=1, time_point=quiz.PRE,
                          answers=(a("q1", 0),))
    assert grade.percent(qs, rec) == 50.0


def test_题数为零不除错():
    rec = quiz.QuizRecord(quiz_id="z1", participant_id=1, material_id=1,
                          session=1, time_point=quiz.PRE, answers=())
    assert grade.percent((), rec) == 0.0


def test_单选必须至少两个选项():
    with pytest.raises(grade.QuizError):
        grade.check_question(q(choices=("A",)))


def test_答案下标越界被拒():
    with pytest.raises(grade.QuizError):
        grade.check_question(q(answer=5))


def test_空题号被拒():
    with pytest.raises(grade.QuizError):
        grade.check_question(q(qid="  "))


def test_未知题型被拒():
    bad = quiz.Question(question_id="q1", stem="x", choices=("A", "B"),
                        answer_index=0, qtype="ranking", content_dimension="")
    with pytest.raises(grade.QuizError):
        grade.check_question(bad)


def test_作答引用不存在的题被拒():
    with pytest.raises(grade.QuizError):
        grade.check_answer(a("q9"), (q(),))


def test_时点不一致被拒():
    qs = (q("q1", 0),)
    rec = quiz.QuizRecord(quiz_id="z1", participant_id=1, material_id=1,
                          session=1, time_point=quiz.POST,
                          answers=(a("q1", 0, quiz.PRE),))
    with pytest.raises(grade.QuizError):
        grade.check_record(rec, qs)


def test_同题重复作答被拒():
    qs = (q("q1", 0),)
    rec = quiz.QuizRecord(quiz_id="z1", participant_id=1, material_id=1,
                          session=1, time_point=quiz.PRE,
                          answers=(a("q1", 0), a("q1", 1)))
    with pytest.raises(grade.QuizError):
        grade.check_record(rec, qs)


def test_关联键必须正整数():
    rec = quiz.QuizRecord(quiz_id="z1", participant_id=0, material_id=1,
                          session=1, time_point=quiz.PRE, answers=())
    with pytest.raises(grade.QuizError):
        grade.check_record(rec, (q(),))
