"""抽崩阈值落库：没有行即未校准，写入须带基线来源与样本量。"""

import sqlite3

import pytest

import kbp.contracts.quality as quality
import kbp.extract.threshold_store as store


def tuned(**kw):
    fields = dict(s1_max=0.3, s2_min=0.5, s3_max=0.6, s4_max_z=2.0,
                  min_props=10, baseline_mean=4.0, baseline_sd=1.5,
                  baseline_source="开发期冻结图 12 张", baseline_n=12)
    fields.update(kw)
    return quality.Thresholds(**fields)


@pytest.fixture
def conn():
    got = sqlite3.connect(":memory:")
    store.ensure(got)
    yield got
    got.close()


def test_没写过时读回未校准(conn):
    assert store.load(conn) is None


def test_写入后整组读回(conn):
    store.save(conn, tuned())
    got = store.load(conn)
    assert got == tuned()
    assert got.calibrated is True


def test_再写一次整组覆盖(conn):
    store.save(conn, tuned())
    store.save(conn, tuned(s1_max=0.4, baseline_n=20))
    assert store.load(conn).s1_max == 0.4
    assert store.load(conn).baseline_n == 20


def test_写入阈值却不记来源时拒绝且不动旧行(conn):
    store.save(conn, tuned())
    with pytest.raises(store.ThresholdError):
        store.save(conn, tuned(baseline_source=""))
    assert store.load(conn).baseline_source == "开发期冻结图 12 张"


def test_样本量为零时拒绝(conn):
    with pytest.raises(store.ThresholdError):
        store.save(conn, tuned(baseline_n=0))


def test_样本量为负或下限非正时拒绝(conn):
    assert store.check(tuned(baseline_n=-1)) != ""
    assert store.check(tuned(min_props=0)) != ""


def test_标准差为负时拒绝(conn):
    assert store.check(tuned(baseline_sd=-0.1)) != ""


def test_四个阈值都空时允许存未校准行(conn):
    store.save(conn, quality.Thresholds(s1_max=None, s2_min=None,
                                        s3_max=None, s4_max_z=None))
    got = store.load(conn)
    assert got.calibrated is False
    assert got.s1_max is None


def test_建表可重复执行(conn):
    store.ensure(conn)
    store.ensure(conn)
    assert store.load(conn) is None
