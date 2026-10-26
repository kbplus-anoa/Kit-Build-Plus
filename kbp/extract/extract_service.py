import kbp.extract.onnx_uie
import kbp.extract.schema
import kbp.contracts.triple
import kbp.extract.vocab
import kbp.extract.window

MAX_TRIPLES = 5000


def extract(text: str, vocab: kbp.contracts.triple.Vocab,
            engine=None) -> kbp.contracts.triple.ExtractionResult:
    """纯函数式入口：文本 + 词表进，候选三元组出。engine 缺省用 ONNX UIE。"""
    kbp.extract.schema.validate_vocab(vocab)
    model = engine or kbp.extract.onnx_uie.OnnxUieExtractor()
    schema = kbp.extract.schema.to_schema(vocab)
    seen: set[tuple[str, str, str]] = set()
    found: list[kbp.contracts.triple.TripleCandidate] = []
    for chunk in kbp.extract.window.split(text):
        raw = model.extract(chunk, schema)
        for cand in kbp.extract.onnx_uie.raw_to_triples(raw, vocab, chunk):
            _keep(cand, seen, found)
            if len(found) >= MAX_TRIPLES:
                return _result(vocab, found)
    return _result(vocab, found)


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
    return kbp.contracts.triple.ExtractionResult(vocab=vocab, triples=tuple(ordered))


def load_vocab(path: str) -> kbp.contracts.triple.Vocab:
    return kbp.extract.vocab.load(path)
