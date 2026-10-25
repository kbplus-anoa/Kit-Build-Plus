import inspect
from dataclasses import FrozenInstanceError

import pytest

import adjudication
import triple


def make_candidate():
    return triple.TripleCandidate(head="记忆", connection="属于",
                                  tail="认知", confidence=0.9)


def make_log():
    v = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("属于", "导致"))
    return adjudication.AdjudicationLog(
        batch_id="b1", vocab=v,
        items=(adjudication.Adjudication(
            candidate=make_candidate(), decision=adjudication.ACCEPTED,
            reason=""),))


def test_裁定只有接受与驳回两值():
    assert adjudication.DECISIONS == ("accepted", "rejected")


def test_裁定项不可变():
    item = adjudication.Adjudication(candidate=make_candidate(),
                                     decision="accepted", reason="")
    with pytest.raises(FrozenInstanceError):
        item.decision = "rejected"


def test_裁定日志不可变():
    log = make_log()
    with pytest.raises(FrozenInstanceError):
        log.batch_id = "b2"


def test_驳回理由长度上限():
    assert adjudication.MAX_REASON == 500


def test_冻结函数签名稳定():
    assert list(inspect.signature(adjudication.freeze).parameters) == [
        "log", "map_version"]


def test_接受项取函数签名稳定():
    assert list(inspect.signature(adjudication.accepted).parameters) == ["log"]


def test_驳回项取函数签名稳定():
    assert list(inspect.signature(adjudication.rejected).parameters) == ["log"]


def test_锁版本判定签名稳定():
    assert list(inspect.signature(adjudication.is_locked).parameters) == [
        "map_version", "used_by_students"]
