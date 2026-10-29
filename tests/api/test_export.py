"""导出端到端：提交与作答落快照，导出按库检索并筛人。

旧路径是前端攒好整份行再 POST 进来，库里查不到这些列；现在写入侧随手存一份。
"""


import csv
import io


import pytest


from fastapi.testclient import TestClient  # noqa: E402

import kbp.api.deps as deps  # noqa: E402
import kbp.api.main as main  # noqa: E402
from kbp.api.bootstrap import create_schema  # noqa: E402

ADJ = {"batch_id": "b1",
       "vocab": {"vocab_id": "心理学", "version": "v1",
                 "connections": ["包括"]},
       "items": [
           {"head": "记忆", "connection": "包括", "tail": "感觉记忆",
            "confidence": 0.9, "decision": "accepted", "reason": ""},
           {"head": "感觉记忆", "connection": "包括", "tail": "短时记忆",
            "confidence": 0.9, "decision": "accepted", "reason": ""}]}


@pytest.fixture
def client():
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


def kit(client):
    """裁一次 kit，返回概念名到 id 的映射。"""
    body = client.post("/api/kit",
                       json={"batch_id": "b1", "map_version": "v1"}).json()
    return {c["label"]: c["concept_id"] for c in body["concepts"]}


def submit(client, ids, **kw):
    payload = {"batch_id": "b1", "map_version": "v1", "mode": "test",
               "condition": "exp",
               "participant_id": 1, "material_id": 1, "time_point": "post",
               "propositions": [{"head_id": ids["记忆"],
                                 "connection": "包括",
                                 "tail_id": ids["感觉记忆"]}]}
    payload.update(kw)
    resp = client.post("/api/submit", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def rows(content, name):
    """按 csv 表头取列，列序变化不影响断言。"""
    table = list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))
    return [dict(zip(table[0], line, strict=True)) for line in table[1:]]


def test_提交后导出被试级_csv(client):
    client.post("/api/adjudicate", json=ADJ)
    ids = kit(client)
    submit(client, ids, condition="exp")
    resp = client.get("/api/export/subject")
    assert resp.status_code == 200
    assert resp.content.startswith(b"\xef\xbb\xbf")
    got = rows(resp.content, "subject")
    assert len(got) == 1
    assert got[0]["correct_propositions"] == "1"
    assert got[0]["total_propositions"] == "2"
    assert got[0]["condition"] == "exp"


def test_导出带上提交端的抽崩标记与信号(client):
    client.post("/api/adjudicate", json=ADJ)
    ids = kit(client)
    submit(client, ids, is_practice=1, possibly_inaccurate=1,
           signal_isolated=0.1, signal_coverage=0.8)
    got = rows(client.get("/api/export/subject").content, "subject")
    assert got[0]["is_practice"] == "1"
    assert got[0]["possibly_inaccurate"] == "1"
    assert float(got[0]["孤立概念率"]) == 0.1
    assert float(got[0]["连接词覆盖率"]) == 0.8
    assert got[0]["基线偏离度"] == ""


def test_按被试筛选只出选中的人(client):
    client.post("/api/adjudicate", json=ADJ)
    ids = kit(client)
    submit(client, ids, participant_id=1)
    submit(client, ids, participant_id=2)
    got = rows(client.get("/api/export/subject?participant_id=2").content,
               "subject")
    assert [r["participant_id"] for r in got] == ["2"]


def test_未分组提交被拒(client):
    client.post("/api/adjudicate", json=ADJ)
    ids = kit(client)
    payload = {"batch_id": "b1", "map_version": "v1", "mode": "test",
               "participant_id": 1, "material_id": 1, "time_point": "post",
               "propositions": [{"head_id": ids["记忆"],
                                 "connection": "包括",
                                 "tail_id": ids["感觉记忆"]}]}
    assert client.post("/api/submit", json=payload).status_code == 422


def test_多选筛选合并成_或(client):
    client.post("/api/adjudicate", json=ADJ)
    ids = kit(client)
    submit(client, ids, participant_id=1)
    submit(client, ids, participant_id=2)
    submit(client, ids, participant_id=3)
    got = rows(client.get("/api/export/subject?participant_id=1"
                          "&participant_id=3").content, "subject")
    assert [r["participant_id"] for r in got] == ["1", "3"]


def test_预览与下载同一套列(client):
    client.post("/api/adjudicate", json=ADJ)
    ids = kit(client)
    submit(client, ids, participant_id=1, condition="exp")
    preview = client.get("/api/export/preview").json()
    table = list(csv.reader(io.StringIO(
        client.get("/api/export/subject").content.decode("utf-8-sig"))))
    assert preview["header"] == table[0]
    assert preview["rows"] == table[1:]
    assert preview["total"] == 1


def test_预览按_limit_截断但总数照给(client):
    client.post("/api/adjudicate", json=ADJ)
    ids = kit(client)
    for who in (1, 2, 3):
        submit(client, ids, participant_id=who)
    preview = client.get("/api/export/preview?limit=2").json()
    assert len(preview["rows"]) == 2
    assert preview["total"] == 3


def test_预览无记录返回_404(client):
    client.post("/api/adjudicate", json=ADJ)
    assert client.get("/api/export/preview").status_code == 404


def test_筛选无结果返回_404(client):
    client.post("/api/adjudicate", json=ADJ)
    ids = kit(client)
    submit(client, ids)
    assert client.get("/api/export/subject?participant_id=9").status_code == 404
