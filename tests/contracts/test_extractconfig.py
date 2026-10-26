import inspect

import kbp.contracts.extractconfig as extractconfig
import pytest


def make(**kw):
    base = dict(provider=extractconfig.OPENAI_COMPATIBLE,
                model="some-model", base_url="http://127.0.0.1:8788",
                timeout_s=60, max_chars=12000, enabled=True)
    base.update(kw)
    return extractconfig.ExtractConfig(**base)


def test_只有自定义_openai_兼容一种供应商():
    assert extractconfig.PROVIDERS == ("openai_compatible",)


def test_供应商文案是人话():
    assert extractconfig.PROVIDER_LABELS[extractconfig.OPENAI_COMPATIBLE] == \
        "自定义 / OpenAI 兼容"


def test_不写死任何具体服务商():
    """协议只有一套，枚举里不该出现某家公司的名字。"""
    for name in extractconfig.PROVIDERS:
        assert "deepseek" not in name and "openai" != name


def test_密钥变量名通用():
    assert extractconfig.key_env(extractconfig.OPENAI_COMPATIBLE) == "KBP_API_KEY"


def test_未知供应商无密钥变量():
    assert extractconfig.key_env("anthropic") == ""


def test_合法配置无错误():
    assert extractconfig.config_error(make()) == ""


def test_未知供应商被拒():
    assert "供应商" in extractconfig.config_error(
        make(provider="deepseek"))


def test_空模型名被拒():
    assert "模型" in extractconfig.config_error(make(model="  "))


def test_空地址被拒():
    assert "地址" in extractconfig.config_error(make(base_url=""))


def test_非_http_地址被拒():
    assert "地址" in extractconfig.config_error(make(base_url="ftp://x"))


def test_超时越界被拒():
    assert "超时" in extractconfig.config_error(make(timeout_s=0))
    assert "超时" in extractconfig.config_error(
        make(timeout_s=extractconfig.MAX_TIMEOUT_S + 1))


def test_字数上限须为正():
    assert "字数" in extractconfig.config_error(make(max_chars=0))


def test_未启用时配置可用():
    assert extractconfig.config_error(make(enabled=False)) == ""


def test_默认配置不预设服务商():
    cfg = extractconfig.default_config()
    assert cfg.provider == extractconfig.OPENAI_COMPATIBLE
    assert cfg.base_url == "" and cfg.model == ""


def test_历史供应商值归一():
    assert extractconfig.canonical_provider("deepseek") == \
        extractconfig.OPENAI_COMPATIBLE


def test_已是新值时不改动():
    assert extractconfig.canonical_provider(extractconfig.OPENAI_COMPATIBLE) == \
        extractconfig.OPENAI_COMPATIBLE


def test_配置不可变():
    with pytest.raises(Exception):
        make().model = "x"


def test_错误判定签名稳定():
    assert list(inspect.signature(extractconfig.config_error).parameters) == [
        "config"]
