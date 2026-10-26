from dataclasses import dataclass


@dataclass(frozen=True)
class Vocab:
    """连接词表契约：封闭集合，抽取结果不得越界。"""

    vocab_id: str  # 学科词表标识，如 心理学；不可空
    vocab_version: str  # 词表版本，如 v1；不可空
    connections: tuple[str, ...]  # 允许的连接词；不可空，元素唯一且非空


@dataclass(frozen=True)
class TripleCandidate:
    """extract 契约：一条候选三元组，连接词必在词表内。"""

    head: str  # 概念 A 的字面；不可空
    connection: str  # 连接词，必须属于 Vocab.connections；不可空
    tail: str  # 概念 B 的字面；不可空
    confidence: float  # UIE 置信度；单位：0~1 的无量纲数；不可空


@dataclass(frozen=True)
class ExtractionResult:
    """extract 契约：一次抽取的全部候选三元组。"""

    vocab: Vocab  # 本次抽取使用的词表；不可空
    triples: tuple[TripleCandidate, ...]  # 候选三元组，按置信度降序；可为空元组


def in_vocab(vocab: Vocab, connection: str) -> bool:
    """纯函数契约：连接词是否落在词表内。"""
    ...
