"""全链路验证：教材文本 → 抽取 → 冻结 → 拆 kit → 提交 → 评分。

本用例是装配层：它按需把各 feature 的模块路径接起来，feature 之间仍互不 import。
用注入的假引擎验证流程，不发起任何网络请求，也不依赖任何模型权重。
"""


import kbp.contracts.extractconfig as extractconfig  # noqa: E402
import kbp.contracts.report as report  # noqa: E402
import kbp.contracts.triple as triple  # noqa: E402
import kbp.contracts.submission as submission  # noqa: E402
import kbp.extract.extract_service as extract_service  # noqa: E402
import kbp.extract.vocab as vocab_mod  # noqa: E402
import kbp.kit.kit_service as kit_service  # noqa: E402
import kbp.score.score_service as score_service  # noqa: E402


class FixedEngine:
    """测试方自建引擎：返回预置的契约三元组，不发请求。"""

    def __init__(self, candidates):
        self.candidates = tuple(candidates)

    def extract(self, text, vocab, config):
        return self.candidates


def make_config():
    return extractconfig.ExtractConfig(
        provider=extractconfig.OPENAI_COMPATIBLE, model="some-model",
        base_url="http://127.0.0.1:8788", timeout_s=60, max_chars=12000,
        enabled=True)


def cand(head, connection, tail, confidence=0.9, evidence=""):
    return triple.TripleCandidate(head=head, connection=connection, tail=tail,
                                  confidence=confidence, evidence=evidence)


def test_教材到分数的全链路():
    vocab = vocab_mod.build({"vocab_id": "心理学", "version": "v1",
                             "connections": ["包括", "属于"]})
    engine = FixedEngine([
        cand("记忆", "包括", "短时记忆", 0.95),
        cand("短时记忆", "属于", "记忆系统", 0.9),
        cand("长时记忆", "包括", "容量", 0.2),
    ])

    result = extract_service.extract("记忆包括短时记忆，短时记忆属于记忆系统。",
                                     vocab, config=make_config(), engine=engine)
    assert len(result.triples) == 3

    target, kit = kit_service.build_kit_auto(result, "v1")
    assert len(target.propositions) == 3
    assert len(target.fingerprint) == 16

    ids = {c.label: c.concept_id for c in kit.concepts}
    sub = submission.Submission(
        map_version="v1", fingerprint=target.fingerprint,
        mode=submission.TEST,
        propositions=(submission.SubmittedProposition(
            head_id=ids["记忆"], connection="包括",
            tail_id=ids["短时记忆"]),),
        started_at="", submitted_at="2026-10-25T10:00:00",
        participant_id=1, material_id=1, time_point=submission.POST,
        submit_seq=1)

    scored = score_service.score(target, sub)
    assert scored.total_propositions == len(target.propositions)
    assert scored.correct_propositions == 1
    assert 0.0 < score_service.fms(scored) <= 100.0
    assert isinstance(scored.errors, tuple)
    assert all(e.kind in report.ERROR_KINDS for e in scored.errors)


def test_同一文本两次自动裁出同一指纹():
    vocab = vocab_mod.build({"vocab_id": "心理学", "version": "v1",
                             "connections": ["包括"]})
    engine = FixedEngine([cand("记忆", "包括", "短时记忆")])
    cfg = make_config()
    first = extract_service.extract("记忆包括短时记忆", vocab, config=cfg,
                                    engine=engine)
    second = extract_service.extract("记忆包括短时记忆", vocab, config=cfg,
                                     engine=engine)
    a = kit_service.build_kit_auto(first, "v1")[0]
    b = kit_service.build_kit_auto(second, "v1")[0]
    assert a.fingerprint == b.fingerprint
