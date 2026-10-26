"""extract 测试共用的小工具：词表、配置、候选与假引擎。"""

import kbp.contracts.extractconfig as extractconfig
import kbp.contracts.triple as triple
import kbp.extract.vocab as vocab_mod

VOCAB_JSON = {"vocab_id": "心理学", "version": "v1",
              "connections": ["属于", "导致"]}


def make_vocab():
    return vocab_mod.build(dict(VOCAB_JSON))


def make_config(**kw):
    base = dict(provider=extractconfig.OPENAI_COMPATIBLE,
                model="some-model",
                base_url="http://127.0.0.1:8788",
                timeout_s=60, max_chars=12000, enabled=True)
    base.update(kw)
    return extractconfig.ExtractConfig(**base)


def body(*props):
    return {"propositions": list(props)}


def prop(head, connection, tail, evidence="", confidence=None):
    item = {"head": head, "connection": connection, "tail": tail,
            "evidence": evidence}
    if confidence is not None:
        item["confidence"] = confidence
    return item


class FakeEngine:
    """测试方自建引擎：按调用顺序返回预设结果，不发起任何网络请求。"""

    def __init__(self, batches):
        self.batches = list(batches)
        self.calls = []

    def extract(self, text, vocab, config):
        self.calls.append((text, vocab, config))
        if not self.batches:
            return ()
        return tuple(self.batches.pop(0))


def cand(head, connection, tail):
    return triple.TripleCandidate(head=head, connection=connection,
                                  tail=tail, confidence=0.5)
