"""抽崩检测：S1–S4 的原值、阈值、校准状态与提示文案。"""

import kbp.contracts.quality as quality_contract
import kbp.contracts.triple as triple
import kbp.extract.quality as quality

VOCAB = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("属于", "导致", "包含", "影响"))


def prop(head, conn, tail):
    return triple.TripleCandidate(head=head, connection=conn, tail=tail,
                                  confidence=1.0, evidence=head + conn + tail)


def result(*triples):
    return triple.ExtractionResult(vocab=VOCAB, triples=tuple(triples))


def tuned(**kw):
    """已校准的阈值组：四阈值齐备并记下来源与样本量。"""
    fields = dict(s1_max=quality.S1_MAX, s2_min=quality.S2_MIN,
                  s3_max=quality.S3_MAX, s4_max_z=quality.S4_MAX_Z,
                  min_props=quality.MIN_PROPS,
                  baseline_source="开发期冻结图", baseline_n=12)
    fields.update(kw)
    return quality_contract.Thresholds(**fields)


def signals(report):
    return {s.name: s for s in report.signals}


def test_度数是每条命题两端各加一次():
    deg = quality.degrees(result(prop("甲", "属于", "乙"),
                                 prop("乙", "导致", "丙")))
    assert deg == {"甲": 1, "乙": 2, "丙": 1}


def test_孤立概念率按只出现一次的占比():
    deg = {"甲": 1, "乙": 2, "丙": 1}
    assert quality.isolated_rate(deg) == 2 / 3
    assert quality.isolated_rate({}) == 0.0


def test_连接词覆盖率按用到的种类算():
    got = quality.connection_coverage(result(prop("甲", "属于", "乙")))
    assert got == 0.25


def test_空词表时覆盖率为零不炸():
    empty = triple.ExtractionResult(
        vocab=triple.Vocab("x", "v1", ()), triples=())
    assert quality.connection_coverage(empty) == 0.0


def test_概念集中度按最热概念占端点比例():
    got = quality.concentration({"甲": 3, "乙": 1}, n_props=2)
    assert got == 0.75
    assert quality.concentration({}, 0) == 0.0


def test_每千字命题数():
    got = quality.density(result(prop("甲", "属于", "乙")), "字" * 500)
    assert got == 2.0


def test_未给阈值时只带原值不判也不提示():
    report = quality.assess(result(prop("甲", "属于", "乙")), "字" * 100)
    assert report.calibrated is False
    assert all(s.threshold is None and s.triggered is False
               for s in report.signals)
    assert report.possibly_inaccurate is False
    assert report.message == ""
    assert (report.baseline_n, report.baseline_source) == (0, "")


def test_阈值不全时仍算未校准():
    partial = quality_contract.Thresholds(s1_max=0.30, baseline_source="x",
                                          baseline_n=3)
    report = quality.assess(result(prop("甲", "属于", "乙")), "字" * 100,
                            partial)
    assert report.calibrated is False
    assert signals(report)["S1"].threshold is None


def test_缺基线来源或样本量时不算校准():
    blank = tuned(baseline_source="  ")
    missing = tuned(baseline_n=0)
    assert blank.calibrated is False
    assert missing.calibrated is False
    assert tuned().calibrated is True


def test_没有基线时_s4_不判():
    report = quality.assess(result(prop("甲", "属于", "乙")), "字" * 100,
                            tuned())
    assert signals(report)["S4"].value is None
    assert signals(report)["S4"].triggered is False


def test_偏离基线超过两倍标准差时触发():
    many = result(*[prop("甲%d" % i, "属于", "乙") for i in range(20)])
    report = quality.assess(many, "字" * 1000,
                            tuned(baseline_mean=2.0, baseline_sd=0.5))
    assert signals(report)["S4"].value == 36.0
    assert signals(report)["S4"].triggered is True


def test_标准差为零时不判():
    assert quality.baseline_z(5.0, (5.0, 0.0)) is None


def test_校准后阈值与信号一起带出():
    report = quality.assess(result(prop("甲", "属于", "乙")), "字" * 100,
                            tuned())
    assert report.calibrated is True
    assert report.baseline_n == 12
    assert report.baseline_source == "开发期冻结图"
    assert signals(report)["S1"].threshold == quality.S1_MAX
    assert signals(report)["S2"].threshold == quality.S2_MIN
    assert signals(report)["S3"].threshold == quality.S3_MAX
    assert signals(report)["S4"].threshold == quality.S4_MAX_Z


def test_命题太少的样本只记录不提示():
    small = result(*[prop("甲%d" % i, "属于", "乙") for i in range(3)])
    report = quality.assess(small, "字" * 50, tuned())
    assert signals(report)["S1"].triggered is True
    assert report.possibly_inaccurate is False
    assert report.message == ""


def test_命题够多且孤立概念多时提示并给出原因():
    one_conn = triple.Vocab("心理学", "v1", ("属于",))
    many = triple.ExtractionResult(one_conn, tuple(
        prop("甲%d" % i, "属于", "乙%d" % i) for i in range(12)))
    report = quality.assess(many, "字" * 200, tuned())
    assert report.possibly_inaccurate is True
    assert report.message == quality.MESSAGE.format(reasons="孤立概念偏多")


def test_多个信号同时触发时原因用顿号连接():
    many = result(*[prop("甲", "属于", "乙%d" % i) for i in range(12)])
    report = quality.assess(many, "字" * 200, tuned())
    assert "、" in report.message
    assert "孤立概念偏多" in report.message
    assert "连接词用得偏少" in report.message


def test_健康结果不提示():
    triples = []
    for i in range(6):
        triples.append(prop("甲%d" % i, "属于", "甲%d" % (i + 1)))
        triples.append(prop("甲%d" % (i + 1), "导致", "甲%d" % i))
    report = quality.assess(result(*triples), "字" * 400, tuned())
    assert report.possibly_inaccurate is False


def test_体检不改动抽取结果():
    got = result(prop("甲", "属于", "乙"))
    before = got
    quality.assess(got, "字" * 10, tuned())
    assert got is before and got.triples[0].head == "甲"
