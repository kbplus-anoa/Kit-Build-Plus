"""题库批次：抽崩后重抽另起一批，新旧并存，旧批可切回。"""

import pytest

from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.main as main
import kbp.contracts.triple as triple
import kbp.extract.extract_service as extract_service
from kbp.api.bootstrap import create_schema

VOCAB = {"vocab_id": "心理学", "version": "v1",
         "connections": ["包括", "属于"]}
A = (("记忆", "包括", "短时记忆"), ("短时记忆", "属于", "记忆系统"))
B = (("记忆", "包括", "长时记忆"), ("长时记忆", "属于", "记忆系统"))


@pytest.fixture
def client():
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


class Fake:
    """按调用次数给不同候选：第一次抽崩那批，第二次换一批。"""

    def __init__(self, monkeypatch):
        self.calls = 0
        self.batches = [A, B]
        monkeypatch.setattr(extract_service, "extract_details", self.run)

    def run(self, text, vocab, cfg=None, engine=None):
        batch = self.batches[min(self.calls, len(self.batches) - 1)]
        self.calls += 1
        triples = tuple(triple.TripleCandidate(head=h, connection=c, tail=t,
                                               confidence=0.9)
                        for h, c, t in batch)
        return extract_service.Details(
            result=triple.ExtractionResult(vocab=vocab, triples=triples))


def auto(client, **kw):
    body = {"text": "记忆包括短时记忆", "vocab": VOCAB, "material_id": 1}
    body.update(kw)
    return client.post("/api/kit/auto", json=body)


def versions(client, **params):
    q = {"material_id": 1}
    q.update(params)
    return client.get("/api/kit/versions", params=q)


def test_重抽另起一批旧批不动(client, monkeypatch):
    fake = Fake(monkeypatch)
    first = auto(client).json()
    second = auto(client, retry=True).json()
    assert (first["map_version"], second["map_version"]) == ("v1", "v2")
    assert first["fingerprint"] != second["fingerprint"]
    assert fake.calls == 2
    rows = versions(client).json()["versions"]
    assert [r["map_version"] for r in rows] == ["v1", "v2"]


def test_命中题库不调模型也不重抽(client, monkeypatch):
    fake = Fake(monkeypatch)
    auto(client)
    again = auto(client).json()
    assert again["from_bank"] is True and again["map_version"] == "v1"
    assert fake.calls == 1


def test_重抽内容相同仍回旧图(client, monkeypatch):
    fake = Fake(monkeypatch)
    auto(client)
    fake.batches = [A]  # 重抽还是同一批内容
    body = auto(client, retry=True).json()
    assert body["map_version"] == "v1" and body["from_bank"] is False
    assert len(versions(client).json()["versions"]) == 1


def test_版本列表按入库先后带指纹与来源(client, monkeypatch):
    Fake(monkeypatch)
    auto(client)
    auto(client, retry=True)
    rows = versions(client).json()["versions"]
    assert [r["map_version"] for r in rows] == ["v1", "v2"]
    assert all(r["source"] == "auto" and r["vocab_version"] == "v1" for r in rows)
    assert all(r["total_propositions"] == 2 and r["in_use"] is False for r in rows)
    assert all(len(r["fingerprint"]) == 16 and r["created_at"] for r in rows)


def test_版本列表可按词表版本筛(client, monkeypatch):
    Fake(monkeypatch)
    auto(client)
    other = dict(VOCAB, version="v2")
    auto(client, vocab=other, retry=True)
    assert [r["map_version"] for r in versions(client).json()["versions"]] == \
        ["v1", "v2"]
    only_v2 = versions(client, vocab_version="v2").json()["versions"]
    assert [r["vocab_version"] for r in only_v2] == ["v2"]


def test_版本列表空教材回空表(client):
    assert versions(client, material_id=9).json() == \
        {"material_id": 9, "versions": []}


def test_切回旧批标为投用(client, monkeypatch):
    Fake(monkeypatch)
    auto(client)
    auto(client, retry=True)
    body = client.post("/api/kit/use",
                       json={"material_id": 1, "map_version": "v1"}).json()
    assert body == {"material_id": 1, "map_version": "v1", "in_use": True}
    rows = versions(client).json()["versions"]
    assert [(r["map_version"], r["in_use"]) for r in rows] == \
        [("v1", True), ("v2", False)]


def test_切回不存在的版本返_404(client):
    r = client.post("/api/kit/use",
                    json={"material_id": 1, "map_version": "v9"})
    assert r.status_code == 404
    assert "v9" in r.json()["detail"]


def test_切回旧批后仍能按旧版建草稿(client, monkeypatch):
    Fake(monkeypatch)
    auto(client)
    auto(client, retry=True)
    client.post("/api/kit/use", json={"material_id": 1, "map_version": "v1"})
    body = client.post("/api/draft", json={
        "map_version": "v1", "mode": "test", "participant_id": 7,
        "material_id": 1, "time_point": "post", "submit_seq": 1,
        "propositions": []})
    assert body.status_code == 200, body.text
    assert body.json()["map_version"] == "v1"
