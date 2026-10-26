from dataclasses import dataclass

from kbp.contracts.triple import ExtractionResult


@dataclass(frozen=True)
class Signal:
    """quality 契约：一条抽崩信号，原值与判据成对带出。"""

    name: str  # 信号代号，如 S1；不可空
    label: str  # 中文短名，展示用；不可空
    value: float | None  # 实测值；可空（基线不足时无值，此时不判）
    threshold: float  # 触发阈值；不可空
    triggered: bool  # 是否触发；不可空


@dataclass(frozen=True)
class QualityReport:
    """quality 契约：一次抽取的可信度体检结果。"""

    signals: tuple[Signal, ...]  # 全部信号，无论是否触发；不可空
    possibly_inaccurate: bool  # 是否提示"可能不可信"；不可空
    message: str = ""  # 触发时的固定文案（含原因）；未触发为空串


def assess(result: ExtractionResult, text: str,
           baseline: tuple[float, float] | None = None) -> QualityReport:
    """纯函数契约：按 S1–S4 体检一次抽取。

    baseline 是（每千字命题数 的均值, 标准差），由调用方从历史留档给出；
    没有历史时传 None，S4 不判。实现属 extract（`kbp/extract/quality.py`）。
    """
    ...
