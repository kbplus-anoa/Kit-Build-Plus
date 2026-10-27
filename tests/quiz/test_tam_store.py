"""量表作答存储：一人一题一行，重答覆盖，读回形状与契约 ScoreRow 一致。"""

import sqlite3

import pytest

import kbp.quiz.tam_store as store
from kbp.quiz.scale import TAM_ITEMS


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    store.ensure(c)
    yield c
    c.close()


def ids():
    return [i.item_id for i in TAM_ITEMS]


def test_写入一题再读回(conn):
    store.save(conn, 1, "PU1", 4, "2026-10-27T10:00:00+00:00")
    assert store.rows(conn) == ((1, "PU1", 4.0),)
    assert store.count(conn) == 1


def test_整卷写入返回条数(conn):
    saved = store.save_all(conn, 2, [("PU1", 3), ("PU2", 5)], "t")
    assert saved == 2
    assert store.count(conn) == 2


def test_同人同题覆盖不追加行(conn):
    store.save(conn, 1, "PU1", 3, "t1")
    store.save(conn, 1, "PU1", 6, "t2")
    assert store.rows(conn) == ((1, "PU1", 6.0),)
    assert store.count(conn) == 1


def test_不同人同题各留一行(conn):
    store.save_all(conn, 1, [("PU1", 3)], "t")
    store.save_all(conn, 2, [("PU1", 5)], "t")
    assert store.rows(conn) == ((1, "PU1", 3.0), (2, "PU1", 5.0))


def test_读回按被试与题号排序(conn):
    store.save(conn, 2, "PU4", 2, "t")
    store.save(conn, 1, "PU2", 4, "t")
    store.save(conn, 2, "PU1", 5, "t")
    store.save(conn, 1, "PU1", 3, "t")
    assert store.rows(conn) == ((1, "PU1", 3.0), (1, "PU2", 4.0),
                                (2, "PU1", 5.0), (2, "PU4", 2.0))


def test_空库读回空与零条(conn):
    assert store.rows(conn) == ()
    assert store.count(conn) == 0


def test_建表可重复调用(conn):
    store.ensure(conn)
    store.save(conn, 1, "PU1", 4, "t")
    store.ensure(conn)
    assert store.count(conn) == 1


def test_得分按浮点存回(conn):
    store.save(conn, 1, "PU1", 3, "t")
    value = conn.execute("SELECT score FROM tam_answer").fetchone()[0]
    assert isinstance(value, float) and store.rows(conn)[0][2] == 3.0


def test_读回形状能直接喂α实现(conn):
    import kbp.quiz.alpha
    for p in range(1, 8):
        store.save_all(conn, p, [(i, 3 + (p % 3)) for i in ids()[:4]], "t")
    reports = kbp.quiz.alpha.alpha_by_construct(store.rows(conn))
    pu = next(r for r in reports if r.construct == "PU")
    assert pu.n == 7
