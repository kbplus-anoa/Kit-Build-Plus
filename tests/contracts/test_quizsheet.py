import inspect
from dataclasses import FrozenInstanceError

import pytest

import kbp.contracts.quizsheet as quiz


def q(qid="q1", answer=0):
    return quiz.Question(question_id=qid, stem="题干", choices=("A", "B"),
                         answer_index=answer, qtype=quiz.SINGLE,
                         content_dimension="")


def a(qid="q1", choice=0, tp=quiz.PRE):
    return quiz.Answer(question_id=qid, choice_index=choice, time_point=tp)


def test_时点只有三个():
    assert quiz.TIME_POINTS == ("pre", "post", "delayed")


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
