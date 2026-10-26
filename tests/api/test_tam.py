"""TAM 路由：量表条目与各构念 α；本层只算不存。"""

import pytest

from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.main as main
from kbp.api.bootstrap import create_schema

PU_IDS = ("PU1", "PU2", "PU3", "PU4")
M1 = [(3, 4, 5, 3), (4, 4, 4, 4), (2, 3, 4, 2), (5, 5, 4, 5),
      (3, 4, 4, 3), (4, 3, 5, 4), (2, 4, 3, 2)]


@pytest.fixture
def client():
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


def rows(matrix, ids):
    return [{"participant_id": 1 + r, "item_id": iid, "score": float(v)}
            for r, row in enumerate(matrix) for iid, v in zip(ids, row)]


def score(participant_id, item_id, value):
    return {"participant_id": participant_id, "item_id": item_id, "score": value}


def report(body, construct):
    return next(r for r in body["reports"] if r["construct_code"] == construct)


def test_条目接口返回十四题与六点上下限(client):
    body = client.get("/api/tam/items").json()
    assert (body["likert_min"], body["likert_max"]) == (1, 6)
    assert body["min_alpha"] == 0.7
    assert len(body["items"]) == 14


def test_条目接口带回构念中文名与可选题(client):
    body = client.get("/api/tam/items").json()
    assert [c["label"] for c in body["constructs"]] == \
        ["感知有用性", "感知易用性", "使用意图", "态度"]
    assert [i["item_id"] for i in body["items"] if i["optional"]] == \
        ["ATT1", "ATT2", "ATT3"]
    pu1 = next(i for i in body["items"] if i["item_id"] == "PU1")
    assert pu1["construct_label"] == "感知有用性" and pu1["optional"] is False


def test_条目接口不收人口学题(client):
    items = client.get("/api/tam/items").json()["items"]
    text = " ".join(i["text"] for i in items)
    assert "性别" not in text and "年龄段" not in text


def test_α_按构念返回四份报告(client):
    body = client.post("/api/tam/alpha", json={"rows": rows(M1, PU_IDS)}).json()
    assert [r["construct_code"] for r in body["reports"]] == ["PU", "PEOU", "BI", "ATT"]
    assert [r["k"] for r in body["reports"]] == [4, 4, 3, 3]
    pu = report(body, "PU")
    assert (pu["alpha"], pu["n"], pu["passed"], pu["threshold"]) == (0.7816, 7, True, 0.7)
    assert pu["construct_label"] == "感知有用性"


def test_α_缺答整人剔除(client):
    data = {"rows": rows(M1, PU_IDS)[:-1]}
    body = client.post("/api/tam/alpha", json=data).json()
    assert report(body, "PU")["n"] == 6


def test_α_没人做的构念不算通过(client):
    body = client.post("/api/tam/alpha", json={"rows": []}).json()
    att = report(body, "ATT")
    assert (att["n"], att["alpha"], att["passed"]) == (0, None, False)


def test_α_未知题号返回_400(client):
    r = client.post("/api/tam/alpha", json={"rows": [score(1, "ZZ9", 3)]})
    assert r.status_code == 400
    assert "未知题号" in r.json()["detail"] and "ZZ9" in r.json()["detail"]


def test_得分越界返回_422(client):
    for value in (0, 7):
        r = client.post("/api/tam/alpha", json={"rows": [score(1, "PU1", value)]})
        assert r.status_code == 422


def test_α_用不上的人群不参与(client):
    data = {"rows": rows(M1, PU_IDS) + [score(1, "BI1", 4), score(1, "BI2", 5)]}
    body = client.post("/api/tam/alpha", json=data).json()
    assert report(body, "BI")["n"] == 0
    assert report(body, "PU")["alpha"] == 0.7816
