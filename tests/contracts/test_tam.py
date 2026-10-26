"""tam 契约：构念枚举、量表题字段、α 报告字段与判据默认值。"""

from kbp.contracts import tam


def test_构念枚举与中文标签():
    assert tam.CONSTRUCTS == (tam.PU, tam.PEOU, tam.BI, tam.ATT)
    assert tam.CONSTRUCT_LABELS[tam.PU] == "感知有用性"
    assert tam.CONSTRUCT_LABELS[tam.ATT] == "态度"


def test_六点上下限与判据():
    assert (tam.LIKERT_MIN, tam.LIKERT_MAX) == (1, 6)
    assert tam.MIN_ALPHA == 0.7


def test_量表题默认必答():
    assert tam.ScaleItem("PU1", tam.PU, "题干").optional is False


def test_量表题可标可选():
    item = tam.ScaleItem("ATT1", tam.ATT, "题干", optional=True)
    assert item.optional is True


def test_α报告字段():
    r = tam.AlphaReport(tam.PU, 4, 30, 0.81, tam.MIN_ALPHA, True)
    assert (r.construct, r.k, r.n, r.alpha, r.threshold, r.passed) == \
        (tam.PU, 4, 30, 0.81, 0.7, True)
    assert tam.AlphaReport(tam.BI, 3, 0, None, tam.MIN_ALPHA, False).alpha is None


def test_得分行是三元组():
    row: tam.ScoreRow = (1, "PU1", 5.0)
    assert row[0] == 1 and row[1] == "PU1" and row[2] == 5.0
