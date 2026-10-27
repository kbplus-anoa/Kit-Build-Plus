"""读 .env：解析键值、已存在的环境变量优先、文件不在时静默。"""

import os

import kbp.api.envfile as envfile


def test_解析键值(tmp_path):
    text = "# 注释\n\nA=1\nB = 值 \nC=\"引号\"\n不是键值\n"
    assert envfile.parse(text) == {"A": "1", "B": "值", "C": "引号"}


def test_值里的等号保留():
    assert envfile.parse("URL=https://x.test?a=b")["URL"] == \
        "https://x.test?a=b"


def test_补进环境变量(tmp_path, monkeypatch):
    file = tmp_path / "x.env"
    file.write_text("KBP_ENVFIELD_TEST=abc\n", encoding="utf-8")
    monkeypatch.setenv("KBP_ENV_FILE", str(file))
    monkeypatch.delenv("KBP_ENVFIELD_TEST", raising=False)
    assert envfile.apply() == {"KBP_ENVFIELD_TEST": "abc"}
    assert os.environ["KBP_ENVFIELD_TEST"] == "abc"


def test_已有的环境变量优先(tmp_path, monkeypatch):
    file = tmp_path / "x.env"
    file.write_text("KBP_ENVFIELD_TEST=file\n", encoding="utf-8")
    monkeypatch.setenv("KBP_ENV_FILE", str(file))
    monkeypatch.setenv("KBP_ENVFIELD_TEST", "shell")
    assert envfile.apply() == {}
    assert os.environ["KBP_ENVFIELD_TEST"] == "shell"


def test_文件不存在时什么都不做(tmp_path, monkeypatch):
    monkeypatch.setenv("KBP_ENV_FILE", str(tmp_path / "missing.env"))
    assert envfile.apply() == {}
