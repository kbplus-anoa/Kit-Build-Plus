"""连接依赖：文件库每线程一条连接，内存库全程共一条。

其他路由用例都 `deps.reset_conn(conn)` 注入单连接，正好绕过这条分配逻辑，
所以这里显式把注入撤掉再验。
"""

import threading

import kbp.api.deps as deps


def collect(n, fn):
    out = []

    def work():
        out.append(fn())

    threads = [threading.Thread(target=work) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out


def test_文件库每线程各一条连接并见到同一份表(tmp_path, monkeypatch):
    monkeypatch.setenv("KBP_DB_PATH", str(tmp_path / "kb.sqlite3"))
    deps.reset_conn(None)
    try:
        got = collect(4, lambda: (id(deps.get_conn()),
                                  deps.get_conn().execute(
                                      "SELECT count(*) FROM quiz_set"
                                  ).fetchone()[0]))
    finally:
        deps.reset_conn(None)
    assert [n for _, n in got] == [0, 0, 0, 0]
    assert len({cid for cid, _ in got}) == 4


def test_内存库每线程各一条连接仍共用一张表(monkeypatch):
    monkeypatch.setenv("KBP_DB_PATH", ":memory:")
    deps.reset_conn(None)
    try:
        deps.get_conn().execute(
            "INSERT INTO quiz_set (quiz_id, questions) VALUES ('z1', '[]')")
        deps.get_conn().commit()
        got = collect(3, lambda: (id(deps.get_conn()),
                                  deps.get_conn().execute(
                                      "SELECT count(*) FROM quiz_set"
                                  ).fetchone()[0]))
    finally:
        deps.reset_conn(None)
    assert [n for _, n in got] == [1, 1, 1]
    assert len({cid for cid, _ in got}) == 3


def test_重置后内存库是新的空库(monkeypatch):
    monkeypatch.setenv("KBP_DB_PATH", ":memory:")
    deps.reset_conn(None)
    try:
        deps.get_conn().execute(
            "INSERT INTO quiz_set (quiz_id, questions) VALUES ('z1', '[]')")
        deps.get_conn().commit()
        deps.reset_conn(None)
        left = deps.get_conn().execute(
            "SELECT count(*) FROM quiz_set").fetchone()[0]
    finally:
        deps.reset_conn(None)
    assert left == 0
