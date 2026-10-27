"""词表、提示词、分段与抽取编排。"""

import json

import kbp.contracts.extraction as extraction
import kbp.contracts.triple as triple
import kbp.extract.extract_service as service
import kbp.extract.prompt as prompt
import kbp.extract.vocab as vocab_mod
import kbp.extract.window as window
import pytest
from tests.extract.helpers import (
    VOCAB_JSON, FakeEngine, cand, make_config, make_vocab)


def test_词表缺字段报错():
    with pytest.raises(vocab_mod.VocabError):
        vocab_mod.build({"vocab_id": "x", "version": "v1"})


def test_词表重复连接词报错():
    raw = dict(VOCAB_JSON)
    raw["connections"] = ["属于", "属于"]
    with pytest.raises(vocab_mod.VocabError):
        vocab_mod.build(raw)


def test_词表可从文件读(tmp_path):
    p = tmp_path / "v.json"
    p.write_text(json.dumps(VOCAB_JSON, ensure_ascii=False), "utf-8")
    assert vocab_mod.load(str(p)).connections == ("属于", "导致")


def test_提示词里出现_json_字样与输出样例():
    msgs = prompt.build(make_vocab(), "原文", make_config())
    system = msgs[0]["content"]
    assert "json" in system
    assert '"propositions"' in system


def test_提示词要求概念不含谓语动词():
    msgs = prompt.build(make_vocab(), "原文", make_config())
    assert "名词性短语" in msgs[0]["content"]


def test_提示词把连接词写进用户消息():
    msgs = prompt.build(make_vocab(), "记忆属于认知", make_config())
    assert "属于" in msgs[1]["content"] and "导致" in msgs[1]["content"]


def test_提示词按配置截断正文():
    msgs = prompt.build(make_vocab(), "记" * 100, make_config(max_chars=10))
    assert "记" * 10 in msgs[1]["content"]
    assert "记" * 11 not in msgs[1]["content"]


def test_长段落按字上限硬切():
    chunks = window.split("甲" * 100, window=40)
    assert len(chunks) == 3
    assert chunks[0] == "甲" * 40


def test_短段装进同一个窗口():
    assert window.split("第一段\n\n第二段") == ["第一段\n\n第二段"]


def test_窗口放不下才分开():
    assert window.split("第一段\n\n第二段", window=6) == ["第一段", "第二段"]


def test_多行短文不再一行一段():
    body = "\n\n".join("甲" * 5 for _ in range(300))
    chunks = window.split(body, window=480)
    assert all(len(chunk) <= 480 for chunk in chunks)
    assert len(chunks) < 300


def test_空文本不切():
    assert window.split("   ") == []


def test_归一化用于去重():
    assert window.normalize("  A  B ") == "a b"


def test_引擎收到的词表与配置就是传入的那份():
    engine = FakeEngine([()])
    cfg = make_config()
    vocab = make_vocab()
    service.extract("文本", vocab, cfg, engine=engine)
    assert engine.calls[0][1] is vocab and engine.calls[0][2] is cfg


def test_跨段重复命题只留一条():
    engine = FakeEngine([[cand("记忆", "属于", "认知")],
                         [cand("记忆", "属于", "认知")]])
    result = service.extract("甲段\n乙段", make_vocab(), make_config(),
                             engine=engine)
    assert len(result.triples) == 1


def test_结果按代理分降序():
    hit = triple.TripleCandidate(head="复习", connection="导致", tail="保持",
                                 confidence=1.0, evidence="复习导致保持")
    miss = triple.TripleCandidate(head="遗忘", connection="导致", tail="衰退",
                                  confidence=0.4, evidence="对不上原文")
    result = service.extract("复习导致保持。", make_vocab(), make_config(),
                             engine=FakeEngine([[miss, hit]]))
    assert [c.head for c in result.triples] == ["复习", "遗忘"]


def test_空词表拒绝抽取():
    bad = triple.Vocab(vocab_id="x", vocab_version="v1", connections=())
    with pytest.raises(service.ExtractError):
        service.extract("文本", bad, make_config(), engine=FakeEngine([()]))


def test_配置不可用时拒绝抽取():
    bad = make_config(timeout_s=0)
    with pytest.raises(service.ExtractError):
        service.extract("文本", make_vocab(), bad, engine=FakeEngine([()]))


def test_未知供应商时拒绝抽取():
    bad = make_config(provider="unknown")
    with pytest.raises(service.ExtractError):
        service.extract("文本", make_vocab(), bad, engine=FakeEngine([()]))


def test_留档记录原文指纹与统计量():
    result = service.extract("记忆属于认知", make_vocab(), make_config(),
                             engine=FakeEngine([[cand("记忆", "属于", "认知")]]))
    rec = service.record(result, "b1", make_config(), "记忆属于认知",
                         sections=1, created_at="2026-10-26T10:00:00")
    assert rec.chars == 6 and len(rec.text_sha256) == 64
    assert rec.triples == result.triples


def test_相同原文指纹相同_不同原文指纹不同():
    assert service.sha256("abc") == service.sha256("abc")
    assert service.sha256("abc") != service.sha256("abd")


class DropEngine:
    """每段都记一条丢弃的假引擎，用来验证丢弃能一路带回来。"""

    def __init__(self):
        self.last_discards = ()
        self.calls = 0

    def extract(self, text, vocab, config):
        self.calls += 1
        self.last_discards = (extraction.DiscardedCandidate(
            head="记忆", connection="包含", tail="编码",
            reason="连接词不在词表"),)
        return ()


def test_丢弃随分段抽取一路带回():
    engine = DropEngine()
    result, drops = service.extract_and_discards("甲。\n\n乙。", make_vocab(),
                                                 make_config(max_chars=3), engine)
    assert engine.calls == 2
    assert result.triples == ()
    assert len(drops) == 2 and drops[0].reason == "连接词不在词表"


def test_extract_仍只回结果():
    result = service.extract("甲。", make_vocab(), make_config(), DropEngine())
    assert result.triples == ()


def test_留档带上丢弃():
    engine = DropEngine()
    result, drops = service.extract_and_discards("甲。", make_vocab(),
                                                 make_config(), engine)
    record = service.record(result, "b1", make_config(), "甲。",
                            created_at="t", discards=drops)
    assert record.discards == drops


class RawEngine:
    """每段回一段原始输出，用来验证留档的原始输出与段数。"""

    def __init__(self):
        self.last_raw = ""
        self.calls = 0

    def extract(self, text, vocab, config):
        self.calls += 1
        self.last_raw = '{"propositions": []}'
        return ()


def test_留档带回原始输出与段数():
    details = service.extract_details("甲。\n\n乙。", make_vocab(),
                                      make_config(max_chars=3), RawEngine())
    assert details.sections == 2
    assert details.raw == '{"propositions": []}\n{"propositions": []}'
    assert details.result.triples == ()


def test_每抽完一段报一次进度():
    seen = []
    details = service.extract_details("甲。\n\n乙。\n\n丙。", make_vocab(),
                                      make_config(max_chars=3), RawEngine(),
                                      on_step=lambda done, total: seen.append((done, total)))
    assert details.sections == 3
    assert seen == [(1, 3), (2, 3), (3, 3)]
