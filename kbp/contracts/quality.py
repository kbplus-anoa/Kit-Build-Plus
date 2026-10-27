from dataclasses import dataclass

from kbp.contracts.triple import ExtractionResult


@dataclass(frozen=True)
class Signal:
    """quality 契约：一条抽崩信号，原值与判据成对带出。"""

    name: str  # 信号代号，如 S1；不可空
    label: str  # 中文短名，展示用；不可空
    value: float | None  # 实测值；可空（判据不成立时无值，此时不判）
    threshold: float | None  # 触发阈值；可空（未校准时为空）
    triggered: bool  # 是否触发；不可空


@dataclass(frozen=True)
class Thresholds:
    """quality 契约：抽崩阈值组，含基线来源与样本量（D08）。

    四阈值取开发期冻结图的经验分位点；冻结图出现前四个阈值留空，
    整组标为未校准，此时体检只记录原值、不提示。
    """

    s1_max: float | None = None  # 孤立概念率上限；可空（未校准）
    s2_min: float | None = None  # 连接词覆盖率下限；可空（未校准）
    s3_max: float | None = None  # 概念集中度上限；可空（未校准）
    s4_max_z: float | None = None  # 每千字命题数的最大 |z|；可空（未校准）
    min_props: int = 10  # 命题少于此数只记录不提示；单位：条；不可空
    baseline_mean: float | None = None  # 每千字命题数基线均值；可空
    baseline_sd: float | None = None  # 每千字命题数基线标准差；可空
    baseline_source: str = ""  # 基线来源（哪批冻结图）；可空
    baseline_n: int = 0  # 基线样本量（参与统计的冻结图数）；单位：张；不可空

    @property
    def calibrated(self) -> bool:
        """四阈值齐备且记下来源与样本量才算校准。"""
        set_all = None not in (self.s1_max, self.s2_min,
                               self.s3_max, self.s4_max_z)
        named = bool(self.baseline_source.strip())
        return set_all and self.baseline_n > 0 and named


@dataclass(frozen=True)
class QualityReport:
    """quality 契约：一次抽取的可信度体检结果。"""

    signals: tuple[Signal, ...]  # 全部信号，无论是否触发；不可空
    possibly_inaccurate: bool  # 是否提示"可能不可信"；不可空
    message: str = ""  # 触发时的固定文案（含原因）；未触发为空串
    calibrated: bool = False  # 本次判据是否已校准；未校准时不可空提示
    baseline_n: int = 0  # 本次基线样本量；单位：张；未校准时为 0
    baseline_source: str = ""  # 本次基线来源；未校准时为空串


def assess(result: ExtractionResult, text: str,
           thresholds: Thresholds | None = None) -> QualityReport:
    """纯函数契约：按 S1–S4 体检一次抽取。

    thresholds 为 None 或未校准时，每个信号的 threshold 为空、不判触发，
    也不给"可能不可信"提示；实现属 extract（`kbp/extract/quality.py`）。
    """
    ...
