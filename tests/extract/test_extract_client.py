"""OpenAI 兼容客户端的网络行为：重试、报错、密钥不出现在错误里。"""

import json

import httpx
import kbp.contracts.extractconfig as extractconfig
import kbp.extract.chat_client as chat_client
import kbp.extract.engine as engine_mod
import pytest
from tests.extract.helpers import make_config, make_vocab, prop


def _transport(status, payload):
    def handler(request):
        return httpx.Response(status, json=payload)
    return httpx.MockTransport(handler)


def _ok(content):
    return {"choices": [{"message": {"content": json.dumps(content)}}]}


def test_思考强度随请求发出(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return httpx.Response(200, json=_ok({"propositions": []}))

    chat_client.chat(make_config(reasoning_effort="high"), [],
                     transport=httpx.MockTransport(handler))
    assert seen["reasoning_effort"] == "high"


def test_留空时不发思考强度(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return httpx.Response(200, json=_ok({"propositions": []}))

    chat_client.chat(make_config(), [], transport=httpx.MockTransport(handler))
    assert "reasoning_effort" not in seen


def test_接口地址拼成_openai_兼容路径():
    cfg = make_config(base_url="http://127.0.0.1:8788/")
    assert chat_client.endpoint(cfg) == \
        "http://127.0.0.1:8788/v1/chat/completions"


def test_未配置密钥时明确报错(monkeypatch):
    monkeypatch.delenv(extractconfig.KEY_ENV_NAME, raising=False)
    with pytest.raises(chat_client.MissingKey):
        chat_client.api_key(make_config())


def test_密钥只从环境变量读(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    assert chat_client.has_key(make_config()) is True
    monkeypatch.delenv(extractconfig.KEY_ENV_NAME)
    assert chat_client.has_key(make_config()) is False


def test_未知供应商无密钥变量():
    assert extractconfig.key_env("anthropic") == ""


def test_正常调用返回解析后的对象(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    transport = _transport(200, _ok({"propositions": []}))
    got = chat_client.chat(make_config(), [], transport=transport)
    assert got == {"propositions": []}


def test_空内容时重试后成功(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json={
                "choices": [{"message": {"content": ""}}]})
        return httpx.Response(200, json=_ok({"propositions": []}))
    got = chat_client.chat(make_config(), [],
                           transport=httpx.MockTransport(handler))
    assert got == {"propositions": []} and calls["n"] == 2


def test_限流按次数重试后成功(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": "rate"})
        return httpx.Response(200, json=_ok({"propositions": []}))
    assert chat_client.chat(make_config(), [],
                            transport=httpx.MockTransport(handler)) == \
        {"propositions": []}


def test_重试耗尽后报错(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    transport = _transport(429, {"error": "rate"})
    with pytest.raises(chat_client.ApiError):
        chat_client.chat(make_config(), [], transport=transport)


def test_非重试状态码立即失败且不重试(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(401, json={"error": "bad key"})
    with pytest.raises(chat_client.ApiError):
        chat_client.chat(make_config(), [],
                         transport=httpx.MockTransport(handler))
    assert calls["n"] == 1


def test_错误信息不含密钥(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-very-secret")
    transport = _transport(401, {"error": "unauthorized"})
    with pytest.raises(chat_client.ApiError) as info:
        chat_client.chat(make_config(), [], transport=transport)
    assert "sk-very-secret" not in str(info.value)


def test_返回不是合法_json_时报错(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    bad = {"choices": [{"message": {"content": "not json"}}]}
    with pytest.raises(chat_client.ApiError):
        chat_client.chat(make_config(), [], transport=_transport(200, bad))


def test_响应缺_choices_时报错(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    with pytest.raises(chat_client.ApiError):
        chat_client.chat(make_config(), [],
                         transport=_transport(200, {"nope": 1}))


def test_引擎一次抽取走完整链路(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    payload = _ok({"propositions": [prop("记忆", "属于", "认知", "记忆属于认知"),
                                    prop("记忆", "包含", "编码")]})
    got = engine_mod.ChatEngine(transport=_transport(200, payload)).extract(
        "记忆属于认知", make_vocab(), make_config())
    assert [c.connection for c in got] == ["属于"]
    assert got[0].evidence == "记忆属于认知"
