from dataclasses import dataclass

from triple import Vocab


@dataclass(frozen=True)
class Concept:
    """kit 契约：目标图中的一个概念。"""

    concept_id: str  # 概念唯一标识，图内唯一；不可空
    label: str  # 概念字面，展示用；不可空


@dataclass(frozen=True)
class Proposition:
    """kit 契约：目标图中的一条命题，即一条带方向的连接。"""

    head_id: str  # 起端概念 id；不可空，须存在于所属 TargetMap.concepts
    connection: str  # 连接词；不可空，须属于所属 TargetMap.vocab.connections
    tail_id: str  # 末端概念 id；不可空，须存在于所属 TargetMap.concepts


@dataclass(frozen=True)
class TargetMap:
    """kit 契约：冻结的目标命题图。"""

    map_version: str  # 版本号，如 v1；不可空，v1 有学生用过即锁
    vocab: Vocab  # 连接词表；不可空
    concepts: tuple[Concept, ...]  # 概念集；不可空，元素唯一
    propositions: tuple[Proposition, ...]  # 命题集；可为空元组，元素唯一


@dataclass(frozen=True)
class Kit:
    """kit 契约：给学生重组的零件集，无连接。"""

    map_version: str  # 对应的目标图版本；不可空
    concepts: tuple[Concept, ...]  # 概念零件；与目标图概念集一致
    connections: tuple[str, ...]  # 连接词零件；与目标图词表一致
