"""草稿接口测试：保存、读回、覆盖、提交后清理。"""


import pytest

from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.main as main
import kbp.kit.bank_store as bank_store
import kbp.kit.kit_service as kit_service
import kbp.kit.split as split
from kbp.api.bootstrap import create_schema
from kbp.contracts.targetbank import ADJUDICATED, BankEntry


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


def _seed(client) -> dict:
    """裁定一批后把冻结图登记进题库，模拟自动路裁出的图。"""
    client.post("/api/adjudicate", json=ADJ)
    conn = deps.get_conn()
    target = kit_service.freeze_batch(conn, "b1", "v1")
    bank_store.register(conn, BankEntry(
        material_id=1, vocab_version=target.vocab.vocab_version,
        source=ADJUDICATED, in_use=False,
        created_at="2026-10-27T00:00:00+00:00", target_map=target))
    return {c.label: c.concept_id for c in split.split(target).concepts}


def _draft(ids, propositions, submit_seq=1, time_point="post", mode="test"):
    return {"map_version": "v1", "mode": mode, "condition": "exp",
            "participant_id": 1, "material_id": 1, "time_point": time_point,
            "submit_seq": submit_seq, "propositions": propositions}


def _prop(ids, head="记忆", tail="感觉记忆"):
    return {"head_id": ids[head], "connection": "包括", "tail_id": ids[tail]}


def test_草稿保存后能原样读回(client):
    ids = _seed(client)
    resp = client.post("/api/draft", json=_draft(ids, [_prop(ids)]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["fingerprint"] and body["saved_at"]
    got = client.get("/api/draft", params={
        "participant_id": 1, "material_id": 1, "time_point": "post",
        "submit_seq": 1}).json()
    assert got["propositions"] == [_prop(ids)]
    assert got["fingerprint"] == body["fingerprint"]


def test_同一键再保存覆盖旧草稿(client):
    ids = _seed(client)
    client.post("/api/draft", json=_draft(ids, [_prop(ids)]))
    client.post("/api/draft",
                json=_draft(ids, [_prop(ids, tail="短时记忆")]))
    got = client.get("/api/draft", params={
        "participant_id": 1, "material_id": 1, "time_point": "post",
        "submit_seq": 1}).json()
    assert got["propositions"] == [_prop(ids, tail="短时记忆")]


def test_读不存在的草稿返回_404(client):
    _seed(client)
    resp = client.get("/api/draft", params={
        "participant_id": 1, "material_id": 1, "time_point": "post",
        "submit_seq": 3})
    assert resp.status_code == 404


def test_草稿越界零件被拒_400(client):
    ids = _seed(client)
    bad = [{"head_id": "c9", "connection": "包括", "tail_id": ids["记忆"]}]
    assert client.post("/api/draft", json=_draft(ids, bad)).status_code == 400


def test_学习模式按序号各存一份草稿(client):
    ids = _seed(client)
    client.post("/api/draft", json=_draft(ids, [_prop(ids)], submit_seq=1))
    client.post("/api/draft", json=_draft(ids, [], submit_seq=2))
    params = {"participant_id": 1, "material_id": 1, "time_point": "post"}
    first = client.get("/api/draft", params={**params, "submit_seq": 1}).json()
    second = client.get("/api/draft", params={**params, "submit_seq": 2}).json()
    assert len(first["propositions"]) == 1 and second["propositions"] == []


def test_提交后同键草稿消失(client):
    ids = _seed(client)
    client.post("/api/draft", json=_draft(ids, [_prop(ids)]))
    resp = client.post("/api/submit", json=_draft(ids, [_prop(ids)]))
    assert resp.status_code == 200 and resp.json()["submit_seq"] == 1
    got = client.get("/api/draft", params={
        "participant_id": 1, "material_id": 1, "time_point": "post",
        "submit_seq": 1})
    assert got.status_code == 404


def test_题库里的图不带批次也能提交(client):
    ids = _seed(client)
    body = _draft(ids, [_prop(ids)])
    assert "batch_id" not in body
    resp = client.post("/api/submit", json=body)
    assert resp.status_code == 200
    assert resp.json()["fms"] == 50.0
