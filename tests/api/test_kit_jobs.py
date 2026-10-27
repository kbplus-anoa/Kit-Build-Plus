"""后台裁 kit 任务：切段预报、逐段进度与失败原因。"""

import time

import pytest
from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.kit_flow as kit_flow
import kbp.api.main as main
import kbp.contracts.extractconfig as extractconfig
import kbp.contracts.triple as triple
import kbp.extract.extract_service as extract_service
from kbp.api.bootstrap import create_schema

VOCAB = {"vocab_id": "心理学", "version": "v1",
         "connections": ["包括", "属于"]}

PAYLOAD = {"text": "记忆包括短时记忆", "vocab": VOCAB, "material_id": 1,
           "map_version": "v1"}


def make_config(**kw):
    base = dict(provider=extractconfig.OPENAI_COMPATIBLE, model="some-model",
                base_url="http://127.0.0.1:8788", timeout_s=60,
                max_chars=12000, enabled=True)
    base.update(kw)
    return extractconfig.ExtractConfig(**base)


@pytest.fixture
def client():
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


def cand(head, connection, tail):
    return triple.TripleCandidate(head=head, connection=connection,
                                  tail=tail, confidence=0.9)


def fake_details(triples, steps):
    """替身：按给定步数逐段报进度，返回给定候选。"""
    def run(text, vocab, cfg=None, engine=None, on_step=None):
        for done in range(1, steps + 1):
            if on_step is not None:
                on_step(done, steps)
        return extract_service.Details(
            result=triple.ExtractionResult(vocab=vocab, triples=triples),
            sections=steps)
    return run


def wait(client, job_id, limit=200):
    for _ in range(limit):
        data = client.get("/api/kit/jobs/" + job_id).json()
        if data["state"] != "running":
            return data
        time.sleep(0.02)
    raise AssertionError("任务一直没有结束")


def test_切段预报回段数与字数(client, monkeypatch):
    monkeypatch.setattr(kit_flow, "load_config", lambda: make_config(max_chars=3))
    data = client.post("/api/kit/preview",
                       json={"text": "甲。\n\n乙。\n\n丙。"}).json()
    assert data["segments"] == 3
    assert data["chars"] == len("甲。\n\n乙。\n\n丙。")


def test_后台任务抽完回结果与进度(client, monkeypatch):
    monkeypatch.setattr(extract_service, "extract_details", fake_details((
        cand("记忆", "包括", "短时记忆"),
        cand("短时记忆", "属于", "记忆系统")), 2))
    started = client.post("/api/kit/jobs", json=PAYLOAD).json()
    assert started["state"] == "running"
    got = wait(client, started["job_id"])
    assert got["state"] == "done"
    assert (got["segments"], got["done"]) == (2, 2)
    assert got["result"]["total_propositions"] == 2
    assert [c["label"] for c in got["result"]["concepts"]] == \
        ["记忆", "短时记忆", "记忆系统"]


def test_后台任务失败带回原因(client, monkeypatch):
    monkeypatch.setattr(extract_service, "extract_details",
                        fake_details((), 1))
    started = client.post("/api/kit/jobs", json=PAYLOAD).json()
    got = wait(client, started["job_id"])
    assert got["state"] == "failed"
    assert got["result"] is None
    assert got["error"].startswith("抽出的图不足以成题")


def test_查不存在的任务_404(client):
    assert client.get("/api/kit/jobs/nope").status_code == 404
