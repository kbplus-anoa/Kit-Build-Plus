from dataclasses import dataclass
from typing import Sequence

PU = "PU"
PEOU = "PEOU"
BI = "BI"
ATT = "ATT"

CONSTRUCTS = (PU, PEOU, BI, ATT)
CONSTRUCT_LABELS = {
    PU: "感知有用性",
    PEOU: "感知易用性",
    BI: "使用意图",
    ATT: "态度",
}

LIKERT_MIN = 1
LIKERT_MAX = 6
MIN_ALPHA = 0.7


@dataclass(frozen=True)
class ScaleItem:
    """tam 契约：一道量表题。"""

    item_id: str  # 题号，如 PU1；全量表唯一；不可空
    construct: str  # 构念代码，取值见 CONSTRUCTS；不可空
    text: str  # 题干中文，逐字取自源问卷；不可空
    optional: bool = False  # 是否属可选构念（源问卷把态度标为可选）


@dataclass(frozen=True)
class AlphaReport:
    """tam 契约：一个构念的内部一致性。"""

    construct: str  # 构念代码，取值见 CONSTRUCTS；不可空
    k: int  # 该构念的题数；不可空
    n: int  # 参与计算的人数（该构念下作答完整者）；不可空
    alpha: float | None  # Cronbach α，保留 4 位；可空（算不出时为 None）
    threshold: float  # 判据；不可空
    passed: bool  # α 是否达到判据；α 为 None 时不算通过


ScoreRow = tuple[int, str, float]  # （被试编号, 题号, 得分 1–6）


def alpha_by_construct(rows: Sequence[ScoreRow], items: Sequence[ScaleItem],
                       threshold: float = MIN_ALPHA) -> tuple[AlphaReport, ...]:
    """纯函数契约：按构念算 Cronbach α，输出顺序同 CONSTRUCTS。

    只收该构念下作答完整的人（缺一题则整人剔除）；量外题号忽略；
    得分须在 LIKERT_MIN–LIKERT_MAX，范围校验由入口（api）做。
    实现属 quiz（`kbp/quiz/alpha.py`）。
    """
    ...
