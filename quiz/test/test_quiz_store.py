import pytest

import quiz_store as qs
import quizsheet as quiz


def q(qid="q1", answer=0):
    return quiz.Question(question_id=qid, stem="题干", choices=("A", "B", "C"),
                         answer_index=answer, qtype=quiz.SINGLE,
                         content_dimension="记忆")


def a(qid="q1", choice=0, tp=quiz.PRE):
    return quiz.Answer(question_id=qid, choice_index=choice, time_point=tp)


def rec(props=None, tp=quiz.PRE):
    return quiz.QuizRecord(quiz_id="z1", participant_id=1, material_id=1,
                           session=1, time_point=tp,
                           answers=tuple(props or (a(),)))


@pytest.fixture
def conn():
    c = qs.connect(":memory:")
    yield c
    c.close()


def test_保存并读回题套(conn):
    qs.save_set(conn, "z1", (q("q1"), q("q2", 1)))
    got = qs.load_set(conn, "z1")
    assert [x.question_id for x in got] == ["q1", "q2"]
    assert got[1].answer_index == 1


def test_同一题套不可被改写(conn):
    qs.save_set(conn, "z1", (q("q1"),))
    with pytest.raises(qs.QuizStoreError):
        qs.save_set(conn, "z1", (q("q1", 1),))


def test_重复保存相同题套幂等(conn):
    qs.save_set(conn, "z1", (q("q1"),))
    qs.save_set(conn, "z1", (q("q1"),))
    assert len(qs.load_set(conn, "z1")) == 1


def test_读不存在题套报错(conn):
    with pytest.raises(qs.QuizStoreError):
        qs.load_set(conn, "nope")


def test_写入作答并读回(conn):
    qs.save_set(conn, "z1", (q("q1"), q("q2", 1)))
    n = qs.save_record(conn, "z1", rec((a("q1", 0), a("q2", 1))),
                       (q("q1"), q("q2", 1)))
    assert n == 2
    assert qs.load_answers(conn, 1, 1, 1, quiz.PRE) == (("q1", 0), ("q2", 1))


def test_判对结果落库(conn):
    qs.save_set(conn, "z1", (q("q1", 0),))
    qs.save_record(conn, "z1", rec((a("q1", 2),)), (q("q1", 0),))
    cur = conn.execute("SELECT is_correct FROM answer")
    assert cur.fetchone()[0] == 0


def test_同点同题重复写入被更新(conn):
    qs.save_set(conn, "z1", (q("q1", 0),))
    qs.save_record(conn, "z1", rec((a("q1", 1),)), (q("q1", 0),))
    qs.save_record(conn, "z1", rec((a("q1", 0),)), (q("q1", 0),))
    assert qs.load_answers(conn, 1, 1, 1, quiz.PRE) == (("q1", 0),)


def test_不同时点互不覆盖(conn):
    qs.save_set(conn, "z1", (q("q1", 0),))
    qs.save_record(conn, "z1", rec((a("q1", 2),), quiz.PRE), (q("q1", 0),))
    qs.save_record(conn, "z1", rec((a("q1", 0),), quiz.POST), (q("q1", 0),))
    assert qs.load_answers(conn, 1, 1, 1, quiz.POST) == (("q1", 0),)
    assert qs.load_answers(conn, 1, 1, 1, quiz.PRE) == (("q1", 2),)


def test_落盘后重开可读回(tmp_path):
    path = str(tmp_path / "sub" / "kb.sqlite3")
    c1 = qs.connect(path)
    qs.save_set(c1, "z1", (q("q1"),))
    qs.save_record(c1, "z1", rec(), (q("q1"),))
    c1.close()
    c2 = qs.connect(path)
    assert len(qs.load_set(c2, "z1")) == 1
    c2.close()
