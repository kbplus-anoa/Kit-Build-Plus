"""路由层测试：用 TestClient 走真实 HTTP，不依赖外部服务。

每个用例用独立的 :memory: 库，避免互相污染。
"""


import pytest


from fastapi.testclient import TestClient  # noqa: E402

import kbp.api.deps as deps  # noqa: E402
import kbp.api.main as main  # noqa: E402
from kbp.api.bootstrap import create_schema  # noqa: E402


@pytest.fixture
def client():
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


ADJ = {"batch_id": "b1",
       "vocab": {"vocab_id": "心理学", "version": "v1",
                 "connections": ["包括"]},
       "items": [
           {"head": "记忆", "connection": "包括", "tail": "感觉记忆",
            "confidence": 0.9, "decision": "accepted", "reason": ""},
           {"head": "感觉记忆", "connection": "包括", "tail": "短时记忆",
            "confidence": 0.9, "decision": "accepted", "reason": ""}]}


def test_服务存活(client):
    assert client.get("/").status_code == 200


def test_健康检查报告表数(client):
    body = client.get("/api/health").json()
    assert body["ok"] is True and body["tables"] >= 6


def test_云端解析失败返回_503_并说清原因(client, monkeypatch):
    import kbp.ingest.ingest_service as ingest_service
    import kbp.ingest.ocr as ocr

    def boom(path):
        raise ocr.MinerUUnavailable("云端解析超时")

    monkeypatch.setattr(ingest_service, "ingest", boom)
    resp = client.post("/api/ingest", json={"path": "/tmp/scan.pdf"})
    assert resp.status_code == 503
    assert "扫描件需要云端解析" in resp.json()["detail"]


def test_裁定不死锁(client):
    """回归：曾因路由先持写锁再取连接而自锁超时。"""
    resp = client.post("/api/adjudicate", json=ADJ)
    assert resp.status_code == 200
    assert resp.json()["saved"] == 2


def test_重复批次被拒(client):
    client.post("/api/adjudicate", json=ADJ)
    assert client.post("/api/adjudicate", json=ADJ).status_code == 409


def test_拆_kit_返回零件(client):
    client.post("/api/adjudicate", json=ADJ)
    body = client.post("/api/kit",
                       json={"batch_id": "b1", "map_version": "v1"}).json()
    assert [c["label"] for c in body["concepts"]] == ["记忆", "感觉记忆", "短时记忆"]
    assert body["connections"] == ["包括"]


def test_缺批次时_kit_返回_404(client):
    assert client.post("/api/kit",
                       json={"batch_id": "x", "map_version": "v1"}).status_code == 404


def test_提交后评分并锁定(client):
    client.post("/api/adjudicate", json=ADJ)
    kit = client.post("/api/kit",
                      json={"batch_id": "b1", "map_version": "v1"}).json()
    ids = {c["label"]: c["concept_id"] for c in kit["concepts"]}
    resp = client.post("/api/submit", json={
        "batch_id": "b1", "map_version": "v1", "mode": "test",
        "participant_id": 1, "material_id": 1, "session": 1,
        "propositions": [{"head_id": ids["记忆"], "connection": "包括",
                          "tail_id": ids["感觉记忆"]}]})
    assert resp.status_code == 200
    assert resp.json()["fms"] == 50.0
    assert client.get("/api/lock?map_version=v1").json()["locked"] == "locked"


def test_越界零件提交被拒(client):
    client.post("/api/adjudicate", json=ADJ)
    resp = client.post("/api/submit", json={
        "batch_id": "b1", "map_version": "v1", "mode": "test",
        "participant_id": 1, "material_id": 1, "session": 1,
        "propositions": [{"head_id": "c9", "connection": "包括",
                          "tail_id": "c1"}]})
    assert resp.status_code == 400


def test_被试级导出带_BOM(client):
    body = {"rows": [{"participant_id": 1, "material_id": 1,
                      "target_map_version": "v1", "session": 1,
                      "mode": "test", "condition": "exp", "is_practice": 0,
                      "correct_propositions": 1, "total_propositions": 2,
                      "n_lacking": 1, "n_excessive": 0, "n_leaving": 0,
                      "n_reversed": 0, "possibly_inaccurate": 0,
                      "map_size": 1, "map_node_count": 2}]}
    resp = client.post("/api/export/subject", json=body)
    assert resp.status_code == 200
    assert resp.content.startswith(b"\xef\xbb\xbf")


def test_题级导出英文表头在前(client):
    body = {"rows": [{"participant_id": 1, "material_id": 1,
                      "target_map_version": "v1", "session": 1,
                      "question_id": "q1", "time_point": "pre",
                      "correct": 1, "qtype": "single",
                      "content_dimension": "记忆"}]}
    resp = client.post("/api/export/question", json=body)
    text = resp.content.decode("utf-8-sig")
    assert "答对" in text and "记忆" in text
