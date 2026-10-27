import kbp.contracts.extraction
import kbp.contracts.triple

MAX_PROPOSITIONS = 400
MAX_FIELD = 200
MAX_CONCEPT = 20  # 概念字数上限；超过只标记可疑，不丢

SCORE_HIT = 1.0  # evidence 在原文逐字命中
SCORE_MISS = 0.4  # 有 evidence 但对不上原文（多半是改写过的）
SCORE_EMPTY = 0.2  # 没给 evidence，无从核对
SCORE_SUSPECT = 0.15  # 可疑的上限分：一律排到最后
OUT_OF_ORDER = 0.6  # 出现位置与模型输出顺序不一致时的折扣


REASON_UNUSABLE = "结构不可用"  # 不是对象，或缺头/尾/连接词
REASON_UNKNOWN = "连接词不在词表"
REASON_SELF = "自环"
REASON_STUFFED = "概念里含连接词"
REASON_DUPLICATE = "重复"


class ParseError(ValueError):
    """模型输出结构不可用。"""


def collect(body: dict, vocab: kbp.contracts.triple.Vocab,
            text: str = "") -> tuple[list[kbp.contracts.triple.TripleCandidate],
                                     list[kbp.contracts.extraction.
                                          DiscardedCandidate]]:
    """收口一次模型输出，同时给出被丢掉的那些与原因（D12 留档用）。"""
    raw = body.get("propositions")
    if raw is None:
        raise ParseError("缺少 propositions 字段")
    if not isinstance(raw, list):
        raise ParseError("propositions 不是数组")
    allowed = set(vocab.connections)
    seen: set[tuple[str, str, str]] = set()
    out: list[kbp.contracts.triple.TripleCandidate] = []
    drops: list[kbp.contracts.extraction.DiscardedCandidate] = []
    for item in raw[:MAX_PROPOSITIONS]:
        cand, reason = _judge(item, allowed, seen, text)
        if cand is None:
            drops.append(_drop(item, reason))
        else:
            out.append(cand)
    return _rank(out, text), drops


def to_candidates(body: dict, vocab: kbp.contracts.triple.Vocab,
                  text: str = "") -> list[kbp.contracts.triple.TripleCandidate]:
    """把模型 JSON 转成契约三元组，越界、自环、重复与塞了连接词的都丢弃。

    这是唯一的收口处：模型的输出不可信，越界连接词粘贴即被丢弃，
    不依赖模型自觉。置信度不用模型自报的（它几乎恒为 1），
    改成本地代理分：evidence 逐字命中原文才算实，排在前面。
    """
    return collect(body, vocab, text)[0]


def _judge(item, allowed: set, seen: set, text: str):
    if not isinstance(item, dict):
        return None, REASON_UNUSABLE
    head = _text(item.get("head"))
    tail = _text(item.get("tail"))
    connection = _text(item.get("connection"))
    if not head or not tail or not connection:
        return None, REASON_UNUSABLE
    if connection not in allowed:
        return None, REASON_UNKNOWN
    if head == tail:
        return None, REASON_SELF
    if _stuffed(head, allowed) or _stuffed(tail, allowed):
        return None, REASON_STUFFED
    key = (head, connection, tail)
    if key in seen:
        return None, REASON_DUPLICATE
    seen.add(key)
    return kbp.contracts.triple.TripleCandidate(
        head=head, connection=connection, tail=tail, confidence=0.0,
        evidence=_evidence(item, text),
        suspect=len(head) > MAX_CONCEPT or len(tail) > MAX_CONCEPT), ""


def _drop(item, reason: str) -> kbp.contracts.extraction.DiscardedCandidate:
    """丢掉的东西也要能查：头尾与连接词原样留，够不上就留空串。"""
    get = item.get if isinstance(item, dict) else lambda _key: None
    return kbp.contracts.extraction.DiscardedCandidate(
        head=_text(get("head")), connection=_text(get("connection")),
        tail=_text(get("tail")), reason=reason)


def _stuffed(value: str, allowed: set) -> bool:
    """概念里塞了连接词，说明模型把整个从句当概念了，这是最强信号。"""
    return any(word in value for word in allowed)


def _rank(cands, text: str) -> list[kbp.contracts.triple.TripleCandidate]:
    """按代理分降序；同分保持模型给的先后。输出只由输入决定，可复现。"""
    ranked = []
    last_pos = -1
    for index, cand in enumerate(cands):
        score, pos = _score(cand, text)
        if pos >= 0:
            if pos < last_pos:
                score *= OUT_OF_ORDER
            last_pos = max(last_pos, pos)
        if cand.suspect:
            score = min(score, SCORE_SUSPECT)
        ranked.append((_scored(cand, score), index))
    ranked.sort(key=lambda pair: (-pair[0].confidence, pair[1]))
    return [cand for cand, _ in ranked]


def _scored(cand, score: float):
    return kbp.contracts.triple.TripleCandidate(
        head=cand.head, connection=cand.connection, tail=cand.tail,
        confidence=round(min(max(score, 0.0), 1.0), 4),
        evidence=cand.evidence, suspect=cand.suspect)


def _score(cand, text: str) -> tuple[float, int]:
    """evidence 是否逐字命中原文；顺带给出它在原文中的位置（未命中为 -1）。"""
    if not cand.evidence or not text:
        return SCORE_EMPTY, -1
    pos = text.find(cand.evidence)
    if pos < 0:
        return SCORE_MISS, -1
    return SCORE_HIT, pos


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
