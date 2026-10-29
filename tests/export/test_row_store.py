"""快照读写：导出只查库，写入侧覆盖同键旧值。"""


import pytest


import kbp.contracts.exportcsv as exportcsv
import kbp.export.row_store as row_store


@pytest.fixture
def conn():
    import sqlite3
    c = sqlite3.connect(":memory:")
    row_store.ensure(c)
    yield c
    c.close()


def subject(**kw):
    base = dict(participant_id=1, material_id=1, time_point="post",
                submit_seq=1, target_map_version="v1", fingerprint="fp1",
                mode="test", condition="exp", is_practice=0,
                correct_propositions=2, total_propositions=3,
                n_lacking=1, n_excessive=0, n_leaving=0, n_reversed=0,
                possibly_inaccurate=0, map_size=2, map_node_count=3,
                signal_isolated=0.1, signal_coverage=0.8,
                signal_concentration=0.5, signal_baseline=1.2)
    base.update(kw)
    return exportcsv.SubjectRow(**base)


def test_被试级快照往返保住每条字段(conn):
    row = subject()
    row_store.save_subject(conn, row)
    assert row_store.subjects(conn) == (row,)


def test_同一四元键覆盖旧值(conn):
    row_store.save_subject(conn, subject(condition="exp"))
    row_store.save_subject(conn, subject(condition="con", submit_seq=1))
    rows = row_store.subjects(conn)
    assert len(rows) == 1 and rows[0].condition == "con"


def test_空条件查出全部(conn):
    for pid in (1, 2, 3):
        row_store.save_subject(conn, subject(participant_id=pid))
    assert len(row_store.subjects(conn)) == 3


def test_按被试单选与多选(conn):
    for pid in (1, 2, 3):
        row_store.save_subject(conn, subject(participant_id=pid))
    assert [r.participant_id for r in row_store.subjects(conn, (2,))] == [2]
    assert [r.participant_id for r in row_store.subjects(conn, (1, 3))] == [1, 3]


def test_教材与时点可叠加筛选(conn):
    row_store.save_subject(conn, subject(material_id=1, time_point="pre"))
    row_store.save_subject(conn, subject(material_id=1, time_point="post"))
    row_store.save_subject(conn, subject(material_id=2, time_point="post"))
    rows = row_store.subjects(conn, (), (1,), ("post",))
    assert len(rows) == 1 and rows[0].time_point == "post"


def test_没有记录返回空(conn):
    assert row_store.subjects(conn) == ()


def test_条数只数被试级(conn):
    assert row_store.count_subjects(conn) == 0
    row_store.save_subject(conn, subject())
    assert row_store.count_subjects(conn) == 1
