"""上传路由：真落盘真解析，纯文本走本地解析，不碰云端。"""

import pytest
from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.main as main
from kbp.api.bootstrap import create_schema

TEXT = "记忆包括感觉记忆。感觉记忆包括短时记忆。短时记忆经过复述转入长时记忆。"


@pytest.fixture
def client(tmp_path, monkeypatch):
    import sqlite3
    monkeypatch.setenv("KBP_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("KBP_INGEST_CACHE", str(tmp_path / "cache"))
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


def _upload(client, name="记忆.txt", data=TEXT.encode("utf-8")):
    return client.post("/api/upload", files={"file": (name, data, "text/plain")})


def test_上传_txt_回正文与教材号(client):
    resp = _upload(client)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["file_name"] == "记忆.txt" and body["ext"] == "txt"
    assert body["material_id"] >= 1
    assert body["text"].startswith("记忆包括感觉记忆")


def test_重复上传同一份复用教材号(client):
    first = _upload(client).json()["material_id"]
    again = _upload(client, name="改名.txt").json()["material_id"]
    assert again == first


def test_不支持的格式被拒并说清格式(client):
    resp = _upload(client, name="记忆.docx", data=b"x")
    assert resp.status_code == 400
    assert "这个格式暂不支持" in resp.json()["detail"]


def test_空文件被拒(client):
    assert _upload(client, data=b"").status_code == 400


def test_没有正文的文件被拒(client):
    resp = _upload(client, name="空.txt", data="  \n ".encode("utf-8"))
    assert resp.status_code == 400
    assert "没有可用的文字" in resp.json()["detail"]


def test_没抽出kit前教材不列出(client):
    """上传成功但还没裁出 kit：列表里不出现，免得点了报 503。"""
    _upload(client)
    assert client.get("/api/materials").json()["items"] == []


def test_抽出kit后教材才列出(client):
    mid = _upload(client).json()["material_id"]
    import kbp.ingest.materials as materials
    materials.mark_ready(deps.get_conn(), mid)
    items = client.get("/api/materials").json()["items"]
    assert [i["file_name"] for i in items] == ["记忆.txt"]


def test_删除教材连原文一起清掉(client, tmp_path):
    mid = _upload(client).json()["material_id"]
    resp = client.delete("/api/materials/" + str(mid))
    assert resp.status_code == 200 and resp.json()["ok"] is True
    assert client.get("/api/materials/" + str(mid) + "/text").status_code == 404
    assert list((tmp_path / "uploads").iterdir()) == []


def test_删除不存在的教材_404(client):
    assert client.delete("/api/materials/999").status_code == 404


def test_重读旧教材回正文(client):
    mid = _upload(client).json()["material_id"]
    body = client.get("/api/materials/" + str(mid) + "/text").json()
    assert body["material_id"] == mid
    assert body["file_name"] == "记忆.txt"
    assert body["text"].startswith("记忆包括感觉记忆")


def test_重读不存在的教材_404(client):
    assert client.get("/api/materials/999/text").status_code == 404


def test_原文被删后重读_404(client, tmp_path):
    mid = _upload(client).json()["material_id"]
    for path in (tmp_path / "uploads").iterdir():
        path.unlink()
    resp = client.get("/api/materials/" + str(mid) + "/text")
    assert resp.status_code == 404


def test_解析失败不留下落盘文件(client, tmp_path):
    _upload(client, name="空.txt", data="  \n ".encode("utf-8"))
    assert list((tmp_path / "uploads").iterdir()) == []
