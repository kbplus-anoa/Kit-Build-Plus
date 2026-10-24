import schema as schema_mod
import triple
import uie
import vocab as vocab_mod
import window

MAX_TRIPLES = 5000


def extract(text: str, vocab: triple.Vocab,
            engine=None) -> triple.ExtractionResult:
    """纯函数式入口：文本 + 词表进，候选三元组出。engine 缺省用 UIE。"""
    schema_mod.validate_vocab(vocab)
    model = engine or uie.UieExtractor()
    schema = schema_mod.to_schema(vocab)
    seen: set[tuple[str, str, str]] = set()
    found: list[triple.TripleCandidate] = []
    for chunk in window.split(text):
        for cand in uie.raw_to_triples(model.extract(chunk, schema), vocab):
            _keep(cand, seen, found)
            if len(found) >= MAX_TRIPLES:
                return _result(vocab, found)
    return _result(vocab, found)


def _keep(cand: triple.TripleCandidate, seen: set,
          found: list[triple.TripleCandidate]) -> None:
    key = window.merge_key(cand.head, cand.connection, cand.tail)
    if key in seen:
        return
    seen.add(key)
    found.append(cand)


def _result(vocab: triple.Vocab,
            found: list[triple.TripleCandidate]) -> triple.ExtractionResult:
    ordered = sorted(found, key=lambda c: c.confidence, reverse=True)
    return triple.ExtractionResult(vocab=vocab, triples=tuple(ordered))


def load_vocab(path: str) -> triple.Vocab:
    return vocab_mod.load(path)
