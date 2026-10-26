"""规范化收口：越界/自环/重复/塞连接词一律丢弃，代理分负责排序。"""

import kbp.extract.normalize as normalize
import pytest
from tests.extract.helpers import body, make_vocab, prop


def test_越界连接词被丢弃():
    got = normalize.to_candidates(
        body(prop("记忆", "包含", "编码"), prop("记忆", "属于", "认知")),
        make_vocab())
    assert [c.connection for c in got] == ["属于"]


def test_自环命题被丢弃():
    got = normalize.to_candidates(body(prop("记忆", "属于", "记忆")),
                                  make_vocab())
    assert got == []


def test_重复命题只留一条():
    p = prop("记忆", "属于", "认知")
    assert len(normalize.to_candidates(body(p, dict(p)), make_vocab())) == 1


def test_缺_propositions_字段报错():
    with pytest.raises(normalize.ParseError):
        normalize.to_candidates({"triples": []}, make_vocab())


def test_propositions_不是数组报错():
    with pytest.raises(normalize.ParseError):
        normalize.to_candidates({"propositions": {}}, make_vocab())


def test_证据缺失时退回原文首句():
    got = normalize.to_candidates(body(prop("记忆", "属于", "认知")),
                                  make_vocab(), "记忆属于认知。第二句。")
    assert got[0].evidence == "记忆属于认知"


def test_证据缺失且无原文时留空串():
    got = normalize.to_candidates(body(prop("记忆", "属于", "认知")),
                                  make_vocab(), "")
    assert got[0].evidence == ""


def test_概念里塞了连接词直接丢():
    got = normalize.to_candidates(
        body(prop("记忆属于认知系统", "导致", "遗忘")), make_vocab())
    assert got == []


def test_证据逐字命中原文得满分():
    got = normalize.to_candidates(
        body(prop("记忆", "属于", "认知", evidence="记忆属于认知")),
        make_vocab(), "记忆属于认知。")
    assert got[0].confidence == 1.0


def test_证据对不上原文时降分():
    got = normalize.to_candidates(
        body(prop("记忆", "属于", "认知", evidence="记忆就是认知")),
        make_vocab(), "记忆属于认知。")
    assert got[0].confidence == normalize.SCORE_MISS


def test_没有证据也没有原文时给最低分():
    got = normalize.to_candidates(body(prop("记忆", "属于", "认知")),
                                  make_vocab(), "")
    assert got[0].confidence == normalize.SCORE_EMPTY


def test_不用模型自报的置信度():
    got = normalize.to_candidates(
        body(prop("记忆", "属于", "认知", confidence=0.01)),
        make_vocab(), "记忆属于认知。")
    assert got[0].confidence == 1.0


def test_位置与输出顺序不一致时降权():
    text = "甲属于乙。丙属于丁。"
    got = normalize.to_candidates(
        body(prop("丙", "属于", "丁", evidence="丙属于丁。"),
             prop("甲", "属于", "乙", evidence="甲属于乙。")),
        make_vocab(), text)
    assert got[0].head == "丙" and got[0].confidence == 1.0
    assert got[1].confidence == normalize.OUT_OF_ORDER


def test_超长概念不丢只标可疑并排后():
    long_head = "工作记忆的中央执行系统负责分配注意资源以及协调各子系统的运作"
    got = normalize.to_candidates(
        body(prop(long_head, "属于", "记忆"), prop("复习", "导致", "保持")),
        make_vocab(), "复习导致保持。")
    assert len(got) == 2
    assert got[0].head == "复习"
    assert got[1].suspect is True
    assert got[1].confidence == normalize.SCORE_SUSPECT


def test_同一输入两次输出同序():
    items = body(prop("甲", "属于", "乙", evidence="甲属于乙"),
                 prop("丙", "属于", "丁"))
    first = normalize.to_candidates(items, make_vocab(), "甲属于乙。")
    second = normalize.to_candidates(items, make_vocab(), "甲属于乙。")
    assert [c.head for c in first] == [c.head for c in second] == ["甲", "丙"]
