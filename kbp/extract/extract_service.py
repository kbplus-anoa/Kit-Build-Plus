import hashlib

import kbp.contracts.extractconfig
import kbp.contracts.extraction
import kbp.contracts.triple
import kbp.extract.engine
import kbp.extract.normalize
import kbp.extract.vocab
import kbp.extract.window

MAX_TRIPLES = 5000


class ExtractError(ValueError):
    """抽取不可进行（词表为空、配置不可用、未配密钥等）。"""


def extract(text: str, vocab: kbp.contracts.triple.Vocab,
            config: kbp.contracts.extractconfig.ExtractConfig | None = None,
            engine=None) -> kbp.contracts.triple.ExtractionResult:
    """编排入口：逐段抽取、按置信度合并去重。引擎可注入以便测试。"""
    return extract_and_discards(text, vocab, config, engine)[0]


def extract_and_discards(
        text: str, vocab: kbp.contracts.triple.Vocab,
        config: kbp.contracts.extractconfig.ExtractConfig | None = None,
        engine=None) -> tuple[kbp.contracts.triple.ExtractionResult,
                              tuple[kbp.contracts.extraction.
                                    DiscardedCandidate, ...]]:
    """同 extract，另带回机器侧丢掉的候选，供留档（D12）。"""
    cfg = config or kbp.contracts.extractconfig.default_config()
    _check(vocab, cfg)
    model = engine or kbp.extract.engine.ChatEngine()
    found: list[kbp.contracts.triple.TripleCandidate] = []
    drops: list[kbp.contracts.extraction.DiscardedCandidate] = []
    seen: set[tuple[str, str, str]] = set()
    for chunk in kbp.extract.window.split(text, cfg.max_chars):
        cands = model.extract(chunk, vocab, cfg)
        drops.extend(getattr(model, "last_discards", ()))
        for cand in cands:
            _keep(cand, seen, found)
            if len(found) >= MAX_TRIPLES:
                return _result(vocab, found), tuple(drops)
    return _result(vocab, found), tuple(drops)


def _check(vocab: kbp.contracts.triple.Vocab,
           cfg: kbp.contracts.extractconfig.ExtractConfig) -> None:
    if not vocab.connections:
        raise ExtractError("连接词表为空，无法抽取")
    reason = kbp.contracts.extractconfig.config_error(cfg)
    if reason:
        raise ExtractError(reason)


def _keep(cand: kbp.contracts.triple.TripleCandidate, seen: set,
          found: list[kbp.contracts.triple.TripleCandidate]) -> None:
    key = kbp.extract.window.merge_key(cand.head, cand.connection, cand.tail)
    if key in seen:
        return
    seen.add(key)
    found.append(cand)


def _result(vocab: kbp.contracts.triple.Vocab,
            found) -> kbp.contracts.triple.ExtractionResult:
    ordered = sorted(found, key=lambda c: c.confidence, reverse=True)
    return kbp.contracts.triple.ExtractionResult(vocab=vocab,
                                                 triples=tuple(ordered))


def record(result: kbp.contracts.triple.ExtractionResult, batch_id: str,
           config: kbp.contracts.extractconfig.ExtractConfig, text: str,
           sections: int = 0, raw: str = "",
           created_at: str = "",
           discards: tuple = ()) -> kbp.contracts.extraction.ExtractionRecord:
    """把一次抽取包成留档记录：只存原文指纹与统计量，不存正文。"""
    return kbp.contracts.extraction.ExtractionRecord(
        batch_id=batch_id, vocab=result.vocab, config=config,
        text_sha256=sha256(text), chars=len(text or ""),
        sections=sections, raw=raw, triples=result.triples,
        created_at=created_at, discards=discards)


def sha256(text: str) -> str:
    """原文指纹，用于判断“这两次抽的是不是同一段话”。"""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def load_vocab(path: str) -> kbp.contracts.triple.Vocab:
    return kbp.extract.vocab.load(path)
