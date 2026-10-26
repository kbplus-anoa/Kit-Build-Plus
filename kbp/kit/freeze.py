import kbp.contracts.adjudication
import kbp.contracts.targetmap


class FreezeError(ValueError):
    """裁定记录不足以冻结成目标图。"""


def accepted_items(log: kbp.contracts.adjudication.AdjudicationLog):
    """取出接受项，保持候选原始顺序。"""
    return tuple(i for i in log.items
                 if i.decision == kbp.contracts.adjudication.ACCEPTED)


def rejected_items(log: kbp.contracts.adjudication.AdjudicationLog):
    """取出驳回项，保持候选原始顺序。"""
    return tuple(i for i in log.items
                 if i.decision == kbp.contracts.adjudication.REJECTED)


def freeze(log: kbp.contracts.adjudication.AdjudicationLog,
           map_version: str) -> kbp.contracts.targetmap.TargetMap:
    """接受项凝固为目标图：概念按标签去重，编号按首次出现顺序。"""
    _check_version(map_version)
    _check_connections(log)
    concepts, index = _collect(log)
    props = _propositions(log, index)
    if not concepts:
        raise FreezeError("没有可接受的概念，无法冻结")
    return kbp.contracts.targetmap.TargetMap(
        map_version=map_version, vocab=log.vocab,
        concepts=tuple(concepts), propositions=tuple(props))


def _check_version(map_version: str) -> None:
    if not map_version or not map_version.strip():
        raise FreezeError("版本号不得为空")


def _check_connections(log: kbp.contracts.adjudication.AdjudicationLog) -> None:
    allowed = set(log.vocab.connections)
    for item in log.items:
        if item.candidate.connection not in allowed:
            raise FreezeError("裁定项含词表外连接词: "
                              + item.candidate.connection)


def _collect(log: kbp.contracts.adjudication.AdjudicationLog):
    index: dict[str, str] = {}
    concepts: list[kbp.contracts.targetmap.Concept] = []
    for item in accepted_items(log):
        for label in (item.candidate.head, item.candidate.tail):
            if label not in index:
                cid = "c" + str(len(concepts) + 1)
                index[label] = cid
                concepts.append(kbp.contracts.targetmap.Concept(concept_id=cid, label=label))
    return concepts, index


def _propositions(log: kbp.contracts.adjudication.AdjudicationLog, index: dict):
    props: list[kbp.contracts.targetmap.Proposition] = []
    seen: set[tuple[str, str, str]] = set()
    for item in accepted_items(log):
        cand = item.candidate
        key = (cand.head, cand.connection, cand.tail)
        if key in seen or cand.head == cand.tail:
            continue
        seen.add(key)
        props.append(kbp.contracts.targetmap.Proposition(
            head_id=index[cand.head], connection=cand.connection,
            tail_id=index[cand.tail]))
    return props
