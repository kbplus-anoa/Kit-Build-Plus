import inspect

import kbp.contracts.extractconfig as extractconfig
import pytest


def make(**kw):
    base = dict(provider=extractconfig.DEEPSEEK,
                model=extractconfig.DEFAULT_MODEL,
                base_url=extractconfig.DEFAULT_BASE,
                timeout_s=60, max_chars=12000, enabled=True)
    base.update(kw)
    return extractconfig.ExtractConfig(**base)


def test_供应商只列_deepseek():
    assert extractconfig.PROVIDERS == ("deepseek",)


def test_默认模型名为_deepseek_flash():
    assert extractconfig.DEFAULT_MODEL == "deepseek-flash"


def test_默认地址为_openai_兼容根():
    assert extractconfig.DEFAULT_BASE == "https://api.deepseek.com"


def test_合法配置无错误():
    assert extractconfig.config_error(make()) == ""


def test_未知供应商被拒():
    assert "供应商" in extractconfig.config_error(make(provider="openai"))


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


def test_配置不可变():
    with pytest.raises(Exception):
        make().model = "x"


def test_错误判定签名稳定():
    assert list(inspect.signature(extractconfig.config_error).parameters) == [
        "config"]
