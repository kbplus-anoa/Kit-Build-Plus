import pytest

import kbp.contracts.adjudication as adjudication
import kbp.contracts.targetmap as targetmap
import kbp.contracts.triple as triple
import kbp.kit._rules as rules
import kbp.kit.freeze as freeze

VOCAB = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("包括", "属于", "导致"))


def t(head, connection, tail, confidence=0.9, evidence=""):
    return triple.TripleCandidate(head=head, connection=connection, tail=tail,
                                  confidence=confidence, evidence=evidence)


def result(*candidates, vocab=None):
    return triple.ExtractionResult(vocab=vocab or VOCAB,
                                   triples=tuple(candidates))


def test_自动路冻结出概念与命题():
    target = freeze.freeze_auto(result(t("记忆", "包括", "短时记忆")), "v1")
    assert [c.label for c in target.concepts] == ["记忆", "短时记忆"]
    assert target.propositions[0].connection == "包括"


def test_自动路丢弃自环():
    target = freeze.freeze_auto(
        result(t("记忆", "包括", "记忆"), t("记忆", "包括", "短时记忆")), "v1")
    assert len(target.propositions) == 1


def test_自动路丢弃重复命题():
    target = freeze.freeze_auto(
        result(t("记忆", "包括", "短时记忆"), t("记忆", "包括", "短时记忆")), "v1")
    assert len(target.propositions) == 1


def test_自动路空结果拒绝冻结():
    with pytest.raises(freeze.FreezeError):
        freeze.freeze_auto(result(), "v1")


def test_自动路空版本号拒绝冻结():
    with pytest.raises(freeze.FreezeError):
        freeze.freeze_auto(result(t("A", "包括", "B")), " ")


def test_自动路空词表拒绝冻结():
    empty = triple.Vocab(vocab_id="x", vocab_version="v1", connections=())
    with pytest.raises(freeze.FreezeError):
        freeze.freeze_auto(result(t("A", "包括", "B"), vocab=empty), "v1")


def test_冻结结果带指纹():
    target = freeze.freeze_auto(result(t("记忆", "包括", "短时记忆")), "v1")
    assert len(target.fingerprint) == rules.FINGERPRINT_LEN


def test_两条路对同一组命题给出相同指纹():
    """开发期评估能迁移到运行期的前提：共用一套规则。"""
    log = adjudication.AdjudicationLog(
        batch_id="b1", vocab=VOCAB,
        items=(adjudication.Adjudication(
                   candidate=t("记忆", "包括", "短时记忆"),
                   decision=adjudication.ACCEPTED, reason=""),))
    assert freeze.freeze(log, "v1").fingerprint == \
        freeze.freeze_auto(result(t("记忆", "包括", "短时记忆")), "v1").fingerprint


def test_方向不同指纹不同_版本号不同指纹不变():
    a = freeze.freeze_auto(result(t("记忆", "包括", "短时记忆")), "v1")
    b = freeze.freeze_auto(result(t("短时记忆", "属于", "记忆")), "v1")
    assert a.fingerprint != b.fingerprint
    assert freeze.freeze_auto(
        result(t("记忆", "包括", "短时记忆")), "v2").fingerprint == a.fingerprint


def test_命题顺序不影响指纹():
    one = freeze.freeze_auto(
        result(t("记忆", "包括", "短时记忆"), t("短时记忆", "属于", "记忆")), "v1")
    two = freeze.freeze_auto(
        result(t("短时记忆", "属于", "记忆"), t("记忆", "包括", "短时记忆")), "v1")
    assert one.fingerprint == two.fingerprint


def test_差一条命题指纹就不同():
    a = freeze.freeze_auto(result(t("记忆", "包括", "短时记忆")), "v1")
    b = freeze.freeze_auto(
        result(t("记忆", "包括", "短时记忆"), t("短时记忆", "属于", "记忆")), "v1")
    assert a.fingerprint != b.fingerprint


def test_同教材不同机器抽出的图指纹相同():
    """v 号区分不了这件事，指纹才区分得了：内容一致即同批。"""
    target_a = freeze.freeze_auto(result(t("记忆", "包括", "短时记忆")), "v1")
    target_b = freeze.freeze_auto(result(t("记忆", "包括", "短时记忆")), "v9")
    assert target_a.fingerprint == target_b.fingerprint


def test_概念编号不影响指纹():
    base = freeze.freeze_auto(result(t("记忆", "包括", "短时记忆")), "v1")
    renumbered = targetmap.TargetMap(
        map_version="v1", vocab=base.vocab,
        concepts=(targetmap.Concept(concept_id="c9", label="记忆"),
                  targetmap.Concept(concept_id="c7", label="短时记忆")),
        propositions=(targetmap.Proposition(head_id="c9", connection="包括",
                                            tail_id="c7"),))
    assert rules.fingerprint(renumbered) == base.fingerprint


def test_指纹长度固定十六位():
    target = freeze.freeze_auto(result(t("记忆", "包括", "短时记忆")), "v1")
    assert len(target.fingerprint) == 16
    assert all(ch in "0123456789abcdef" for ch in target.fingerprint)


def test_去重用归一化键():
    kept = rules.ordered_propositions([(" 记忆 ", "包括", "短时记忆"),
                                       ("记忆", "包括", "短时记忆")])
    assert len(kept) == 2


def test_字面到编号取首次出现():
    concepts = (targetmap.Concept(concept_id="c1", label="记忆"),)
    assert rules.label_to_id(concepts) == {"记忆": "c1"}
