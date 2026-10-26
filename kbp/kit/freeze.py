import kbp.contracts.adjudication
import kbp.contracts.targetmap
import kbp.contracts.triple
import kbp.kit._rules


class FreezeError(ValueError):
    """裁定记录或抽取结果不足以冻结成目标图。"""


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
    """开发期人工路：接受项凝固为目标图。"""
    _check_version(map_version)
    _check_connections(log)
    edges = [(i.candidate.head, i.candidate.connection, i.candidate.tail)
             for i in accepted_items(log)]
    return _build(log.vocab, edges, map_version)


def freeze_auto(result: kbp.contracts.triple.ExtractionResult,
                map_version: str) -> kbp.contracts.targetmap.TargetMap:
    """运行期自动路：模型抽出的候选直接冻结，无人逐条裁定。

    与人工路共用 _rules：越界、自环、重复同样丢弃，指纹同样计算。
    """
    _check_version(map_version)
    _check_vocab_connections(result.vocab)
    edges = [(c.head, c.connection, c.tail) for c in result.triples]
    return _build(result.vocab, edges, map_version)


def _build(vocab: kbp.contracts.triple.Vocab, edges, map_version: str):
    kept = kbp.kit._rules.ordered_propositions(edges)
    concepts = _concepts(edges)
    if not concepts:
        raise FreezeError("没有可接受的概念，无法冻结")
    props = _propositions(kept)
    target = kbp.contracts.targetmap.TargetMap(
        map_version=map_version, vocab=vocab,
        concepts=tuple(concepts), propositions=tuple(props))
    return kbp.contracts.targetmap.TargetMap(
        map_version=target.map_version, vocab=target.vocab,
        concepts=target.concepts, propositions=target.propositions,
        fingerprint=kbp.kit._rules.fingerprint(target))


def _concepts(kept) -> list[kbp.contracts.targetmap.Concept]:
    """概念按标签去重，编号按首次出现顺序。"""
    labels = _first_seen_labels(kept)
    return [kbp.contracts.targetmap.Concept(concept_id="c" + str(i + 1), label=lab)
            for i, lab in enumerate(labels)]


def _propositions(kept) -> list[kbp.contracts.targetmap.Proposition]:
    labels = _first_seen_labels(kept)
    index = {label: "c" + str(i + 1) for i, label in enumerate(labels)}
    return [kbp.contracts.targetmap.Proposition(
                head_id=index[head], connection=connection, tail_id=index[tail])
            for head, connection, tail in kept]


def _first_seen_labels(kept) -> list[str]:
    labels: list[str] = []
    for head, _, tail in kept:
        for label in (head, tail):
            if label not in labels:
                labels.append(label)
    return labels


def _check_version(map_version: str) -> None:
    if not map_version or not map_version.strip():
        raise FreezeError("版本号不得为空")


def _check_connections(log: kbp.contracts.adjudication.AdjudicationLog) -> None:
    allowed = set(log.vocab.connections)
    for item in log.items:
        if item.candidate.connection not in allowed:
            raise FreezeError("裁定项含词表外连接词: "
                              + item.candidate.connection)


def _check_vocab_connections(vocab: kbp.contracts.triple.Vocab) -> None:
    if not vocab.connections:
        raise FreezeError("词表为空，无法冻结")
