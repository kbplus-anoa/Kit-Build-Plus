from dataclasses import dataclass

from targetmap import TargetMap
from triple import TripleCandidate, Vocab

ACCEPTED = "accepted"
REJECTED = "rejected"

DECISIONS = (ACCEPTED, REJECTED)

MAX_REASON = 500


@dataclass(frozen=True)
class Adjudication:
    """kit 契约：人对一条候选三元组的裁定，驳回项留档作标注。"""

    candidate: TripleCandidate  # 被裁定的候选三元组；不可空
    decision: str  # 裁定枚举，取值见 DECISIONS；不可空
    reason: str  # 驳回理由，可空（空串表示未填），长度 <= MAX_REASON


@dataclass(frozen=True)
class AdjudicationLog:
    """kit 契约：一次抽取批次的完整裁定记录，驳回项与接受项并存。"""

    batch_id: str  # 抽取批次标识，与 extract 的批次对应；不可空
    vocab: Vocab  # 本次裁定使用的词表；不可空
    items: tuple[Adjudication, ...]  # 裁定项，按候选原始顺序；可为空元组


def accepted(log: AdjudicationLog) -> tuple[Adjudication, ...]:
    """纯函数契约：取出被接受的裁定项，保持原顺序。"""
    ...


def rejected(log: AdjudicationLog) -> tuple[Adjudication, ...]:
    """纯函数契约：取出被驳回的裁定项，保持原顺序。"""
    ...


def freeze(log: AdjudicationLog, map_version: str) -> TargetMap:
    """纯函数契约：接受项凝固为目标图。

    概念按标签去重并按首次出现顺序编号；连接词须全部落在 log.vocab 内。
    """
    ...


def is_locked(map_version: str, used_by_students: bool) -> bool:
    """纯函数契约：该版本是否已锁死（有学生用过即不可改）。"""
    ...
