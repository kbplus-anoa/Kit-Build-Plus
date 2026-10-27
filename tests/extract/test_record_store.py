"""抽取留档落库：原始输出、配置快照与图版本对账。"""

import sqlite3

import pytest

import kbp.contracts.extractconfig as extractconfig
import kbp.contracts.extraction as extraction
import kbp.contracts.triple as triple
import kbp.extract.extract_service as service
import kbp.extract.record_store as store

TEXT = "记忆包括短时记忆。"


@pytest.fixture
def conn():
    got = sqlite3.connect(":memory:")
    store.ensure(got)
    yield got
    got.close()


def vocab(version="v1"):
    return triple.Vocab(vocab_id="心理学", vocab_version=version,
                        connections=("包括", "属于"))


def config():
    return extractconfig.ExtractConfig(
        provider="openai_compatible", model="m", base_url="http://x",
        timeout_s=30, max_chars=1000, enabled=True)


def result():
    return triple.ExtractionResult(vocab=vocab(), triples=(
        triple.TripleCandidate(head="记忆", connection="包括",
                               tail="短时记忆", evidence="记忆包括短时记忆",
                               confidence=1.0, suspect=True),
        triple.TripleCandidate(head="短时记忆", connection="属于", tail="记忆",
                               confidence=0.4),
    ))


def build(batch="b1"):
    return service.record(
        result(), batch, config(), TEXT, sections=2, raw='{"p": []}',
        created_at="2026-10-27T00:00:00+00:00",
        discards=(extraction.DiscardedCandidate(
            head="记忆", connection="包含", tail="编码",
            reason="连接词不在词表"),))


def test_留档往返保住全部字段(conn):
    store.save(conn, build())
    got = store.load(conn, "b1")
    assert got.batch_id == "b1"
    assert got.vocab.connections == ("包括", "属于")
    assert (got.config.provider, got.config.model, got.config.base_url) == (
        "openai_compatible", "m", "http://x")
    assert (got.config.timeout_s, got.config.max_chars,
            got.config.enabled) == (30, 1000, True)
    assert got.text_sha256 == service.sha256(TEXT)
    assert (got.chars, got.sections, got.raw) == (
        len(TEXT), 2, '{"p": []}')
    assert got.triples == result().triples
    assert got.discards[0].reason == "连接词不在词表"
    assert got.created_at.startswith("2026-10-27")


def test_同批次不可覆盖(conn):
    store.save(conn, build())
    with pytest.raises(store.RecordError):
        store.save(conn, build())


def test_空批次拒收(conn):
    with pytest.raises(store.RecordError):
        store.save(conn, build(batch=""))


def test_没有留档读回为空(conn):
    assert store.load(conn, "nope") is None
    assert store.by_text(conn, service.sha256(TEXT)) == ()


def test_同一原文多批按入库先后(conn):
    store.save(conn, build("b1"))
    store.save(conn, build("b2"))
    got = store.by_text(conn, service.sha256(TEXT))
    assert [item.batch_id for item in got] == ["b1", "b2"]


def test_回填图版本与指纹(conn):
    store.save(conn, build())
    store.attach_map(conn, "b1", "v3", "abc123")
    got = store.load(conn, "b1")
    assert (got.map_version, got.fingerprint) == ("v3", "abc123")


def test_回填不存在的批次报错(conn):
    with pytest.raises(store.RecordError):
        store.attach_map(conn, "ghost", "v1", "abc")


def test_条数(conn):
    assert store.count(conn) == 0
    store.save(conn, build())
    assert store.count(conn) == 1
