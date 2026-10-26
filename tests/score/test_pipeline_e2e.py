"""全链路验证：教材文本 → 抽取 → 裁定 → 冻结 → 拆 kit → 提交 → 评分。

本用例是装配层：它按需把各 feature 的模块路径接起来，feature 之间仍互不 import。
不加载 ONNX 权重，用注入的假引擎验证流程，避免测试依赖 448MB 模型。
"""


import kbp.contracts.adjudication as adjudication  # noqa: E402
import kbp.extract.extract_service as extract_service  # noqa: E402
import kbp.kit.freeze as freeze  # noqa: E402
import kbp.contracts.report as report  # noqa: E402
import kbp.score.score_service as score_service  # noqa: E402
import kbp.kit.split as split  # noqa: E402
import kbp.contracts.submission as submission  # noqa: E402
import kbp.extract.vocab as vocab_mod  # noqa: E402


class FixedEngine:
    """测试方自建引擎：返回预置抽取结果，不加载模型。"""

    def __init__(self, payload):
        self.payload = payload

    def extract(self, text, schema):
        return self.payload


def test_教材到分数的全链路():
    vocab = vocab_mod.build({
        "vocab_id": "心理学", "version": "v1",
        "connections": ["包括", "属于"],
    })
    nodes = [{"text": "记忆", "probability": 0.95},
             {"text": "短时记忆", "probability": 0.9},
             {"text": "记忆系统", "probability": 0.85}]
    pays = [{"包括": nodes, "属于": nodes}]

    result = extract_service.extract("记忆包括短时记忆，短时记忆属于记忆系统。",
                                     vocab, engine=FixedEngine(pays))
    assert len(result.triples) >= 2

    items = []
    for cand in result.triples:
        keep = ((cand.head, cand.connection, cand.tail)
                in {("记忆", "包括", "短时记忆"),
                    ("短时记忆", "属于", "记忆系统")})
        items.append(adjudication.Adjudication(
            candidate=cand,
            decision=adjudication.ACCEPTED if keep else adjudication.REJECTED,
            reason="" if keep else "教材未提及"))

    log = adjudication.AdjudicationLog(batch_id="b1", vocab=vocab,
                                       items=tuple(items))
    target = freeze.freeze(log, "v1")
    kit = split.split(target)
    assert len(target.propositions) >= 1

    ids = {c.label: c.concept_id for c in kit.concepts}
    sub = submission.Submission(
        map_version="v1", mode=submission.TEST,
        propositions=(submission.SubmittedProposition(
            head_id=ids["记忆"], connection="包括",
            tail_id=ids["短时记忆"]),),
        started_at="", submitted_at="2026-10-25T10:00:00",
        participant_id=1, material_id=1, session=1)

    scored = score_service.score(target, sub)
    assert scored.total_propositions == len(target.propositions)
    assert scored.correct_propositions == 1
    assert 0.0 < score_service.ratio(scored) <= 1.0
    assert isinstance(scored.errors, tuple)
    assert all(e.kind in report.ERROR_KINDS for e in scored.errors)
