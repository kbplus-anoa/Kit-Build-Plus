"""教材登记：同一份字节只占一行，内容一变就新开。"""

import sqlite3

import pytest

import kbp.ingest.materials as materials


@pytest.fixture
def conn():
    db = sqlite3.connect(":memory:")
    materials.ensure(db)
    yield db
    db.close()


def add(conn, name="记忆.pdf", digest="a1", chars=120, at="2026-01-01T00:00:00"):
    return materials.add_or_get(conn, name, "pdf", "pdf", chars, digest, at)


def test_首次上传登记一行(conn):
    mid = add(conn)
    row = materials.get(conn, mid)
    assert row[1] == "记忆.pdf" and row[4] == 120


def test_同字节复用同一个教材号(conn):
    first = add(conn)
    again = add(conn, name="改过名.pdf", at="2026-01-02T00:00:00")
    assert again == first
    assert len(materials.list_all(conn)) == 1


def test_内容变了就新开一行(conn):
    first = add(conn)
    second = add(conn, digest="b2")
    assert second != first
    assert len(materials.list_all(conn)) == 2


def test_列表新在前且按上限截断(conn):
    add(conn, name="一.pdf", digest="d1")
    add(conn, name="二.pdf", digest="d2")
    add(conn, name="三.pdf", digest="d3")
    rows = materials.list_all(conn, limit=2)
    assert [r[1] for r in rows] == ["三.pdf", "二.pdf"]


def test_同字节后再上传会补上原文路径(conn):
    mid = add(conn)
    assert materials.get(conn, mid)[6] == ""
    again = materials.add_or_get(conn, "记忆.pdf", "pdf", "pdf", 120, "a1",
                                 "2026-01-02T00:00:00", path="/tmp/x.pdf")
    assert again == mid
    assert materials.get(conn, mid)[6] == "/tmp/x.pdf"


def test_查不到的教材号返回空(conn):
    assert materials.get(conn, 999) is None
