import inspect
from dataclasses import FrozenInstanceError

import pytest

import kbp.contracts.quizsheet as quiz
import kbp.contracts.submission as submission


def test_关联键四元固定():
    assert submission.KEY_FIELDS == ("participant_id", "material_id",
                                     "time_point", "submit_seq")


def test_提交契约带指纹与时点与提交序号():
    from dataclasses import fields
    names = {f.name for f in fields(submission.Submission)}
    assert {"fingerprint", "time_point", "submit_seq"} <= names
    assert "session" not in names


def test_草稿契约带指纹与时点与提交序号():
    from dataclasses import fields
    names = {f.name for f in fields(submission.Draft)}
    assert {"fingerprint", "time_point", "submit_seq"} <= names
    assert "session" not in names


def test_时点三个取值与题库契约一致():
    assert submission.TIME_POINTS == ("pre", "post", "delayed")


def test_关联键校验签名稳定():
    assert list(inspect.signature(submission.check_key).parameters) == [
        "participant_id", "material_id", "time_point", "submit_seq"]


def q(qid="q1", answer=0):
    return quiz.Question(question_id=qid, stem="题干", choices=("A", "B"),
                         answer_index=answer, qtype=quiz.SINGLE,
                         content_dimension="")


def a(qid="q1", choice=0, tp=submission.PRE):
    return quiz.Answer(question_id=qid, choice_index=choice, time_point=tp)


def test_时点只有三个():
    assert submission.TIME_POINTS == ("pre", "post", "delayed")


def test_题型含单选填空简答():
    assert quiz.QUESTION_TYPES == ("single", "blank", "essay")


def test_未作答用负一表示():
    assert a(choice=-1).choice_index == -1


def test_题目不可变():
    with pytest.raises(FrozenInstanceError):
        q().stem = "改"


def test_作答不可变():
    with pytest.raises(FrozenInstanceError):
        a().choice_index = 1


def test_判对函数签名稳定():
    assert list(inspect.signature(quiz.is_correct).parameters) == [
        "question", "answer"]


def test_百分制函数签名稳定():
    assert list(inspect.signature(quiz.percent_score).parameters) == [
        "questions", "record"]


def test_选项数上限():
    assert quiz.MAX_CHOICES == 8


def test_题干长度上限():
    assert quiz.MAX_STEM == 2000


def test_整卷契约带提交序号不带场次():
    from dataclasses import fields
    names = {f.name for f in fields(quiz.QuizRecord)}
    assert "submit_seq" in names and "time_point" in names
    assert "session" not in names
