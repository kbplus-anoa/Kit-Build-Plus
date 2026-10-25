import pytest

import adjudication
import store
import triple


def cand(head, conn, tail, conf=0.9):
    return triple.TripleCandidate(head=head, connection=conn,
                                  tail=tail, confidence=conf)


def make_log(batch="b1", decision=adjudication.ACCEPTED):
    v = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("属于", "导致", "包括"))
    items = (adjudication.Adjudication(candidate=cand("记忆", "包括", "短时记忆"),
                                       decision=decision, reason=""),
             adjudication.Adjudication(candidate=cand("长度", "包括", "容量"),
                                       decision=adjudication.REJECTED,
                                       reason="教材未提及"))
    return adjudication.AdjudicationLog(batch_id=batch, vocab=v, items=items)


@pytest.fixture
def conn():
    c = store.connect(":memory:")
    yield c
    c.close()


def test_写入并读回条数一致(conn):
    assert store.save(conn, make_log()) == 2
    assert len(store.load(conn, "b1").items) == 2


def test_读回保留裁定与理由(conn):
    store.save(conn, make_log())
    log = store.load(conn, "b1")
    assert log.items[0].decision == adjudication.ACCEPTED
    assert log.items[1].reason == "教材未提及"


def test_读回保留完整词表(conn):
    store.save(conn, make_log())
    assert store.load(conn, "b1").vocab.connections == ("属于", "导致", "包括")


def test_读回保持写入顺序(conn):
    store.save(conn, make_log())
    log = store.load(conn, "b1")
    assert log.items[0].candidate.head == "记忆"


def test_同一批次不可覆盖(conn):
    store.save(conn, make_log())
    with pytest.raises(store.StoreError):
        store.save(conn, make_log())


def test_词表被改写时拒绝(conn):
    store.save(conn, make_log())
    v2 = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                      connections=("属于",))
    bad = adjudication.AdjudicationLog(batch_id="b2", vocab=v2,
                                       items=())
    with pytest.raises(store.StoreError):
        store.save(conn, bad)


def test_不存在的批次报错(conn):
    with pytest.raises(store.StoreError):
        store.load(conn, "nope")


def test_列出已存批次按写入顺序(conn):
    store.save(conn, make_log("b1"))
    store.save(conn, make_log("b2"))
    assert store.batches(conn) == ("b1", "b2")


def test_落盘后重开仍可读回(tmp_path):
    path = str(tmp_path / "sub" / "kb.sqlite3")
    c1 = store.connect(path)
    store.save(c1, make_log())
    c1.close()
    c2 = store.connect(path)
    assert len(store.load(c2, "b1").items) == 2
    c2.close()
