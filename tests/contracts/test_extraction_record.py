import inspect

import pytest

import kbp.contracts.extraction as extraction
import kbp.contracts.extractconfig as extractconfig
import kbp.contracts.targetmap as targetmap
import kbp.contracts.triple as triple


def make_config():
    return extractconfig.default_config()


def make_record():
    return extraction.ExtractionRecord(
        batch_id="b1",
        vocab=triple.Vocab(vocab_id="心理学", vocab_version="v1",
                           connections=("属于",)),
        config=make_config(), text_sha256="a" * 64, chars=1000,
        sections=3, raw='{"propositions": []}', triples=(), created_at="2026-10-26")


def test_留档记录不可变():
    with pytest.raises(Exception):
        make_record().batch_id = "b2"


def test_留档不含密钥字段():
    names = {f.name for f in extraction.ExtractionRecord.__dataclass_fields__.values()}
    assert not any("key" in n or "token" in n or "secret" in n for n in names)


def test_配置快照可空三元组():
    assert make_record().triples == ()


def test_默认配置不预设服务商():
    cfg = make_config()
    assert cfg.provider in extractconfig.PROVIDERS
    assert cfg.base_url == "" and cfg.model == ""


def test_填好地址与模型即可用():
    cfg = extractconfig.ExtractConfig(
        provider=extractconfig.OPENAI_COMPATIBLE, model="some-model",
        base_url="http://127.0.0.1:8788", timeout_s=60, max_chars=12000,
        enabled=True)
    assert extractconfig.config_error(cfg) == ""


def test_留档可回填冻结图的版本与指纹():
    record = make_record()
    assert (record.map_version, record.fingerprint) == ("", "")
    filled = extraction.ExtractionRecord(
        batch_id=record.batch_id, vocab=record.vocab, config=record.config,
        text_sha256=record.text_sha256, chars=record.chars,
        sections=record.sections, raw=record.raw, triples=record.triples,
        created_at=record.created_at, map_version="v3", fingerprint="fp3")
    assert (filled.map_version, filled.fingerprint) == ("v3", "fp3")


def test_留档存储协议方法名固定():
    names = [n for n in extraction.ExtractionStore.__dict__
             if not n.startswith("_")]
    assert names == ["save", "load", "by_text", "attach_map"]


def test_指纹签名稳定():
    assert list(inspect.signature(
        targetmap.content_fingerprint).parameters) == ["concepts", "propositions"]
