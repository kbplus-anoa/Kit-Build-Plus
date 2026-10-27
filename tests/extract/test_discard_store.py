"""机器侧丢弃留档：按原文指纹分组追加，与人工裁定留档分开。"""

import sqlite3

import pytest

import kbp.contracts.extraction as extraction
import kbp.extract.discard_store as store
from tests.extract.helpers import make_vocab


def drop(head="记忆", connection="包含", tail="编码",
         reason="连接词不在词表"):
    return extraction.DiscardedCandidate(head=head, connection=connection,
                                         tail=tail, reason=reason)


@pytest.fixture
def conn():
    got = sqlite3.connect(":memory:")
    store.ensure(got)
    yield got
    got.close()


def test_写入后按原文指纹读回(conn):
    assert store.save(conn, "abc", make_vocab(), (drop(),), "t1") == 1
    assert store.by_text(conn, "abc") == (("记忆", "包含", "编码",
                                          "连接词不在词表"),)


def test_不同原文分开(conn):
    store.save(conn, "abc", make_vocab(), (drop(),), "t1")
    store.save(conn, "def", make_vocab(), (drop("编码", "包含", "记忆"),),
               "t1")
    assert len(store.by_text(conn, "abc")) == 1
    assert len(store.by_text(conn, "def")) == 1


def test_同一原文抽两次追加不覆盖(conn):
    store.save(conn, "abc", make_vocab(), (drop(),), "t1")
    store.save(conn, "abc", make_vocab(), (drop(),), "t2")
    assert len(store.by_text(conn, "abc")) == 2


def test_没有丢弃时不写也不报错(conn):
    assert store.save(conn, "abc", make_vocab(), (), "t1") == 0
    assert store.count(conn) == 0


def test_原文指纹为空时拒绝(conn):
    with pytest.raises(store.DiscardError):
        store.save(conn, "", make_vocab(), (drop(),), "t1")


def test_没写过的原文读回空(conn):
    assert store.by_text(conn, "nope") == ()
    assert store.by_text(conn, "") == ()


def test_建表可重复执行(conn):
    store.ensure(conn)
    assert store.count(conn) == 0
