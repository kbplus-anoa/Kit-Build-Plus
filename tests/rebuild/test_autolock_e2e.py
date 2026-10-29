"""跨 feature 的端到端验证：裁定 → 冻结 → 拆 kit → 提交 → 版本自动锁定。

kit 与 rebuild 互不 import；本用例扮演装配层，自己把两边的表建进同一个库。
"""

import kbp.contracts.adjudication as adjudication  # noqa: E402
import kbp.rebuild.draft_store as ds  # noqa: E402
import kbp.kit.freeze as freeze  # noqa: E402
import kbp.kit.kit_service as kit_service  # noqa: E402
import kbp.kit.lock as lock  # noqa: E402
import kbp.rebuild.rebuild_service as svc  # noqa: E402
import kbp.kit.split as split  # noqa: E402
import kbp.kit.store as kit_store  # noqa: E402
import kbp.contracts.submission as submission  # noqa: E402
import kbp.contracts.triple as triple  # noqa: E402
import kbp.rebuild.usage as usage  # noqa: E402


def cand(head, conn, tail):
    return triple.TripleCandidate(head=head, connection=conn, tail=tail,
                                  confidence=0.9)


def make_log():
    v = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("包括", "属于"))
    items = (
        adjudication.Adjudication(candidate=cand("记忆", "包括", "短时记忆"),
                                  decision=adjudication.ACCEPTED, reason=""),
        adjudication.Adjudication(candidate=cand("容量", "包括", "长度"),
                                  decision=adjudication.REJECTED,
                                  reason="教材未提及"),
    )
    return adjudication.AdjudicationLog(batch_id="b1", vocab=v, items=items)


def shared_conn():
    """装配层职责：一个库里同时容纳 kit 与 rebuild 的表。"""
    conn = ds.connect(":memory:")
    kit_store.ensure(conn)
    return conn


def make_sub(kit, seq=1, mode=submission.TEST):
    ids = [c.concept_id for c in kit.concepts]
    return submission.Submission(
        map_version="v1", fingerprint="fp1", mode=mode,
        propositions=(submission.SubmittedProposition(
            head_id=ids[0], connection="包括", tail_id=ids[1]),),
        started_at="", submitted_at="2026-10-25T10:00:00",
        participant_id=1, material_id=1, time_point=submission.POST,
        submit_seq=seq)


def test_提交后版本自动锁定():
    conn = shared_conn()
    port = usage.SubmissionUsage(conn, 1)
    kit = split.split(freeze.freeze(make_log(), "v1"))
    lock.assert_mutable("v1", port)
    svc.submit(conn, kit, make_sub(kit))
    assert port.is_used("v1") is True
    assert lock.lock_state("v1", port) == "locked"
    conn.close()


def test_驳回项不进_kit_但留档():
    conn = shared_conn()
    kit_service.adjudicate(conn, make_log())
    kit = kit_service.build_kit(conn, "b1", "v1")
    assert "容量" not in [c.label for c in kit.concepts]
    assert len(kit_service.load_batch(conn, "b1").items) == 2
    conn.close()


def test_同一四元键重复提交被拒():
    conn = shared_conn()
    kit = split.split(freeze.freeze(make_log(), "v1"))
    sub = make_sub(kit)
    svc.submit(conn, kit, sub)
    try:
        svc.submit(conn, kit, sub)
        dup = False
    except Exception:
        dup = True
    assert dup is True
    conn.close()
