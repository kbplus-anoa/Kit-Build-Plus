"""配置路由：读写抽取配置，密钥只报是否已配置。"""

import pytest

from fastapi.testclient import TestClient

import kbp.api.deps as deps
import kbp.api.main as main
import kbp.contracts.extractconfig as extractconfig
from kbp.api.bootstrap import create_schema

KEY = extractconfig.KEY_ENV_NAME

BODY = {"provider": extractconfig.OPENAI_COMPATIBLE, "model": "some-model",
        "base_url": "http://127.0.0.1:8788", "timeout_s": 60,
        "max_chars": 12000, "enabled": True}


ENV_KEYS = (extractconfig.ENV_MODEL, extractconfig.ENV_BASE_URL,
            extractconfig.ENV_TIMEOUT_S, extractconfig.ENV_MAX_CHARS,
            extractconfig.ENV_ENABLED, KEY)


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    """挡掉开发机上真实的 .env 与 shell 变量，空配置用例才稳定。"""
    monkeypatch.setenv("KBP_ENV_FILE", str(tmp_path / "none.env"))
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def client():
    import sqlite3
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    create_schema(conn)
    deps.reset_conn(conn)
    yield TestClient(main.app)
    deps.reset_conn(None)
    conn.close()


def test_未保存时返回空配置(client, clean_env):
    body = client.get("/api/config").json()
    assert body["provider"] == extractconfig.OPENAI_COMPATIBLE
    assert body["base_url"] == ""


def test_未保存时读_env里的模型(client, monkeypatch, clean_env):
    """模型与地址写在 .env 里，界面不用先填也能抽出目标图。"""
    monkeypatch.setenv(extractconfig.ENV_MODEL, "env-model")
    monkeypatch.setenv(extractconfig.ENV_BASE_URL, "http://127.0.0.1:8799/")
    body = client.get("/api/config").json()
    assert body["model"] == "env-model"
    assert body["base_url"] == "http://127.0.0.1:8799"


def test_库里的设置盖过_env(client, monkeypatch):
    monkeypatch.setenv(extractconfig.ENV_MODEL, "env-model")
    client.put("/api/config", json=BODY)
    assert client.get("/api/config").json()["model"] == "some-model"


def test_未保存时的空配置带中文原因(client, clean_env):
    body = client.get("/api/config").json()
    assert "模型" in body["error"]


def test_保存后读回一致(client):
    assert client.put("/api/config", json=BODY).status_code == 200
    body = client.get("/api/config").json()
    assert body["max_chars"] == 12000 and body["enabled"] is True
    assert body["model"] == "some-model"


def test_响应只报是否已配置密钥(client, monkeypatch):
    monkeypatch.setenv(KEY, "sk-very-secret")
    body = client.get("/api/config").json()
    assert body["has_key"] is True
    assert "sk-very-secret" not in str(body)
    assert body["key_env"] == KEY


def test_响应不含密钥本身(client, monkeypatch):
    monkeypatch.setenv(KEY, "sk-very-secret")
    client.put("/api/config", json=BODY)
    assert "sk-very-secret" not in client.get("/api/config").text


def test_未配置密钥时报告未配置(client, monkeypatch, clean_env):
    monkeypatch.delenv(KEY, raising=False)
    assert client.get("/api/config").json()["has_key"] is False


def test_不支持的供应商被拒(client):
    bad = dict(BODY, provider="deepseek")
    assert client.put("/api/config", json=bad).status_code == 400


def test_非法地址被拒(client):
    assert client.put("/api/config",
                      json=dict(BODY, base_url="ftp://x")).status_code == 400


def test_超时越界被拒(client):
    """越界值在请求模型处就被拦下（422），不进业务层。"""
    assert client.put("/api/config",
                      json=dict(BODY, timeout_s=0)).status_code == 422


def test_保存后可重复覆盖(client):
    client.put("/api/config", json=BODY)
    client.put("/api/config", json=dict(BODY, max_chars=3000))
    assert client.get("/api/config").json()["max_chars"] == 3000


def test_历史供应商值读回时归一(client):
    """库里可能留着旧值，读出来要与当前枚举对得上。"""
    conn = deps.get_conn()
    conn.execute("INSERT OR REPLACE INTO extract_config VALUES (1, 'deepseek',"
                 " 'some-model', 'http://127.0.0.1:8788', 60, 12000, 1)")
    conn.commit()
    assert client.get("/api/config").json()["provider"] == \
        extractconfig.OPENAI_COMPATIBLE


def test_换服务商只改地址与模型(client):
    """协议只有一套，换服务商不动代码。"""
    other = dict(BODY, model="another-model",
                 base_url="https://api.example.com")
    assert client.put("/api/config", json=other).status_code == 200
    assert client.get("/api/config").json()["model"] == "another-model"
