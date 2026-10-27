"""运行期自动裁 kit：文本 → 抽取 → 冻结 → 拆零件。"""

import pytest

from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.main as main
import kbp.api.routes_text as routes_text
import kbp.contracts.extractconfig as extractconfig
import kbp.contracts.extraction as extraction
import kbp.contracts.triple as triple
import kbp.extract.discard_store as discard_store
import kbp.extract.extract_service as extract_service
import kbp.extract.threshold_store as threshold_store
from kbp.api.bootstrap import create_schema
from kbp.contracts.quality import Thresholds

KEY = extractconfig.KEY_ENV_NAME

VOCAB = {"vocab_id": "心理学", "version": "v1",
         "connections": ["包括", "属于"]}


@pytest.fixture
def client():
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


def patch_extract(monkeypatch, fn):
    """把编排层换成假实现：按给定结果返回，丢弃留档为空。"""
    def run(text, vocab, cfg=None, engine=None):
        return fn(text, vocab, cfg, engine), ()
    monkeypatch.setattr(extract_service, "extract_and_discards", run)


def cand(head, connection, tail, confidence=0.9):
    return triple.TripleCandidate(head=head, connection=connection, tail=tail,
                                  confidence=confidence)


class FakeEngine:
    def __init__(self, candidates):
        self.candidates = tuple(candidates)

    def extract(self, text, vocab, config):
        return self.candidates


@pytest.fixture
def fake(monkeypatch):
    engine = FakeEngine([cand("记忆", "包括", "短时记忆"),
                         cand("短时记忆", "属于", "记忆系统")])
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=engine_or(engine)))
    return engine


def engine_or(engine):
    return engine if engine else ()


def test_自动裁出零件与指纹(client, monkeypatch):
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=(
                      cand("记忆", "包括", "短时记忆"),
                      cand("短时记忆", "属于", "记忆系统"))))
    body = client.post("/api/kit/auto",
                       json={"text": "记忆包括短时记忆", "vocab": VOCAB, "material_id": 1,
                             "map_version": "v1"})
    assert body.status_code == 200
    data = body.json()
    assert data["total_propositions"] == 2
    assert len(data["fingerprint"]) == 16
    assert [c["label"] for c in data["concepts"]] == \
        ["记忆", "短时记忆", "记忆系统"]


def test_同一文本两次裁出同一指纹(client, monkeypatch):
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=(
                      cand("记忆", "包括", "短时记忆"),)))
    payload = {"text": "记忆包括短时记忆", "vocab": VOCAB, "material_id": 1, "map_version": "v1"}
    a = client.post("/api/kit/auto", json=payload).json()
    b = client.post("/api/kit/auto", json=payload).json()
    assert a["fingerprint"] == b["fingerprint"]


def seeded_thresholds():
    return Thresholds(s1_max=0.30, s2_min=0.50, s3_max=0.60, s4_max_z=2.0,
                      min_props=10, baseline_source="开发期冻结图",
                      baseline_n=12)


def test_抽崩时返回可能不可信与信号原值(client, monkeypatch):
    """12 条孤立命题：S1/S2 触发，命题数够多，于是置标记并给文案。"""
    threshold_store.save(deps.get_conn(), seeded_thresholds())
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=tuple(
                      cand("甲%d" % i, "属于", "乙%d" % i)
                      for i in range(12))))
    data = client.post("/api/kit/auto",
                       json={"text": "甲属于乙。" * 20, "vocab": VOCAB, "material_id": 1,
                             "map_version": "v1"}).json()
    assert data["possibly_inaccurate"] is True
    assert data["message"].startswith("本次组件抽取可能不可信")
    signals = {s["name"]: s for s in data["signals"]}
    assert set(signals) == {"S1", "S2", "S3", "S4"}
    assert signals["S1"]["triggered"] is True
    assert signals["S1"]["value"] is not None
    assert signals["S1"]["threshold"] == 0.30
    assert signals["S4"]["value"] is None
    assert data["calibrated"] is True
    assert data["baseline_n"] == 12
    assert data["baseline_source"] == "开发期冻结图"


def test_阈值未校准时只带原值不提示(client, monkeypatch):
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=tuple(
                      cand("甲%d" % i, "属于", "乙%d" % i)
                      for i in range(12))))
    data = client.post("/api/kit/auto",
                       json={"text": "甲属于乙。" * 20, "vocab": VOCAB,
                             "material_id": 1, "map_version": "v1"}).json()
    assert data["possibly_inaccurate"] is False
    assert data["message"] == ""
    assert data["calibrated"] is False
    signals = {s["name"]: s for s in data["signals"]}
    assert signals["S1"]["value"] is not None
    assert signals["S1"]["triggered"] is False
    assert signals["S1"]["threshold"] is None


def test_健康抽取不置不可信标记(client, monkeypatch):
    pairs = [("记忆", "包括", "短时记忆"), ("短时记忆", "包括", "长时记忆"),
             ("长时记忆", "包括", "记忆"), ("感觉记忆", "属于", "记忆")]
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=tuple(
                      cand(*p) for p in pairs)))
    data = client.post("/api/kit/auto",
                       json={"text": "记忆包括短时记忆", "vocab": VOCAB, "material_id": 1,
                             "map_version": "v1"}).json()
    assert data["possibly_inaccurate"] is False
    assert data["message"] == ""


def test_抽不出命题时返回_422(client, monkeypatch):
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=()))
    resp = client.post("/api/kit/auto",
                       json={"text": "无关文本", "vocab": VOCAB, "material_id": 1,
                             "map_version": "v1"})
    assert resp.status_code == 422


def filled_config():
    return extractconfig.ExtractConfig(
        provider=extractconfig.OPENAI_COMPATIBLE, model="some-model",
        base_url="http://127.0.0.1:8788", timeout_s=60, max_chars=12000,
        enabled=True)


def test_未配密钥时返回_503(client, monkeypatch):
    monkeypatch.delenv(KEY, raising=False)
    monkeypatch.setattr(routes_text, "_config", filled_config)
    resp = client.post("/api/kit/auto",
                       json={"text": "记忆包括短时记忆", "vocab": VOCAB, "material_id": 1,
                             "map_version": "v1"})
    assert resp.status_code == 503


def test_抽取接口带回证据片段(client, monkeypatch):
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=(
                      triple.TripleCandidate(
                          head="记忆", connection="包括", tail="短时记忆",
                          confidence=0.9, evidence="记忆包括短时记忆",
                          suspect=True),)))
    data = client.post("/api/extract",
                       json={"text": "记忆包括短时记忆",
                             "vocab": VOCAB}).json()
    assert data["triples"][0]["evidence"] == "记忆包括短时记忆"
    assert data["triples"][0]["suspect"] is True


def test_命中题库时不重抽模型(client, monkeypatch):
    calls = []

    def fake(text, vocab, cfg=None, engine=None):
        calls.append(text)
        return triple.ExtractionResult(vocab=vocab, triples=(
            cand("记忆", "包括", "短时记忆"),))

    patch_extract(monkeypatch, fake)
    first = client.post("/api/kit/auto",
                        json={"text": "记忆包括短时记忆", "vocab": VOCAB,
                              "material_id": 1, "map_version": "v1"}).json()
    assert first["from_bank"] is False
    assert first["map_version"] == "v1"
    second = client.post("/api/kit/auto",
                         json={"text": "完全不同的原文", "vocab": VOCAB,
                               "material_id": 1, "map_version": "v9"}).json()
    assert len(calls) == 1
    assert second["from_bank"] is True
    assert second["map_version"] == "v1"
    assert second["fingerprint"] == first["fingerprint"]


def test_同一教材同一词表换原文仍复用(client, monkeypatch):
    """命中条件是教材 + 词表版本；已冻结的图不因换原文而重抽。"""
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=(
                      cand("记忆", "包括", "短时记忆"),)))
    a = client.post("/api/kit/auto",
                    json={"text": "甲", "vocab": VOCAB, "material_id": 1,
                          "map_version": "v1"}).json()
    b = client.post("/api/kit/auto",
                    json={"text": "乙", "vocab": VOCAB, "material_id": 1,
                          "map_version": "v1"}).json()
    assert (a["map_version"], b["map_version"]) == ("v1", "v1")
    assert b["from_bank"] is True


def test_同一教材换词表版本另开版本(client, monkeypatch):
    answer = [cand("记忆", "包括", "短时记忆")]

    def fake(text, vocab, cfg=None, engine=None):
        return triple.ExtractionResult(vocab=vocab, triples=tuple(answer))

    patch_extract(monkeypatch, fake)
    other_vocab = {"vocab_id": "心理学", "version": "v2",
                   "connections": ["包括", "属于"]}
    a = client.post("/api/kit/auto",
                    json={"text": "甲", "vocab": VOCAB, "material_id": 1,
                          "map_version": "v1"}).json()
    answer[:] = [cand("短时记忆", "包括", "长时记忆")]
    b = client.post("/api/kit/auto",
                    json={"text": "乙", "vocab": other_vocab, "material_id": 1,
                          "map_version": "v1"}).json()
    assert (a["map_version"], b["map_version"]) == ("v1", "v2")
    assert b["from_bank"] is False


def test_机器侧丢弃写进留档(client, monkeypatch):
    text = "记忆包括短时记忆。"

    def run(text, vocab, cfg=None, engine=None):
        got = triple.ExtractionResult(
            vocab=vocab, triples=(cand("记忆", "包括", "短时记忆"),))
        return got, (extraction.DiscardedCandidate(
            head="记忆", connection="包含", tail="编码",
            reason="连接词不在词表"),)
    monkeypatch.setattr(extract_service, "extract_and_discards", run)
    resp = client.post("/api/kit/auto",
                       json={"text": text, "vocab": VOCAB, "material_id": 1,
                             "map_version": "v1"})
    assert resp.status_code == 200
    digest = extract_service.sha256(text)
    assert discard_store.by_text(deps.get_conn(), digest) == (
        ("记忆", "包含", "编码", "连接词不在词表"),)


def test_没有丢弃时不写丢弃表(client, fake):
    client.post("/api/kit/auto",
                json={"text": "记忆包括短时记忆。", "vocab": VOCAB,
                      "material_id": 1, "map_version": "v1"})
    assert discard_store.count(deps.get_conn()) == 0


def test_不同教材互不命中(client, monkeypatch):
    patch_extract(monkeypatch,
                  lambda text, vocab, cfg=None, engine=None:
                  triple.ExtractionResult(vocab=vocab, triples=(
                      cand("记忆", "包括", "短时记忆"),)))
    client.post("/api/kit/auto",
                json={"text": "甲", "vocab": VOCAB, "material_id": 1,
                      "map_version": "v1"})
    other = client.post("/api/kit/auto",
                        json={"text": "甲", "vocab": VOCAB, "material_id": 2,
                              "map_version": "v1"}).json()
    assert other["from_bank"] is False
