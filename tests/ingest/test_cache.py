"""解析缓存：同字节同版本不重复解析，落盘目录不入 git。"""

from pathlib import Path

import pytest

import kbp.ingest.cache as cache
import kbp.ingest.ingest_service as service
import kbp.ingest.textfile as textfile
from kbp.contracts.textdoc import OCR_CLOUD, TEXT_LAYER, TextDoc


@pytest.fixture(autouse=True)
def cache_dir(tmp_path, monkeypatch):
    monkeypatch.setenv(cache.DIR_ENV, str(tmp_path / "cache"))


def doc(text="正文", source=TEXT_LAYER):
    return TextDoc(text=text, source=source, file_name="a.txt",
                   has_ocr=False, page_count=0)


def test_同文件第二次不再解析(tmp_path, monkeypatch):
    p = tmp_path / "a.txt"
    p.write_bytes("正文".encode("utf-8"))
    calls = []
    real = textfile.read_text

    def counting(path):
        calls.append(path)
        return real(path)

    monkeypatch.setattr(textfile, "read_text", counting)
    first = service.ingest(str(p))
    second = service.ingest(str(p))
    assert calls == [str(p)]
    assert second.text == first.text
    assert second.file_name == "a.txt"


def test_字节变了就重新解析(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes("原文".encode("utf-8"))
    assert service.ingest(str(p)).text == "原文"
    p.write_bytes("改过".encode("utf-8"))
    assert service.ingest(str(p)).text == "改过"


def test_换解析器版本不复用(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"x")
    cache.save(str(p), doc(), version="1")
    assert cache.load(str(p), version="1") is not None
    assert cache.load(str(p), version="2") is None


def test_空文本不进缓存(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"x")
    cache.save(str(p), doc(text=""))
    assert cache.load(str(p)) is None


def test_坏缓存当未命中(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"x")
    cache.save(str(p), doc())
    Path(cache.path_for(str(p))).write_text("不是 json", "utf-8")
    assert cache.load(str(p)) is None


def test_缓存保住来源与页数(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"x")
    cache.save(str(p), TextDoc(text="扫描", source=OCR_CLOUD, file_name="a.txt",
                               has_ocr=True, page_count=3))
    got = cache.load(str(p))
    assert (got.text, got.source, got.has_ocr, got.page_count) == (
        "扫描", OCR_CLOUD, True, 3)


def test_默认目录落在仓库根_tmp(monkeypatch):
    monkeypatch.delenv(cache.DIR_ENV, raising=False)
    got = cache.dir_path()
    assert got.name == "ingest_cache" and got.parent.name == "tmp"
