"""历史与草稿：刷新或换设备后，做过的记录要能找回来。"""

import pytest
from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.main as main
import kbp.contracts.triple as triple
import kbp.extract.extract_service as extract_service
from kbp.api.bootstrap import create_schema

VOCAB = {"vocab_id": "心理学", "version": "v1",
         "connections": ["包括", "属于"]}
TRIPLES = (("记忆", "包括", "短时记忆"), ("短时记忆", "属于", "记忆系统"))


@pytest.fixture
def client(monkeypatch):
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)

    def fake(text, vocab, cfg=None, engine=None, on_step=None):
        return extract_service.Details(
            result=triple.ExtractionResult(
                vocab=vocab,
                triples=tuple(triple.TripleCandidate(head=h, connection=c,
                                                     tail=t, confidence=0.9)
                              for h, c, t in TRIPLES)))

    monkeypatch.setattr(extract_service, "extract_details", fake)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


def build_kit(client) -> str:
    body = {"text": "记忆包括短时记忆", "vocab": VOCAB, "material_id": 1}
    resp = client.post("/api/kit/auto", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()["map_version"]


def submit(client, version: str, mode: str = "study", props=None):
    props = props if props is not None else [
        {"head_id": "c1", "connection": "包括", "tail_id": "c2"}]
    return client.post("/api/submit", json={
        "map_version": version, "mode": mode, "condition": "exp",
        "participant_id": 1, "material_id": 1, "time_point": "post",
        "propositions": props})


def test_提交后能按人列出记录(client):
    version = build_kit(client)
    assert submit(client, version).status_code == 200
    items = client.get("/api/records", params={"participant_id": 1}).json()["items"]
    assert len(items) == 1
    got = items[0]
    assert got["scored"] is True
    assert (got["correct_propositions"], got["total_propositions"]) == (1, 2)
    assert got["fms"] == 50.0
    assert got["lacking"] == 1
    assert got["mode"] == "study" and got["map_version"] == version
    assert got["propositions"] == [
        {"head_id": "c1", "connection": "包括", "tail_id": "c2"}]
    assert len(got["target_propositions"]) == 2
    assert [c["label"] for c in got["concepts"]] == \
        ["记忆", "短时记忆", "记忆系统"]


def test_测验提交后再交被拒但记录还在(client):
    version = build_kit(client)
    assert submit(client, version, mode="test").status_code == 200
    again = submit(client, version, mode="test")
    assert again.status_code == 409
    assert "测验模式已提交" in again.json()["detail"]
    items = client.get("/api/records", params={"participant_id": 1}).json()["items"]
    assert [item["mode"] for item in items] == ["test"]


def test_记录可按教材筛(client):
    version = build_kit(client)
    submit(client, version)
    other = client.get("/api/records",
                       params={"participant_id": 1, "material_id": 2}).json()
    assert other["items"] == []


def test_当前草稿存得进读得回(client):
    version = build_kit(client)
    body = {"map_version": version, "mode": "study", "participant_id": 1,
            "material_id": 1, "time_point": "post",
            "propositions": [{"head_id": "c1", "connection": "包括",
                              "tail_id": "c2"}]}
    saved = client.post("/api/draft/current", json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json()["submit_seq"] == 1
    got = client.get("/api/draft/current", params={
        "participant_id": 1, "material_id": 1, "time_point": "post"}).json()
    assert got["propositions"] == body["propositions"]
    assert got["fingerprint"] == saved.json()["fingerprint"]
    listed = client.get("/api/drafts", params={"participant_id": 1}).json()
    assert len(listed["items"]) == 1


def test_没有草稿时_404(client):
    resp = client.get("/api/draft/current", params={
        "participant_id": 1, "material_id": 1, "time_point": "post"})
    assert resp.status_code == 404
    assert "草稿不存在" in resp.json()["detail"]


def test_草稿存两遍覆盖成最新的一条(client):
    version = build_kit(client)
    body = {"map_version": version, "mode": "study", "participant_id": 1,
            "material_id": 1, "time_point": "post", "propositions": []}
    assert client.post("/api/draft/current", json=body).status_code == 200
    body["propositions"] = [{"head_id": "c1", "connection": "包括",
                             "tail_id": "c2"}]
    assert client.post("/api/draft/current", json=body).status_code == 200
    listed = client.get("/api/drafts", params={"participant_id": 1}).json()
    assert len(listed["items"]) == 1
    got = client.get("/api/draft/current", params={
        "participant_id": 1, "material_id": 1, "time_point": "post"}).json()
    assert got["submit_seq"] == 1
    assert len(got["propositions"]) == 1
