"""Cronbach α：按构念算量表内部一致性。

公式与 STAT_PLAN.md 一致：α = k/(k-1) × (1 − Σσ²ᵢ/σ²总)，
方差取样本方差（分母 n-1），与 SPSS、R 的 `var()` 同口径。
"""

from collections.abc import Sequence

from kbp.contracts.tam import (CONSTRUCTS, MIN_ALPHA, AlphaReport, ScaleItem,
                               ScoreRow)
from kbp.quiz.scale import TAM_ITEMS

MIN_ROWS = 2


def variance(values: Sequence[float]) -> float:
    """样本方差（分母 n-1）；少于两人时返回 0.0。"""
    n = len(values)
    if n < MIN_ROWS:
        return 0.0
    mean = sum(values) / n
    return sum((v - mean) ** 2 for v in values) / (n - 1)


def cronbach_alpha(matrix: Sequence[Sequence[float]]) -> float | None:
    """按公式算 α（保留 4 位）；题数少于 2、人数少于 2 或总变异为 0 时算不出。"""
    k = len(matrix[0]) if matrix else 0
    if len(matrix) < MIN_ROWS or k < MIN_ROWS or any(len(r) != k for r in matrix):
        return None
    total = variance([sum(r) for r in matrix])
    if total <= 0:
        return None
    items = sum(variance([r[j] for r in matrix]) for j in range(k))
    return round((k / (k - 1)) * (1 - items / total), 4)


def _complete(rows: Sequence[ScoreRow], ids: tuple[str, ...]) -> list[list[float]]:
    """该构念下作答完整者的得分矩阵：缺一题整人剔除，同人同题取最后一次。"""
    seen: dict[int, dict[str, float]] = {}
    for participant, item_id, score in rows:
        if item_id in ids:
            seen.setdefault(participant, {})[item_id] = float(score)
    return [[got[i] for i in ids] for got in seen.values()
            if all(i in got for i in ids)]


def alpha_by_construct(rows: Sequence[ScoreRow], items: Sequence[ScaleItem] = TAM_ITEMS,
                       threshold: float = MIN_ALPHA) -> tuple[AlphaReport, ...]:
    """按构念算 α，输出顺序同 CONSTRUCTS；量外题号忽略。"""
    reports = []
    for construct in CONSTRUCTS:
        ids = tuple(i.item_id for i in items if i.construct == construct)
        matrix = _complete(rows, ids) if ids else []
        alpha = cronbach_alpha(matrix) if matrix else None
        reports.append(AlphaReport(construct=construct, k=len(ids), n=len(matrix),
                                   alpha=alpha, threshold=threshold,
                                   passed=alpha is not None and alpha >= threshold))
    return tuple(reports)
