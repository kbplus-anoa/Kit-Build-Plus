import hashlib

import kbp.contracts.targetmap

FINGERPRINT_LEN = 16
SEP_FIELD = "\u0001"
SEP_EDGE = "\u0002"
SEP_GROUP = "\u0003"


def label_index(concepts: tuple[kbp.contracts.targetmap.Concept, ...]
                ) -> dict[str, str]:
    """概念 id → 字面。指纹只认字面，不认编号。"""
    return {c.concept_id: c.label for c in concepts}


def label_to_id(concepts: tuple[kbp.contracts.targetmap.Concept, ...]
                ) -> dict[str, str]:
    """字面 → 首次出现的 id；两条路共用同一套编号规则。"""
    index: dict[str, str] = {}
    for concept in concepts:
        index.setdefault(concept.label, concept.concept_id)
    return index


def ordered_propositions(edges: list[tuple[str, str, str]]) -> list[tuple]:
    """去自环、去重，保持首次出现顺序。两条路共用。"""
    seen: set[tuple[str, str, str]] = set()
    out: list[tuple[str, str, str]] = []
    for head, connection, tail in edges:
        key = (head, connection, tail)
        if head == tail or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def next_version(versions: tuple[str, ...]) -> str:
    """分配新版本号：已占用的 vN 里取最大 N 加一，空库从 v1 起。

    v 号只区分"第几版"，不区分内容；同一张图靠指纹认，不靠版本号。
    """
    numbers = [int(v[1:]) for v in versions if v.startswith("v") and v[1:].isdigit()]
    return "v" + str(max(numbers) + 1 if numbers else 1)


def fingerprint(target: kbp.contracts.targetmap.TargetMap) -> str:
    """按内容算指纹：与编号、输入顺序无关，只认结构。

    同一教材在两台机器上抽出的概念与命题只要一致，指纹就一致；
    概念或命题差一条，指纹立刻不同——这正是 v 号区分不了的东西。
    """
    return content_fingerprint(target.concepts, target.propositions)


def content_fingerprint(concepts, propositions) -> str:
    index = label_index(concepts)
    labels = sorted(set(index.values()))
    edges = sorted((index.get(p.head_id, p.head_id), p.connection,
                    index.get(p.tail_id, p.tail_id)) for p in propositions)
    payload = SEP_FIELD.join(labels) + SEP_GROUP + SEP_EDGE.join(
        SEP_FIELD.join(edge) for edge in edges)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:FINGERPRINT_LEN]
