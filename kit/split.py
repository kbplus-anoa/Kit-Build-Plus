import targetmap


class SplitError(ValueError):
    """目标图无法拆成 kit。"""


def split(target: targetmap.TargetMap) -> targetmap.Kit:
    """去掉连接，只留零件：概念集 + 连接词集。这正是 Kit-Build 的定义。

    约束：每个零件都必须至少被一条目标命题用到，否则它就是空白干扰项。
    """
    if not target.concepts:
        raise SplitError("目标图没有概念，无法拆 kit")
    used_concepts = _concept_ids(target)
    connections = _used(target)
    if not connections:
        raise SplitError("目标图中没有任何连接词被用到")
    concepts = tuple(c for c in target.concepts if c.concept_id in used_concepts)
    return targetmap.Kit(map_version=target.map_version,
                         concepts=concepts,
                         connections=tuple(connections))


def _concept_ids(target: targetmap.TargetMap) -> set[str]:
    used: set[str] = set()
    for prop in target.propositions:
        used.add(prop.head_id)
        used.add(prop.tail_id)
    return used


def _used(target: targetmap.TargetMap) -> list[str]:
    order: dict[str, None] = {}
    for prop in target.propositions:
        order.setdefault(prop.connection, None)
    return list(order)


def kit_signature(kit: targetmap.Kit) -> tuple:
    """kit 的稳定指纹，用于判断两次拆出的零件集是否等价。"""
    return (kit.map_version,
            tuple((c.concept_id, c.label) for c in kit.concepts),
            tuple(sorted(kit.connections)))
