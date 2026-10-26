"""把 DeepSeek 的输出规范化成契约三元组。

模型的输出不可信：可能越出词表、可能反向、可能重复、可能压根不是数组。
本文件是唯一的收口处，所有异常都在这里被丢弃或降级，绝不静默通过。
"""

import kbp.contracts.extractconfig
import kbp.contracts.triple
import kbp.extract.deepseek_client
import kbp.extract.prompt

MAX_PROPOSITIONS = 200
MAX_FIELD = 200


class ParseError(ValueError):
    """模型输出结构不可用。"""


def extract(text: str, vocab: kbp.contracts.triple.Vocab,
            config: kbp.contracts.extractconfig.ExtractConfig,
            transport=None) -> list[kbp.contracts.triple.TripleCandidate]:
    """一次抽取：构造提示词、调接口、规范化。"""
    messages = kbp.extract.prompt.build(vocab, text, config)
    body = kbp.extract.deepseek_client.chat(config, messages,
                                            transport=transport)
    return to_candidates(body, vocab)


def to_candidates(body: dict,
                  vocab: kbp.contracts.triple.Vocab
                  ) -> list[kbp.contracts.triple.TripleCandidate]:
    """把模型 JSON 转成契约三元组，越界与重复一律丢弃。"""
    raw = body.get("propositions")
    if raw is None:
        raise ParseError("缺少 propositions 字段")
    if not isinstance(raw, list):
        raise ParseError("propositions 不是数组")
    allowed = set(vocab.connections)
    seen = set()
    out = []
    for item in raw[:MAX_PROPOSITIONS]:
        cand = _one(item, allowed, seen)
        if cand is not None:
            out.append(cand)
    return out


def _one(item, allowed: set, seen: set):
    if not isinstance(item, dict):
        return None
    head = _text(item.get("head"))
    tail = _text(item.get("tail"))
    connection = _text(item.get("connection"))
    if not head or not tail or connection not in allowed:
        return None
    if head == tail:
        return None
    key = (head, connection, tail)
    if key in seen:
        return None
    seen.add(key)
    return kbp.contracts.triple.TripleCandidate(
        head=head, connection=connection, tail=tail,
        confidence=_conf(item),
        evidence=_text(item.get("evidence"))[:MAX_FIELD])


def _text(value) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:MAX_FIELD]


def _conf(item) -> float:
    raw = item.get("confidence")
    if isinstance(raw, (int, float)):
        return min(max(float(raw), 0.0), 1.0)
    return 0.0
