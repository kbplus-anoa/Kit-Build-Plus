"""人工裁定路的入库：首次用到时把冻结图登记进题库，与自动路同一张表。"""

import kbp.contracts.adjudication as adjudication
import kbp.contracts.targetbank as targetbank
import kbp.contracts.triple as triple
import kbp.kit.bank_store as bank_store
import kbp.kit.kit_service as kit_service
import kbp.kit.store as store


def log(items):
    v = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("包括",))
    return adjudication.AdjudicationLog(batch_id="b1", vocab=v,
                                        items=tuple(items))


def acc(head, conn, tail):
    cand = triple.TripleCandidate(head=head, connection=conn, tail=tail,
                                  confidence=0.9)
    return adjudication.Adjudication(candidate=cand,
                                     decision=adjudication.ACCEPTED, reason="")


def seeded():
    conn = store.connect(":memory:")
    bank_store.ensure(conn)
    kit_service.adjudicate(conn, log([acc("记忆", "包括", "短时记忆")]))
    return conn


def test_人工裁定图首次用到即入库():
    conn = seeded()
    target, kit = kit_service.freeze_and_bank(conn, 7, "b1", "v1")
    entry = bank_store.by_version(conn, 7, "v1")
    assert entry is not None
    assert entry.source == targetbank.ADJUDICATED
    assert entry.batch_id == "b1"
    assert entry.target_map.fingerprint == target.fingerprint
    assert [c.label for c in kit.concepts] == ["记忆", "短时记忆"]
    conn.close()


def test_同一张图不重复入库():
    conn = seeded()
    kit_service.freeze_and_bank(conn, 7, "b1", "v1")
    again, _ = kit_service.freeze_and_bank(conn, 7, "b1", "v2")
    assert again.map_version == "v1"
    assert len(kit_service.history(conn, 7)) == 1
    conn.close()


def test_登记项带词表版本且未投用():
    conn = seeded()
    target, _ = kit_service.freeze_and_bank(conn, 7, "b1", "v1")
    entry = bank_store.by_version(conn, 7, "v1")
    assert entry.vocab_version == target.vocab.vocab_version
    assert entry.in_use is False
    conn.close()
