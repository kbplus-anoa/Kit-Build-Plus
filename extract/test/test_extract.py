import json

import pytest

import extract_service as service
import schema
import triple
import uie
import vocab as vocab_mod
import window

VOCAB_JSON = {
    "vocab_id": "心理学",
    "version": "v1",
    "connections": ["属于", "导致"],
}


def make_vocab():
    return vocab_mod.build(dict(VOCAB_JSON))


class FakeEngine:
    """测试方自建引擎：不加载任何模型，只按预设返回原始条目。"""

    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def extract(self, text, schema):
        self.calls.append((text, schema))
        return self.payload


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


def test_schema_的键是概念_值即词表():
    assert schema.to_schema(make_vocab()) == {"概念": ["属于", "导致"]}


def test_空词表拒绝抽取():
    bad = triple.Vocab(vocab_id="x", vocab_version="v1", connections=())
    with pytest.raises(ValueError):
        schema.validate_vocab(bad)


def test_长文本按窗口切且重叠():
    chunks = window.split("a" * 100, window=40, overlap=10)
    assert len(chunks) == 3
    assert chunks[1].startswith("a" * 30)


def test_空文本不切():
    assert window.split("   ") == []


def test_归一化用于去重():
    assert window.normalize("  A  B ") == "a b"


def test_越界连接词被丢弃():
    nodes = [{"text": "记忆", "probability": 0.9},
             {"text": "编码", "probability": 0.8}]
    raw = [{"属于": nodes, "包含": [{"text": "记忆"}]}]
    got = uie.raw_to_triples(raw, make_vocab())
    assert {c.connection for c in got} == {"属于"}


def test_同一对概念生成两条有向命题():
    nodes = [{"text": "记忆", "probability": 0.9},
             {"text": "编码", "probability": 0.8}]
    raw = [{"属于": nodes}]
    got = uie.raw_to_triples(raw, make_vocab())
    assert len(got) == 2
    assert {c.head for c in got} == {"记忆", "编码"}


def test_抽取结果按置信度降序且去重():
    nodes = [{"text": "遗忘", "probability": 0.4},
             {"text": "衰退", "probability": 0.9}]
    payload = [{"导致": nodes}]
    result = service.extract("文本", make_vocab(), engine=FakeEngine(payload))
    confs = [c.confidence for c in result.triples]
    assert confs == sorted(confs, reverse=True)
    assert len({(c.head, c.connection, c.tail) for c in result.triples}) == 2


def test_引擎收到的是词表_schema():
    engine = FakeEngine([])
    service.extract("文本", make_vocab(), engine=engine)
    assert engine.calls[0][1] == {"概念": ["属于", "导致"]}


def test_未装_paddlenlp_时明确报错():
    adapter = uie.UieExtractor()
    with pytest.raises(uie.UieUnavailable):
        adapter.extract("文本", {"概念": ["属于"]})
