import json

import httpx
import pytest

import kbp.contracts.extractconfig as extractconfig
import kbp.contracts.triple as triple
import kbp.extract.chat_client as chat_client
import kbp.extract.engine as engine_mod
import kbp.extract.extract_service as service
import kbp.extract.normalize as normalize
import kbp.extract.prompt as prompt
import kbp.extract.vocab as vocab_mod
import kbp.extract.window as window

VOCAB_JSON = {"vocab_id": "心理学", "version": "v1",
              "connections": ["属于", "导致"]}


def make_vocab():
    return vocab_mod.build(dict(VOCAB_JSON))


def make_config(**kw):
    base = dict(provider=extractconfig.OPENAI_COMPATIBLE,
                model="some-model",
                base_url="http://127.0.0.1:8788",
                timeout_s=60, max_chars=12000, enabled=True)
    base.update(kw)
    return extractconfig.ExtractConfig(**base)


def body(*props):
    return {"propositions": list(props)}


def prop(head, connection, tail, evidence="", confidence=None):
    item = {"head": head, "connection": connection, "tail": tail,
            "evidence": evidence}
    if confidence is not None:
        item["confidence"] = confidence
    return item


class FakeEngine:
    """测试方自建引擎：按调用顺序返回预设结果，不发起任何网络请求。"""

    def __init__(self, batches):
        self.batches = list(batches)
        self.calls = []

    def extract(self, text, vocab, config):
        self.calls.append((text, vocab, config))
        if not self.batches:
            return ()
        return tuple(self.batches.pop(0))


def cand(head, connection, tail):
    return triple.TripleCandidate(head=head, connection=connection,
                                  tail=tail, confidence=0.5)


def test_词表缺字段报错():
    with pytest.raises(vocab_mod.VocabError):
        vocab_mod.build({"vocab_id": "x", "version": "v1"})


def test_词表重复连接词报错():
    raw = dict(VOCAB_JSON)
    raw["connections"] = ["属于", "属于"]
    with pytest.raises(vocab_mod.VocabError):
        vocab_mod.build(raw)


def test_词表可从文件读(tmp_path):
    p = tmp_path / "v.json"
    p.write_text(json.dumps(VOCAB_JSON, ensure_ascii=False), "utf-8")
    assert vocab_mod.load(str(p)).connections == ("属于", "导致")


def test_提示词里出现_json_字样与输出样例():
    msgs = prompt.build(make_vocab(), "原文", make_config())
    system = msgs[0]["content"]
    assert "json" in system
    assert '"propositions"' in system


def test_提示词把连接词写进用户消息():
    msgs = prompt.build(make_vocab(), "记忆属于认知", make_config())
    assert "属于" in msgs[1]["content"] and "导致" in msgs[1]["content"]


def test_提示词按配置截断正文():
    msgs = prompt.build(make_vocab(), "记" * 100, make_config(max_chars=10))
    assert "记" * 10 in msgs[1]["content"]
    assert "记" * 11 not in msgs[1]["content"]


def test_越界连接词被丢弃():
    got = normalize.to_candidates(
        body(prop("记忆", "包含", "编码"), prop("记忆", "属于", "认知")),
        make_vocab())
    assert [c.connection for c in got] == ["属于"]


def test_自环命题被丢弃():
    got = normalize.to_candidates(body(prop("记忆", "属于", "记忆")),
                                  make_vocab())
    assert got == []


def test_重复命题只留一条():
    p = prop("记忆", "属于", "认知")
    assert len(normalize.to_candidates(body(p, dict(p)), make_vocab())) == 1


def test_缺_propositions_字段报错():
    with pytest.raises(normalize.ParseError):
        normalize.to_candidates({"triples": []}, make_vocab())


def test_propositions_不是数组报错():
    with pytest.raises(normalize.ParseError):
        normalize.to_candidates({"propositions": {}}, make_vocab())


def test_证据缺失时退回原文首句():
    got = normalize.to_candidates(body(prop("记忆", "属于", "认知")),
                                  make_vocab(), "记忆属于认知。第二句。")
    assert got[0].evidence == "记忆属于认知"


def test_证据缺失且无原文时留空串():
    got = normalize.to_candidates(body(prop("记忆", "属于", "认知")),
                                  make_vocab(), "")
    assert got[0].evidence == ""


def test_置信度缺失时按一处理():
    got = normalize.to_candidates(body(prop("记忆", "属于", "认知")),
                                  make_vocab())
    assert got[0].confidence == 1.0


def test_置信度越界被夹到零一之间():
    got = normalize.to_candidates(
        body(prop("记忆", "属于", "认知", confidence=9)), make_vocab())
    assert got[0].confidence == 1.0


def test_长段落按字上限硬切():
    chunks = window.split("甲" * 100, window=40)
    assert len(chunks) == 3
    assert chunks[0] == "甲" * 40


def test_空行分段不跨段合并():
    assert window.split("第一段\n\n第二段") == ["第一段", "第二段"]


def test_空文本不切():
    assert window.split("   ") == []


def test_归一化用于去重():
    assert window.normalize("  A  B ") == "a b"


def test_引擎收到的词表与配置就是传入的那份():
    engine = FakeEngine([()])
    cfg = make_config()
    vocab = make_vocab()
    service.extract("文本", vocab, cfg, engine=engine)
    assert engine.calls[0][1] is vocab and engine.calls[0][2] is cfg


def test_跨段重复命题只留一条():
    engine = FakeEngine([[cand("记忆", "属于", "认知")],
                         [cand("记忆", "属于", "认知")]])
    result = service.extract("甲段\n乙段", make_vocab(), make_config(),
                             engine=engine)
    assert len(result.triples) == 1


def test_结果按置信度降序():
    low = triple.TripleCandidate(head="遗忘", connection="导致", tail="衰退",
                                 confidence=0.4)
    high = triple.TripleCandidate(head="复习", connection="导致", tail="保持",
                                  confidence=0.9)
    result = service.extract("文本", make_vocab(), make_config(),
                             engine=FakeEngine([[low, high]]))
    assert [c.confidence for c in result.triples] == [0.9, 0.4]


def test_空词表拒绝抽取():
    bad = triple.Vocab(vocab_id="x", vocab_version="v1", connections=())
    with pytest.raises(service.ExtractError):
        service.extract("文本", bad, make_config(), engine=FakeEngine([()]))


def test_配置不可用时拒绝抽取():
    bad = make_config(timeout_s=0)
    with pytest.raises(service.ExtractError):
        service.extract("文本", make_vocab(), bad, engine=FakeEngine([()]))


def test_未知供应商时拒绝抽取():
    bad = make_config(provider="unknown")
    with pytest.raises(service.ExtractError):
        service.extract("文本", make_vocab(), bad, engine=FakeEngine([()]))


def test_留档记录原文指纹与统计量():
    result = service.extract("记忆属于认知", make_vocab(), make_config(),
                             engine=FakeEngine([[cand("记忆", "属于", "认知")]]))
    rec = service.record(result, "b1", make_config(), "记忆属于认知",
                         sections=1, created_at="2026-10-26T10:00:00")
    assert rec.chars == 6 and len(rec.text_sha256) == 64
    assert rec.triples == result.triples


def test_相同原文指纹相同_不同原文指纹不同():
    assert service.sha256("abc") == service.sha256("abc")
    assert service.sha256("abc") != service.sha256("abd")


def test_接口地址拼成_openai_兼容路径():
    cfg = make_config(base_url="http://127.0.0.1:8788/")
    assert chat_client.endpoint(cfg) == \
        "http://127.0.0.1:8788/v1/chat/completions"


def test_未配置密钥时明确报错(monkeypatch):
    monkeypatch.delenv(extractconfig.KEY_ENV_NAME,
                       raising=False)
    with pytest.raises(chat_client.MissingKey):
        chat_client.api_key(make_config())


def test_密钥只从对应供应商的环境变量读(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME, "sk-dev")
    assert chat_client.has_key(make_config()) is True
    monkeypatch.delenv(extractconfig.KEY_ENV_NAME)
    assert chat_client.has_key(make_config()) is False


def test_未知供应商无密钥变量(monkeypatch):
    assert extractconfig.key_env("anthropic") == ""


def _transport(status, payload):
    def handler(request):
        return httpx.Response(status, json=payload)
    return httpx.MockTransport(handler)


def _ok(content):
    return {"choices": [{"message": {"content": json.dumps(content)}}]}


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


def test_错误信息不含密钥与环境变量值(monkeypatch):
    monkeypatch.setenv(extractconfig.KEY_ENV_NAME,
                       "sk-very-secret")
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
