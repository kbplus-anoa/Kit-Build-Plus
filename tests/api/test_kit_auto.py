"""运行期自动裁 kit：文本 → 抽取 → 冻结 → 拆零件。"""

import pytest

from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.main as main
import kbp.api.routes_text as routes_text
import kbp.contracts.extractconfig as extractconfig
import kbp.contracts.triple as triple
import kbp.extract.extract_service as extract_service
from kbp.api.bootstrap import create_schema

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
    monkeypatch.setattr(extract_service, "extract",
                        lambda text, vocab, cfg=None, engine=None:
                        triple.ExtractionResult(vocab=vocab,
                                                triples=engine_or(engine)))
    return engine


def engine_or(engine):
    return engine if engine else ()


def test_自动裁出零件与指纹(client, monkeypatch):
    monkeypatch.setattr(extract_service, "extract",
                        lambda text, vocab, cfg=None, engine=None:
                        triple.ExtractionResult(vocab=vocab, triples=(
                            cand("记忆", "包括", "短时记忆"),
                            cand("短时记忆", "属于", "记忆系统"))))
    body = client.post("/api/kit/auto",
                       json={"text": "记忆包括短时记忆", "vocab": VOCAB,
                             "map_version": "v1"})
    assert body.status_code == 200
    data = body.json()
    assert data["total_propositions"] == 2
    assert len(data["fingerprint"]) == 16
    assert [c["label"] for c in data["concepts"]] == \
        ["记忆", "短时记忆", "记忆系统"]


def test_同一文本两次裁出同一指纹(client, monkeypatch):
    monkeypatch.setattr(extract_service, "extract",
                        lambda text, vocab, cfg=None, engine=None:
                        triple.ExtractionResult(vocab=vocab, triples=(
                            cand("记忆", "包括", "短时记忆"),)))
    payload = {"text": "记忆包括短时记忆", "vocab": VOCAB, "map_version": "v1"}
    a = client.post("/api/kit/auto", json=payload).json()
    b = client.post("/api/kit/auto", json=payload).json()
    assert a["fingerprint"] == b["fingerprint"]


def test_抽不出命题时返回_422(client, monkeypatch):
    monkeypatch.setattr(extract_service, "extract",
                        lambda text, vocab, cfg=None, engine=None:
                        triple.ExtractionResult(vocab=vocab, triples=()))
    resp = client.post("/api/kit/auto",
                       json={"text": "无关文本", "vocab": VOCAB,
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
                       json={"text": "记忆包括短时记忆", "vocab": VOCAB,
                             "map_version": "v1"})
    assert resp.status_code == 503


def test_抽取接口带回证据片段(client, monkeypatch):
    monkeypatch.setattr(extract_service, "extract",
                        lambda text, vocab, cfg=None, engine=None:
                        triple.ExtractionResult(vocab=vocab, triples=(
                            triple.TripleCandidate(head="记忆", connection="包括",
                                                   tail="短时记忆",
                                                   confidence=0.9,
                                                   evidence="记忆包括短时记忆",
                                                   suspect=True),)))
    data = client.post("/api/extract",
                       json={"text": "记忆包括短时记忆",
                             "vocab": VOCAB}).json()
    assert data["triples"][0]["evidence"] == "记忆包括短时记忆"
    assert data["triples"][0]["suspect"] is True
