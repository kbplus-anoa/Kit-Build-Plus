"""TAM 路由：条目、作答落库、按库里的作答算 α。

问卷整份提交，一人一题一行；α 只从库读，调用方不能再送一份数进来现算。
"""

import pytest

from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.main as main
import kbp.quiz.alpha
import kbp.quiz.tam_store
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


def answers(matrix, ids):
    return [{"item_id": iid, "score": float(v)}
            for row in matrix for iid, v in zip(ids, row)]


def post(client, participant_id, pairs, **kw):
    body = {"participant_id": participant_id,
            "answers": [{"item_id": i, "score": float(v)} for i, v in pairs]}
    body.update(kw)
    return client.post("/api/tam/answers", json=body)


def fill(client, matrix, ids):
    for r, row in enumerate(matrix):
        resp = post(client, 1 + r, list(zip(ids, row)))
        assert resp.status_code == 200, resp.text


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


def test_作答落库后α按构念读库算出(client):
    fill(client, M1, PU_IDS)
    body = client.get("/api/tam/alpha").json()
    assert [r["construct_code"] for r in body["reports"]] == ["PU", "PEOU", "BI", "ATT"]
    assert [r["k"] for r in body["reports"]] == [4, 4, 3, 3]
    pu = report(body, "PU")
    assert (pu["alpha"], pu["n"], pu["passed"], pu["threshold"]) == (0.7816, 7, True, 0.7)
    assert pu["construct_label"] == "感知有用性"


def test_整份作答一次写入并回条数(client):
    resp = post(client, 1, list(zip(PU_IDS, M1[0])))
    assert resp.status_code == 200
    assert resp.json() == {"participant_id": 1, "saved": 4}
    assert kbp.quiz.tam_store.count(deps.get_conn()) == 4


def test_同题重答覆盖不追加行(client):
    fill(client, M1, PU_IDS)
    resp = post(client, 1, [("PU1", 6)])
    assert resp.status_code == 200
    conn = deps.get_conn()
    assert kbp.quiz.tam_store.count(conn) == 28
    rows = kbp.quiz.tam_store.rows(conn)
    assert len(rows) == 28 and (1, "PU1", 6.0) in rows
    matrix = [(6,) + M1[0][1:]] + list(M1[1:])
    expect_rows = [(r + 1, item, float(v)) for r, row in enumerate(matrix)
                   for item, v in zip(PU_IDS, row)]
    expect = next(r for r in kbp.quiz.alpha.alpha_by_construct(expect_rows)
                  if r.construct == "PU")
    assert report(client.get("/api/tam/alpha").json(), "PU")["alpha"] == expect.alpha


def test_重答带回自己的时间戳(client):
    post(client, 3, [("PU1", 4), ("PU2", 4)], answered_at="2026-10-27T10:00:00+00:00")
    post(client, 3, [("PU1", 5)], answered_at="2026-10-27T11:00:00+00:00")
    row = deps.get_conn().execute(
        "SELECT score, answered_at FROM tam_answer"
        " WHERE participant_id=3 AND item_id='PU1'").fetchone()
    assert tuple(row) == (5.0, "2026-10-27T11:00:00+00:00")


def test_答案时间留空取服务端当前时间(client):
    post(client, 2, [("PU1", 4)])
    stamp = deps.get_conn().execute(
        "SELECT answered_at FROM tam_answer WHERE participant_id=2").fetchone()[0]
    assert stamp.endswith("+00:00") and len(stamp) == 25


def test_α缺答整人剔除(client):
    fill(client, M1[:-1], PU_IDS)
    assert report(client.get("/api/tam/alpha").json(), "PU")["n"] == 6


def test_α空库不算通过(client):
    att = report(client.get("/api/tam/alpha").json(), "ATT")
    assert (att["n"], att["alpha"], att["passed"]) == (0, None, False)


def test_α没人做的构念不参与(client):
    fill(client, M1, PU_IDS)
    post(client, 1, [("BI1", 4), ("BI2", 5)])
    body = client.get("/api/tam/alpha").json()
    assert report(body, "BI")["n"] == 0
    assert report(body, "PU")["alpha"] == 0.7816


def test_作答未知题号返回_400(client):
    r = post(client, 1, [("ZZ9", 3)])
    assert r.status_code == 400
    assert "未知题号" in r.json()["detail"] and "ZZ9" in r.json()["detail"]


def test_同一份卷子同题两答返回_400(client):
    r = post(client, 1, [("PU1", 3), ("PU1", 4)])
    assert r.status_code == 400
    assert "同题重复作答" in r.json()["detail"] and "PU1" in r.json()["detail"]


def test_得分越界返回_422(client):
    for value in (0, 7):
        assert post(client, 1, [("PU1", value)]).status_code == 422


def test_空作答返回_422(client):
    assert post(client, 1, []).status_code == 422
