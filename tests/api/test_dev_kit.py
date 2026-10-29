"""开发者模式落库：改后的图进库，读图与提交都按改后的来。"""

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
PASSWORD = "1234321"

# 冻结图是 c1 记忆 / c2 短时记忆 / c3 记忆系统，命题 c1-包括->c2、c2-属于->c3
WIDE = {"concepts": [{"concept_id": "c1", "label": "记忆"},
                     {"concept_id": "c2", "label": "短时记忆"},
                     {"concept_id": "c3", "label": "记忆系统"},
                     {"concept_id": "c4", "label": "长时记忆"}],
        "connections": ["包括", "属于"],
        "propositions": [{"head_id": "c1", "connection": "包括", "tail_id": "c2"},
                         {"head_id": "c2", "connection": "属于",
                          "tail_id": "c3"},
                         {"head_id": "c1", "connection": "包括",
                          "tail_id": "c4"}]}


@pytest.fixture
def client(monkeypatch):
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)

    def run(text, vocab, cfg=None, engine=None):
        triples = tuple(triple.TripleCandidate(head=h, connection=c, tail=t,
                                               confidence=0.9)
                        for h, c, t in TRIPLES)
        return extract_service.Details(
            result=triple.ExtractionResult(vocab=vocab, triples=triples))

    monkeypatch.setattr(extract_service, "extract_details", run)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


def freeze(client):
    body = {"text": "记忆包括短时记忆", "vocab": VOCAB, "material_id": 1}
    return client.post("/api/kit/auto", json=body)


def dev(client, **params):
    q = {"material_id": 1, "map_version": "v1"}
    q.update(params)
    return client.get("/api/dev/kit", params=q)


def put(client, patch=None, **kw):
    body = {"material_id": 1, "map_version": "v1", "password": PASSWORD}
    body.update(WIDE)
    body.update(kw)
    if patch:
        body.update(patch)
    return client.put("/api/dev/kit", json=body)


def drop(client, password=PASSWORD):
    return client.request("DELETE", "/api/dev/kit", json={
        "material_id": 1, "map_version": "v1", "password": password,
        "concepts": [], "connections": [], "propositions": []})


def labels(body):
    return [c["label"] for c in body["concepts"]]


def test_没改过读回冻结图(client):
    freeze(client)
    body = dev(client).json()
    assert body["edited"] is False and body["updated_at"] == ""
    assert labels(body) == ["记忆", "短时记忆", "记忆系统"]
    assert body["total_propositions"] == 2


def test_改了就进库并标出改过(client):
    freeze(client)
    body = put(client).json()
    assert body["edited"] is True and body["updated_at"]
    assert labels(body) == ["记忆", "短时记忆", "记忆系统", "长时记忆"]
    assert body["total_propositions"] == 3
    assert dev(client).json()["total_propositions"] == 3


def test_改后读图走的是库里的图(client):
    freeze(client)
    put(client)
    body = client.get("/api/kit/entry",
                      params={"material_id": 1, "map_version": "v1"}).json()
    assert "长时记忆" in labels(body)
    triples = [(p["head_id"], p["connection"], p["tail_id"])
               for p in body["propositions"]]
    assert ("c1", "包括", "c4") in triples


def test_改后指纹与版本号照旧(client):
    first = freeze(client).json()
    after = put(client).json()
    assert after["map_version"] == first["map_version"] == "v1"


def test_改后提交按新图校验(client):
    freeze(client)
    put(client)
    body = client.post("/api/draft", json={
        "map_version": "v1", "mode": "test", "participant_id": 7,
        "material_id": 1, "time_point": "post", "submit_seq": 1,
        "propositions": [{"head_id": "c1", "connection": "包括",
                          "tail_id": "c4"}]})
    assert body.status_code == 200, body.text


def test_密码不对拒改也拒撤(client):
    freeze(client)
    assert put(client, password="0000").status_code == 403
    put(client)
    assert drop(client, password="0000").status_code == 403
    assert dev(client).json()["edited"] is True


def test_密码不对时库里一个字不动(client):
    freeze(client)
    put(client, password="0000")
    assert dev(client).json()["edited"] is False


def test_图不成立就拒改并说明原因(client):
    freeze(client)
    bad = {"propositions": [{"head_id": "c1", "connection": "包括",
                             "tail_id": "c1"}]}
    r = put(client, patch=bad)
    assert r.status_code == 400
    assert "自环" in r.json()["detail"]
    assert dev(client).json()["edited"] is False


def test_命题用了不存在的概念就拒(client):
    freeze(client)
    bad = {"concepts": WIDE["concepts"][:3],
           "propositions": WIDE["propositions"]}
    r = put(client, patch=bad)
    assert r.status_code == 400
    assert "c4" in r.json()["detail"]


def test_撤销回到冻结图(client):
    freeze(client)
    put(client)
    body = drop(client).json()
    assert body["edited"] is False and body["updated_at"] == ""
    assert body["total_propositions"] == 2
    assert "长时记忆" not in labels(body)


def test_撤销没改过的也不报错(client):
    freeze(client)
    body = drop(client).json()
    assert body["edited"] is False and body["total_propositions"] == 2


def test_版本不存在返_404(client):
    freeze(client)
    assert dev(client, map_version="v9").status_code == 404
    assert put(client, map_version="v9").status_code == 404


def test_改过的那一批按库里存的原样回(client):
    freeze(client)
    put(client, patch={"propositions": WIDE["propositions"][:2]})
    body = dev(client).json()
    assert labels(body) == ["记忆", "短时记忆", "记忆系统", "长时记忆"]
    assert len(body["propositions"]) == 2
    parts = client.get("/api/kit/entry",
                       params={"material_id": 1, "map_version": "v1"}).json()
    assert labels(parts) == ["记忆", "短时记忆", "记忆系统", "长时记忆"]
    assert len(parts["propositions"]) == 2


def test_没被命题用上的连接词也留在回包里(client):
    freeze(client)
    put(client, patch={"connections": ["包括", "属于", "依赖"]})
    body = dev(client).json()
    assert body["connections"] == ["包括", "属于", "依赖"]
