"""抽崩检测：一次抽取看起来可不可信。只体检，不改结果、不拦流程。"""

from kbp.contracts.quality import QualityReport, Signal, Thresholds
from kbp.contracts.triple import ExtractionResult

S1_MAX = 0.30  # 孤立概念率上限
S2_MIN = 0.50  # 连接词覆盖率下限
S3_MAX = 0.60  # 概念集中度上限
S4_MAX_Z = 2.0  # 每千字命题数与基线的最大 |z|
MIN_PROPS = 10  # 命题少于此数时只记录信号、不提示：比例类指标在小样本上抖得没意义

LABELS = {"S1": "孤立概念率", "S2": "连接词覆盖率",
          "S3": "概念集中度", "S4": "基线偏离度"}
REASONS = {"S1": "孤立概念偏多", "S2": "连接词用得偏少",
           "S3": "命题过度集中在少数概念上", "S4": "命题数量明显偏离以往"}
MESSAGE = "本次组件抽取可能不可信，您可重新抽取（{reasons}）"
PER_KILO = 1000.0

# 代码默认值：仅作开发期占位，未经冻结图校准，不能算已校准。
DEFAULT_THRESHOLDS = Thresholds(s1_max=S1_MAX, s2_min=S2_MIN, s3_max=S3_MAX,
                                s4_max_z=S4_MAX_Z, min_props=MIN_PROPS)


def degrees(result: ExtractionResult) -> dict[str, int]:
    """每个概念出现在多少条命题里（同一条里 head、tail 各算一次）。"""
    out: dict[str, int] = {}
    for t in result.triples:
        for label in (t.head, t.tail):
            out[label] = out.get(label, 0) + 1
    return out


def isolated_rate(deg: dict[str, int]) -> float:
    """S1：只出现过一次的概念占比。"""
    if not deg:
        return 0.0
    once = sum(1 for n in deg.values() if n == 1)
    return once / len(deg)


def connection_coverage(result: ExtractionResult) -> float:
    """S2：用到的连接词种类占词表的比例。"""
    allowed = result.vocab.connections
    if not allowed:
        return 0.0
    used = {t.connection for t in result.triples}
    return len(used & set(allowed)) / len(allowed)


def concentration(deg: dict[str, int], n_props: int) -> float:
    """S3：最热概念占全部连接端点的比例。"""
    if not deg or n_props <= 0:
        return 0.0
    return max(deg.values()) / (2 * n_props)


def density(result: ExtractionResult, text: str) -> float:
    """每千字命题数。"""
    return len(result.triples) * PER_KILO / max(len(text), 1)


def baseline_z(value: float, baseline: tuple[float, float] | None) -> float | None:
    """S4：与历史基线的偏离。标准差非正或没有基线时不判。"""
    if baseline is None:
        return None
    mean, sd = baseline
    if sd <= 0:
        return None
    return abs(value - mean) / sd


def _baseline(thr: Thresholds | None) -> tuple[float, float] | None:
    if thr is None or thr.baseline_mean is None or thr.baseline_sd is None:
        return None
    return thr.baseline_mean, thr.baseline_sd


def _signal(name: str, value: float | None, threshold: float | None,
            triggered: bool) -> Signal:
    return Signal(name=name, label=LABELS[name], value=value,
                  threshold=threshold, triggered=triggered)


def _hotter_than_max(value: float, cap: float | None) -> bool:
    return cap is not None and value > cap


def _colder_than_min(value: float, floor: float | None) -> bool:
    return floor is not None and value < floor


def _signals(thr: Thresholds | None, s1: float, s2: float, s3: float,
             z: float | None) -> tuple[Signal, ...]:
    """未校准（thr 为 None）时全部不判，阈值留空。"""
    if thr is None:
        return (_signal("S1", s1, None, False), _signal("S2", s2, None, False),
                _signal("S3", s3, None, False), _signal("S4", z, None, False))
    return (
        _signal("S1", s1, thr.s1_max, _hotter_than_max(s1, thr.s1_max)),
        _signal("S2", s2, thr.s2_min, _colder_than_min(s2, thr.s2_min)),
        _signal("S3", s3, thr.s3_max, _hotter_than_max(s3, thr.s3_max)),
        _signal("S4", z, thr.s4_max_z,
                z is not None and _hotter_than_max(z, thr.s4_max_z)),
    )


def assess(result: ExtractionResult, text: str,
           thresholds: Thresholds | None = None) -> QualityReport:
    """按 S1–S4 体检；阈值只用于提示，不丢命题、不拦流程。

    阈值组为空或未校准时只带出原值，不置"可能不可信"；
    命题数不足 min_props 时信号照算照带出，同样不提示。
    """
    thr = thresholds if thresholds is not None and thresholds.calibrated else None
    deg = degrees(result)
    n_props = len(result.triples)
    s1 = isolated_rate(deg)
    s2 = connection_coverage(result)
    s3 = concentration(deg, n_props)
    z = baseline_z(density(result, text), _baseline(thr))
    signals = _signals(thr, s1, s2, s3, z)
    reasons = [REASONS[s.name] for s in signals if s.triggered]
    flagged = bool(reasons) and n_props >= (thr.min_props if thr else 0)
    return QualityReport(
        signals=signals, possibly_inaccurate=flagged,
        message=MESSAGE.format(reasons="、".join(reasons)) if flagged else "",
        calibrated=thr is not None,
        baseline_n=thr.baseline_n if thr else 0,
        baseline_source=thr.baseline_source if thr else "")
