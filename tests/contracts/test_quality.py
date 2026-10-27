"""quality 契约：阈值组、信号与体检报告的形状。"""

import kbp.contracts.quality as quality
import kbp.contracts.triple as triple

VOCAB = triple.Vocab("心理学", "v1", ("属于",))


def test_阈值组默认未校准():
    blank = quality.Thresholds()
    assert blank.calibrated is False
    assert blank.min_props == 10
    assert (blank.baseline_n, blank.baseline_source) == (0, "")


def test_四阈值齐备且记下来源与样本量才算校准():
    tuned = quality.Thresholds(s1_max=0.3, s2_min=0.5, s3_max=0.6,
                               s4_max_z=2.0, baseline_source="冻结图",
                               baseline_n=8)
    assert tuned.calibrated is True
    assert quality.Thresholds(**{**tuned.__dict__, "baseline_n": 0}
                              ).calibrated is False


def test_体检报告默认未校准():
    report = quality.QualityReport(signals=(), possibly_inaccurate=False)
    assert report.calibrated is False
    assert report.message == ""
    assert (report.baseline_n, report.baseline_source) == (0, "")


def test_信号阈值可为空():
    signal = quality.Signal(name="S1", label="孤立概念率", value=0.4,
                            threshold=None, triggered=False)
    assert signal.threshold is None


def test_assess_契约签名稳定():
    import inspect
    params = list(inspect.signature(quality.assess).parameters)
    assert params == ["result", "text", "thresholds"]
