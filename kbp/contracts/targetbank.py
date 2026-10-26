from dataclasses import dataclass
from typing import Protocol

from kbp.contracts.targetmap import TargetMap

ADJUDICATED = "adjudicated"
AUTO = "auto"

SOURCES = (ADJUDICATED, AUTO)

MAX_CREATED = 40


@dataclass(frozen=True)
class BankEntry:
    """kit 契约：一份已冻结目标图在库里的登记项。"""

    material_id: int  # 教材顺序编号；不可空，>=1
    vocab_version: str  # 连接词表版本，同一教材换词表就得另出一张图；不可空
    source: str  # 来源枚举，取值见 SOURCES；不可空
    in_use: bool  # 是否已投用，投用后拒改也不重抽；不可空
    created_at: str  # 入库时间，ISO 8601；不可空
    target_map: TargetMap  # 冻结后的目标图，自带版本号与内容指纹；不可空


def check_entry(entry: BankEntry) -> str:
    """纯函数契约：登记项是否合法；返回空串表示合法，否则返回中文原因。"""
    if not isinstance(entry.material_id, int) or entry.material_id < 1:
        return "material_id 须为正整数"
    if not entry.vocab_version:
        return "词表版本不得为空"
    if entry.source not in SOURCES:
        return "未知来源: " + str(entry.source)
    if not entry.created_at:
        return "入库时间不得为空"
    if not entry.target_map.map_version:
        return "版本号不得为空"
    if not entry.target_map.fingerprint:
        return "冻结图必须带内容指纹"
    return ""


def same_map(entry: BankEntry, fingerprint: str) -> bool:
    """纯函数契约：该登记项是否就是这张指纹对应的图。"""
    return bool(fingerprint) and entry.target_map.fingerprint == fingerprint


class TargetMapBank(Protocol):
    """行为契约：已冻结目标图的库。

    按教材与词表版本登记，按内容指纹查；同一教材可有多个版本并存，
    但版本号在同一教材内不复用（D02：自动抽不覆盖已投用的旧版本）。
    """

    def register(self, entry: BankEntry) -> None:
        """登记一份新冻结的图；版本号或指纹重复须拒绝。"""
        ...

    def by_fingerprint(self, material_id: int,
                       fingerprint: str) -> BankEntry | None:
        """按内容指纹查同一张图；查不到返回 None。"""
        ...

    def latest(self, material_id: int, vocab_version: str) -> BankEntry | None:
        """该教材该词表版本下最新入库的一张图；没有返回 None。"""
        ...

    def version_exists(self, material_id: int, map_version: str) -> bool:
        """该教材是否已占用这个版本号，用于分配新版本时避开旧号。"""
        ...

    def mark_in_use(self, material_id: int, map_version: str) -> None:
        """标记为已投用；此后该版本拒改、也不再被重抽覆盖。"""
        ...
