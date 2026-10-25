import pytest

import adjudication
import freeze
import triple


def cand(head, conn, tail, conf=0.9):
    return triple.TripleCandidate(head=head, connection=conn,
                                  tail=tail, confidence=conf)


def item(head, conn, tail, decision=adjudication.ACCEPTED, reason=""):
    return adjudication.Adjudication(candidate=cand(head, conn, tail),
                                     decision=decision, reason=reason)


def make_log(items):
    v = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("属于", "导致", "包括"))
    return adjudication.AdjudicationLog(batch_id="b1", vocab=v, items=tuple(items))


def test_接受项按原顺序取出():
    log = make_log([item("A", "属于", "B"),
                    item("C", "属于", "D", adjudication.REJECTED)])
    assert len(freeze.accepted_items(log)) == 1


def test_驳回项按原顺序取出():
    log = make_log([item("A", "属于", "B"),
                    item("C", "属于", "D", adjudication.REJECTED)])
    assert len(freeze.rejected_items(log)) == 1


def test_冻结后概念按首次出现编号():
    log = make_log([item("记忆", "包括", "短时记忆")])
    t = freeze.freeze(log, "v1")
    assert [c.concept_id for c in t.concepts] == ["c1", "c2"]
    assert [c.label for c in t.concepts] == ["记忆", "短时记忆"]


def test_冻结后命题指向正确概念():
    log = make_log([item("记忆", "包括", "短时记忆")])
    p = freeze.freeze(log, "v1").propositions[0]
    assert (p.head_id, p.connection, p.tail_id) == ("c1", "包括", "c2")


def test_驳回项不进目标图():
    log = make_log([item("记忆", "包括", "短时记忆"),
                    item("长度", "包括", "容量", adjudication.REJECTED)])
    t = freeze.freeze(log, "v1")
    assert len(t.propositions) == 1
    assert "容量" not in [c.label for c in t.concepts]


def test_重复概念只编号一次():
    log = make_log([item("记忆", "包括", "短时记忆"),
                    item("短时记忆", "包括", "长时记忆")])
    t = freeze.freeze(log, "v1")
    assert [c.label for c in t.concepts] == ["记忆", "短时记忆", "长时记忆"]


def test_完全重复的命题被去重():
    log = make_log([item("记忆", "包括", "短时记忆"),
                    item("记忆", "包括", "短时记忆")])
    assert len(freeze.freeze(log, "v1").propositions) == 1


def test_自环命题被丢弃():
    log = make_log([item("记忆", "包括", "记忆")])
    t = freeze.freeze(log, "v1")
    assert t.propositions == ()


def test_词表外连接词拒绝冻结():
    log = make_log([item("A", "包含", "B")])
    with pytest.raises(freeze.FreezeError):
        freeze.freeze(log, "v1")


def test_空版本号拒绝冻结():
    with pytest.raises(freeze.FreezeError):
        freeze.freeze(make_log([item("A", "属于", "B")]), "  ")


def test_无接受概念拒绝冻结():
    log = make_log([item("A", "属于", "B", adjudication.REJECTED)])
    with pytest.raises(freeze.FreezeError):
        freeze.freeze(log, "v1")


def test_冻结结果不可变():
    t = freeze.freeze(make_log([item("A", "属于", "B")]), "v1")
    with pytest.raises(Exception):
        t.map_version = "v2"
