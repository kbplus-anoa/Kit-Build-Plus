import kbp.contracts.triple

MAX_PROPOSITIONS = 400
MAX_FIELD = 200


class ParseError(ValueError):
    """模型输出结构不可用。"""


def to_candidates(body: dict, vocab: kbp.contracts.triple.Vocab,
                  text: str = "") -> list[kbp.contracts.triple.TripleCandidate]:
    """把模型 JSON 转成契约三元组，越界、自环与重复一律丢弃。

    这是唯一的收口处：模型的输出不可信，越界连接词粘贴即被丢弃，
    不依赖模型自觉。evidence 缺失时降级为空串，不阻断抽取。
    """
    raw = body.get("propositions")
    if raw is None:
        raise ParseError("缺少 propositions 字段")
    if not isinstance(raw, list):
        raise ParseError("propositions 不是数组")
    allowed = set(vocab.connections)
    seen: set[tuple[str, str, str]] = set()
    out: list[kbp.contracts.triple.TripleCandidate] = []
    for item in raw[:MAX_PROPOSITIONS]:
        cand = _one(item, allowed, seen, text)
        if cand is not None:
            out.append(cand)
    return out


def _one(item, allowed: set, seen: set, text: str):
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
        confidence=_conf(item), evidence=_evidence(item, text))


def _text(value) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:MAX_FIELD]


def _evidence(item, text: str) -> str:
    """模型给了就压空白截断；没给而原文够长就退回首句，绝不编造。"""
    given = _text(item.get("evidence"))
    if given:
        return given[:MAX_FIELD]
    body = (text or "").strip()
    if not body:
        return ""
    for sep in ("。", "；", "\n"):
        if sep in body:
            return body.split(sep)[0][:MAX_FIELD]
    return body[:MAX_FIELD]


def _conf(item) -> float:
    raw = item.get("confidence")
    if isinstance(raw, (int, float)):
        return min(max(float(raw), 0.0), 1.0)
    return 1.0
