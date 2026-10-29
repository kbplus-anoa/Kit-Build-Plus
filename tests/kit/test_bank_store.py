import sqlite3

import pytest

import kbp.contracts.targetbank as targetbank
import kbp.contracts.targetmap as targetmap
import kbp.contracts.triple as triple
import kbp.kit._rules as rules
import kbp.kit.bank_store as bank_store
import kbp.kit.kit_service as kit_service

VOCAB = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("包括", "属于"))


def conn():
    connection = sqlite3.connect(":memory:")
    bank_store.ensure(connection)
    return connection


def target(version="v1", vocab=None):
    return targetmap.TargetMap(
        map_version=version, vocab=vocab or VOCAB,
        concepts=(targetmap.Concept(concept_id="c1", label="记忆"),
                  targetmap.Concept(concept_id="c2", label="短时记忆")),
        propositions=(targetmap.Proposition(head_id="c1", connection="包括",
                                            tail_id="c2"),),
        fingerprint="fp-" + version)


def entry(version="v1", material_id=1, created_at="2026-10-27T10:00:00",
          source=targetbank.AUTO, vocab=None):
    return targetbank.BankEntry(
        material_id=material_id, vocab_version=(vocab or VOCAB).vocab_version,
        source=source, in_use=False, created_at=created_at,
        target_map=target(version, vocab), batch_id="b1")


def test_登记后可按指纹查到同一张图():
    db = conn()
    bank_store.register(db, entry())
    found = bank_store.by_fingerprint(db, 1, "fp-v1")
    assert found.target_map.map_version == "v1"
    assert [c.label for c in found.target_map.concepts] == ["记忆", "短时记忆"]
    assert found.batch_id == "b1"


def test_按教材与版本号取回冻结图():
    db = conn()
    bank_store.register(db, entry())
    assert bank_store.by_version(db, 1, "v1").target_map.fingerprint == "fp-v1"
    assert bank_store.by_version(db, 1, "v9") is None
    assert bank_store.by_version(db, 2, "v1") is None
    assert bank_store.by_version(db, 1, "") is None


def test_同一教材版本号不可重复():
    db = conn()
    bank_store.register(db, entry())
    with pytest.raises(bank_store.BankError, match="版本号已存在"):
        bank_store.register(db, entry(created_at="2026-10-27T11:00:00"))


def test_同一张图不许登记两次():
    db = conn()
    bank_store.register(db, entry())
    dup = targetbank.BankEntry(
        material_id=1, vocab_version="v1", source=targetbank.AUTO,
        in_use=False, created_at="2026-10-27T11:00:00",
        target_map=targetmap.TargetMap(
            map_version="v2", vocab=VOCAB,
            concepts=target().concepts, propositions=target().propositions,
            fingerprint="fp-v1"))
    with pytest.raises(bank_store.BankError, match="同一张图已在库"):
        bank_store.register(db, dup)


def test_缺指纹的图拒绝入库():
    db = conn()
    bad = targetbank.BankEntry(
        material_id=1, vocab_version="v1", source=targetbank.AUTO,
        in_use=False, created_at="2026-10-27T10:00:00",
        target_map=targetmap.TargetMap(map_version="v1", vocab=VOCAB,
                                       concepts=(), propositions=()))
    with pytest.raises(bank_store.BankError, match="指纹"):
        bank_store.register(db, bad)


def test_版本列表按入库先后且跨教材互不冲突():
    db = conn()
    bank_store.register(db, entry("v1"))
    bank_store.register(db, entry("v2", created_at="2026-10-27T11:00:00"))
    bank_store.register(db, entry("v1", material_id=2))
    assert bank_store.versions(db, 1) == ("v1", "v2")
    assert bank_store.versions(db, 2) == ("v1",)


def test_最新版按入库时间取():
    db = conn()
    bank_store.register(db, entry("v2", created_at="2026-10-27T11:00:00"))
    bank_store.register(db, entry("v1"))
    assert bank_store.latest(db, 1, "v1").target_map.map_version == "v2"


def test_标记投用后可读回且缺版本报错():
    db = conn()
    bank_store.register(db, entry())
    bank_store.mark_in_use(db, 1, "v1")
    assert bank_store.by_fingerprint(db, 1, "fp-v1").in_use is True
    with pytest.raises(bank_store.BankError, match="版本不存在"):
        bank_store.mark_in_use(db, 1, "v9")


def test_改投另一批时旧批取消投用():
    db = conn()
    bank_store.register(db, entry("v1"))
    bank_store.register(db, entry("v2", created_at="2026-10-27T11:00:00"))
    bank_store.mark_in_use(db, 1, "v1")
    bank_store.mark_in_use(db, 1, "v2")
    assert bank_store.by_fingerprint(db, 1, "fp-v1").in_use is False
    assert bank_store.by_fingerprint(db, 1, "fp-v2").in_use is True


def test_别的教材的在用标记互不牵连():
    db = conn()
    bank_store.register(db, entry("v1"))
    bank_store.register(db, entry("v1", material_id=2))
    bank_store.mark_in_use(db, 2, "v1")
    bank_store.mark_in_use(db, 1, "v1")
    assert bank_store.by_fingerprint(db, 2, "fp-v1").in_use is True
    assert bank_store.by_fingerprint(db, 1, "fp-v1").in_use is True


def test_换词表版本的图也能读回原词表():
    db = conn()
    vocab2 = triple.Vocab(vocab_id="心理学", vocab_version="v2",
                          connections=("包括",))
    bank_store.register(db, entry(vocab=vocab2))
    back = bank_store.latest(db, 1, "v2").target_map
    assert back.vocab.vocab_version == "v2"
    assert back.vocab.connections == ("包括",)


def test_next_version_从_v1_起并跳已占用():
    assert rules.next_version(()) == "v1"
    assert rules.next_version(("v1",)) == "v2"
    assert rules.next_version(("v1", "v3")) == "v4"
    assert rules.next_version(("初版",)) == "v1"


def test_同一内容二次冻结不新开版本():
    db = conn()
    result = triple.ExtractionResult(vocab=VOCAB, triples=(
        triple.TripleCandidate(head="记忆", connection="包括", tail="短时记忆",
                               confidence=1.0),))
    first = kit_service.freeze_to_bank(db, 1, result, "2026-10-27T10:00:00")
    second = kit_service.freeze_to_bank(db, 1, result, "2026-10-27T11:00:00")
    assert first[2].target_map.fingerprint == second[2].target_map.fingerprint
    assert bank_store.versions(db, 1) == (first[0].map_version,)


def test_冻结入库时沿用期望版本号_被占则往后排():
    db = conn()
    result = triple.ExtractionResult(vocab=VOCAB, triples=(
        triple.TripleCandidate(head="记忆", connection="包括", tail="短时记忆",
                               confidence=1.0),))
    kit_service.freeze_to_bank(db, 1, result, "2026-10-27T10:00:00", "v5")
    assert bank_store.versions(db, 1) == ("v5",)
    other = triple.ExtractionResult(vocab=VOCAB, triples=(
        triple.TripleCandidate(head="短时记忆", connection="属于", tail="记忆",
                               confidence=1.0),))
    kit_service.freeze_to_bank(db, 1, other, "2026-10-27T11:00:00", "v5")
    assert bank_store.versions(db, 1) == ("v5", "v6")
