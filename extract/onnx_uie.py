import os
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer, models, normalizers, pre_tokenizers

import triple

DEFAULT_DIR = "tmp/uie"
MODEL_FILE = "inference.onnx"
VOCAB_FILE = "vocab.txt"
UNK = "[UNK]"
CLS = "[CLS]"
SEP = "[SEP]"
PAD = "[PAD]"
CLS_ID = 1
SEP_ID = 2
MAX_LEN = 512
POSITION_PROB = 0.5


class OnnxUnavailable(RuntimeError):
    """ONNX 权重或运行库不可用。"""


class OnnxUieExtractor:
    """ONNX 版 UIE 适配器：权重来自 PaddleNLP uie-base 的离线转换。

    构造不加载模型；首次 extract 才建会话，避免拖慢服务启动。
    """

    def __init__(self, model_dir: str | None = None,
                 position_prob: float = POSITION_PROB) -> None:
        self._dir = Path(model_dir or os.environ.get("KBP_UIE_DIR", DEFAULT_DIR))
        self._limit = position_prob
        self._session = None
        self._tokenizer = None

    def _load(self):
        if self._session is not None:
            return self._session, self._tokenizer
        model = self._dir / MODEL_FILE
        vocab = self._dir / VOCAB_FILE
        if not model.exists() or not vocab.exists():
            raise OnnxUnavailable("缺少 ONNX 权重: " + str(model))
        try:
            import onnxruntime
        except Exception as exc:
            raise OnnxUnavailable("未安装 onnxruntime 或 tokenizers") from exc
        self._session = onnxruntime.InferenceSession(
            str(model), providers=["CPUExecutionProvider"])
        self._tokenizer = _build_tokenizer(str(vocab))
        return self._session, self._tokenizer

    def extract(self, text: str, schema: dict) -> list[dict]:
        """对单段文本按 schema 的每个连接词各抽一遍，返回 UIEMarkup 结构。"""
        session, tokenizer = self._load()
        connections = schema.get("概念") or []
        out: list[dict] = []
        for connection in connections:
            spans = self._spans(session, tokenizer, connection, text)
            if spans:
                out.append({connection: spans})
        return out

    def _spans(self, session, tokenizer, connection: str, text: str) -> list[dict]:
        ids, offsets, split_at = _encode(tokenizer, connection, text)
        if not ids:
            return []
        feeds = _feeds(ids, split_at)
        start, end = session.run(["start_prob", "end_prob"], feeds)
        return _decode(start[0], end[0], offsets, ids, self._limit)


def _build_tokenizer(vocab_path: str) -> Tokenizer:
    tk = Tokenizer(models.WordPiece.from_file(vocab_path, unk_token=UNK))
    tk.normalizer = normalizers.BertNormalizer(
        clean_text=True, handle_chinese_chars=True,
        strip_accents=True, lowercase=True)
    tk.pre_tokenizer = pre_tokenizers.BertPreTokenizer()
    return tk


def _encode(tokenizer: Tokenizer, prompt: str, text: str):
    """按 [CLS] prompt [SEP] text [SEP] 拼接，返回 ids 与正文的 offset 映射。"""
    p = tokenizer.encode(prompt, add_special_tokens=False)
    t = tokenizer.encode(text, add_special_tokens=False)
    prompt_len = len(p.ids)
    ids = [CLS_ID] + p.ids + [SEP_ID] + t.ids[: MAX_LEN - prompt_len - 3] + [SEP_ID]
    offsets = [(0, 0)] + [(0, 0)] * prompt_len + [(0, 0)]
    offsets += t.offsets[: MAX_LEN - prompt_len - 3] + [(0, 0)]
    return ids, offsets, prompt_len + 2


def _feeds(ids: list[int], split_at: int) -> dict:
    """split_at 是正文首个 token 的下标：之前为句 A（prompt），之后为句 B。"""
    arr = np.array([ids], dtype="int64")
    types = np.zeros_like(arr)
    types[0, split_at:] = 1
    return {
        "input_ids": arr,
        "token_type_ids": types,
        "attention_mask": np.ones_like(arr),
    }


def _decode(start, end, offsets, ids, limit: float) -> list[dict]:
    """把 start/end 概率解成互不重叠的 span，坐标换回正文位置。"""
    starts = [(i, float(p)) for i, p in enumerate(start) if p > limit]
    ends = [(i, float(p)) for i, p in enumerate(end) if p > limit]
    spans = _pair(starts, ends)
    out = []
    for (si, sp), (ei, ep) in sorted(spans):
        begin, stop = offsets[si][0], offsets[ei][1]
        if stop <= begin:
            continue
        out.append({"text": None, "start": begin, "end": stop,
                    "probability": sp * ep})
    return out


def _pair(starts, ends):
    """按下标顺序配对 start 与 end，每个下标只用一次。"""
    paired, used = [], set()
    for si, sp in starts:
        for ei, ep in ends:
            if ei >= si and ei not in used:
                paired.append(((si, sp), (ei, ep)))
                used.add(ei)
                break
    return paired


def raw_to_triples(raw: list[dict], vocab: triple.Vocab,
                   text: str = "") -> list[triple.TripleCandidate]:
    """UIE 原始输出转契约三元组；text 为空时 span 须自带 text 字段。

    兼容两种输出：本适配器的 span 结构，以及 PaddleNLP 的
    {连接词: [{text, probability}...]} 结构。
    """
    if _has_text(raw):
        return _from_text(raw, vocab)
    return to_triples(raw, text, vocab)


def _has_text(raw: list[dict]) -> bool:
    for entry in raw:
        for _, spans in (entry or {}).items():
            for span in spans or []:
                if span.get("text") is not None:
                    return True
    return False


def _from_text(raw: list[dict],
               vocab: triple.Vocab) -> list[triple.TripleCandidate]:
    allowed = set(vocab.connections)
    out: list[triple.TripleCandidate] = []
    for entry in raw:
        for connection, spans in (entry or {}).items():
            if connection not in allowed:
                continue
            nodes = [s for s in (spans or []) if s.get("text")]
            for head in nodes:
                for tail in nodes:
                    if head is tail:
                        continue
                    out.append(triple.TripleCandidate(
                        head=head["text"], connection=connection,
                        tail=tail["text"],
                        confidence=_conf(head, tail)))
    return out


def _conf(head: dict, tail: dict) -> float:
    return float(min(head.get("probability", 0.5),
                     tail.get("probability", 0.5)))


def to_triples(raw: list[dict], text: str,
               vocab: triple.Vocab) -> list[triple.TripleCandidate]:
    """ONNX 输出转契约三元组：同连接词下的 span 两两成对。"""
    allowed = set(vocab.connections)
    out: list[triple.TripleCandidate] = []
    for entry in raw:
        for connection, spans in (entry or {}).items():
            if connection not in allowed:
                continue
            out.extend(_cross(connection, spans, text))
    return out


def _cross(connection: str, spans: list[dict],
           text: str) -> list[triple.TripleCandidate]:
    nodes = [_fill(s, text) for s in spans]
    nodes = [n for n in nodes if n["text"]]
    out = []
    for head in nodes:
        for tail in nodes:
            if head is tail:
                continue
            out.append(triple.TripleCandidate(
                head=head["text"], connection=connection,
                tail=tail["text"],
                confidence=float(min(head["probability"],
                                     tail["probability"]))))
    return out


def _fill(span: dict, text: str) -> dict:
    if span.get("text") is None:
        span = dict(span)
        span["text"] = text[span["start"]:span["end"]]
    return span
