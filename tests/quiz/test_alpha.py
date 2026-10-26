"""α 计算：公式对照、样本方差口径、缺答剔除与判据。

参考值用 R 的 `psych::alpha(check.keys=FALSE)` 对照，raw_alpha 与实现逐位相同。
"""

from kbp.contracts.tam import ATT, BI, PEOU, PU, ScaleItem
from kbp.quiz import alpha as A
from kbp.quiz.scale import TAM_ITEMS

M1 = [(3, 4, 5, 3), (4, 4, 4, 4), (2, 3, 4, 2), (5, 5, 4, 5),
      (3, 4, 4, 3), (4, 3, 5, 4), (2, 4, 3, 2)]
M2 = [(1, 2, 3, 1, 1), (2, 2, 2, 2, 3), (3, 3, 2, 3, 3),
      (1, 1, 2, 1, 2), (2, 3, 3, 2, 2), (3, 2, 2, 3, 3)]


def rows_of(matrix, ids, first=1):
    return [(first + r, iid, float(v)) for r, row in enumerate(matrix)
            for iid, v in zip(ids, row)]


def report_of(reports, construct):
    return next(r for r in reports if r.construct == construct)


def test_与_R_对照_矩阵一():
    ids = ("PU1", "PU2", "PU3", "PU4")
    a = A.cronbach_alpha([list(r) for r in M1])
    assert a == 0.7816
    assert report_of(A.alpha_by_construct(rows_of(M1, ids)), PU).alpha == 0.7816


def test_与_R_对照_矩阵二():
    items = tuple(ScaleItem("X%d" % i, PU, "题") for i in range(1, 6))
    ids = tuple(i.item_id for i in items)
    got = A.alpha_by_construct(rows_of(M2, ids), items=items)
    assert report_of(got, PU).alpha == 0.7511


def test_样本方差口径():
    assert A.variance([1.0, 2.0, 3.0]) == 1.0
    assert A.variance([5.0]) == 0.0
    assert A.variance([]) == 0.0


def test_条目完全一致时α为一():
    ids = tuple(i.item_id for i in TAM_ITEMS if i.construct == BI)
    rows = [(p, iid, float(p % 3 + 1)) for p in range(1, 5) for iid in ids]
    assert report_of(A.alpha_by_construct(rows), BI).alpha == 1.0


def test_单题构念算不出():
    items = (ScaleItem("X1", PU, "题"),)
    got = A.alpha_by_construct([(1, "X1", 3.0), (2, "X1", 5.0)], items=items)
    r = report_of(got, PU)
    assert (r.k, r.n, r.alpha, r.passed) == (1, 2, None, False)


def test_只有一人算不出():
    ids = ("PU1", "PU2", "PU3", "PU4")
    r = report_of(A.alpha_by_construct(rows_of([M1[0]], ids)), PU)
    assert (r.n, r.alpha) == (1, None)


def test_全常数算不出():
    ids = ("PU1", "PU2", "PU3", "PU4")
    rows = [(p, iid, 6.0) for p in range(1, 5) for iid in ids]
    r = report_of(A.alpha_by_construct(rows), PU)
    assert (r.n, r.alpha) == (4, None)


def test_缺答整人剔除():
    ids = ("PU1", "PU2", "PU3", "PU4")
    full = rows_of(M1, ids)
    cut = full[:-1]  # 第 7 人少最后一题
    r = report_of(A.alpha_by_construct(cut), PU)
    assert r.n == 6
    assert r.alpha == A.cronbach_alpha([list(x) for x in M1[:-1]])
    assert r.alpha != A.cronbach_alpha([list(x) for x in M1])


def test_量外题号与别的构念不影响():
    ids = ("PU1", "PU2", "PU3", "PU4")
    rows = rows_of(M1, ids) + [(1, "ZZ9", 2.0), (1, "BI1", 3.0)]
    assert report_of(A.alpha_by_construct(rows), PU).alpha == 0.7816


def test_同人同题取最后一次():
    ids = ("PU1", "PU2", "PU3", "PU4")
    rows = rows_of(M1, ids) + [(1, "PU1", 6.0)]
    assert report_of(A.alpha_by_construct(rows), PU).alpha != 0.7816
    assert report_of(A.alpha_by_construct(rows), PU).n == 7


def test_按构念分别报且顺序同枚举():
    got = A.alpha_by_construct([])
    assert [r.construct for r in got] == [PU, PEOU, BI, ATT]
    assert [r.k for r in got] == [4, 4, 3, 3]
    assert all(r.n == 0 and r.alpha is None and not r.passed for r in got)


def test_达到判据才算通过():
    ids = ("PU1", "PU2", "PU3", "PU4")
    rows = rows_of(M1, ids)
    low = report_of(A.alpha_by_construct(rows, threshold=0.7), PU)
    high = report_of(A.alpha_by_construct(rows, threshold=0.9), PU)
    assert low.passed is True and low.threshold == 0.7
    assert high.passed is False and high.threshold == 0.9


def test_矩阵行列不齐算不出():
    assert A.cronbach_alpha([[1.0, 2.0], [3.0]]) is None
    assert A.cronbach_alpha([]) is None
