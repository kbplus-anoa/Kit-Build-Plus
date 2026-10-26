"""流程路由：裁定 → 冻结 → 拆 kit → 提交 → 评分。

所有落库写操作都持同一把锁：SQLite 连接跨线程共享。
"""

from fastapi import APIRouter, HTTPException


import kbp.contracts.adjudication
import kbp.api.deps
import kbp.kit.kit_service
import kbp.kit.lock
import kbp.rebuild.rebuild_service
import kbp.score.score_service
import kbp.kit.split
import kbp.kit.store
import kbp.contracts.submission
import kbp.contracts.triple
import kbp.rebuild.usage
from kbp.api.schemas import (
    BatchIn, BatchOut, BuildKitIn, ConceptOut, ErrorOut, KitOut, ReadyOut,
    ScoreOut, SubmitIn)

router = APIRouter(prefix="/api", tags=["流程"])


def _vocab(v) -> kbp.contracts.triple.Vocab:
    return kbp.contracts.triple.Vocab(vocab_id=v.vocab_id, vocab_version=v.version,
                                      connections=tuple(v.connections))


def _candidate(item) -> kbp.contracts.triple.TripleCandidate:
    return kbp.contracts.triple.TripleCandidate(head=item.head, connection=item.connection,
                                                tail=item.tail, confidence=item.confidence)


@router.post("/adjudicate", response_model=BatchOut)
def adjudicate(body: BatchIn) -> BatchOut:
    """保存整批裁定；驳回项与接受项一并留档。"""
    items = tuple(kbp.contracts.adjudication.Adjudication(
        candidate=_candidate(i), decision=i.decision, reason=i.reason)
        for i in body.items)
    log = kbp.contracts.adjudication.AdjudicationLog(batch_id=body.batch_id,
                                                     vocab=_vocab(body.vocab), items=items)
    with kbp.api.deps.db_lock():
        try:
            saved = kbp.kit.kit_service.adjudicate(kbp.api.deps.get_conn(), log)
        except kbp.kit.store.StoreError as exc:
            raise HTTPException(409, str(exc))
    return BatchOut(batch_id=body.batch_id, saved=saved)


@router.post("/kit", response_model=KitOut)
def build_kit(body: BuildKitIn) -> KitOut:
    """冻结目标图并拆 kit，返回学生可见零件。"""
    conn = kbp.api.deps.get_conn()
    try:
        target = kbp.kit.kit_service.freeze_batch(conn, body.batch_id, body.map_version)
        kit = kbp.kit.split.split(target)
    except Exception as exc:
        raise HTTPException(404, "批次或词表不可用: " + str(exc))
    return KitOut(map_version=kit.map_version,
                  concepts=[ConceptOut(concept_id=c.concept_id, label=c.label)
                            for c in kit.concepts],
                  connections=list(kit.connections),
                  total_propositions=len(target.propositions))


@router.get("/lock", response_model=ReadyOut)
def lock_state(map_version: str) -> ReadyOut:
    """查该版本是否已被学生用过（用过即不可改）。"""
    port = kbp.rebuild.usage.SubmissionUsage(kbp.api.deps.get_conn())
    return ReadyOut(map_version=map_version,
                    locked=kbp.kit.lock.lock_state(map_version, port))


@router.post("/submit", response_model=ScoreOut)
def submit(body: SubmitIn) -> ScoreOut:
    """提交并立即评分。rebuild 本身不评分，评分由 score 做。"""
    conn = kbp.api.deps.get_conn()
    try:
        target = kbp.kit.kit_service.freeze_batch(conn, body.batch_id, body.map_version)
        kit = kbp.kit.split.split(target)
    except Exception as exc:
        raise HTTPException(404, "批次不可用: " + str(exc))
    sub = kbp.contracts.submission.Submission(
        map_version=body.map_version, mode=body.mode,
        propositions=tuple(kbp.contracts.submission.SubmittedProposition(
            head_id=p.head_id, connection=p.connection, tail_id=p.tail_id)
            for p in body.propositions),
        started_at="", submitted_at=_now(),
        participant_id=body.participant_id, material_id=body.material_id,
        session=body.session)
    with kbp.api.deps.db_lock():
        try:
            kbp.rebuild.rebuild_service.submit(conn, kit, sub)
        except Exception as exc:
            raise HTTPException(400, str(exc))
    result = kbp.score.score_service.score(target, sub)
    summary = kbp.score.score_service.summary(result)
    return ScoreOut(
        total_propositions=result.total_propositions,
        correct_propositions=result.correct_propositions,
        score=summary["score"], lacking=summary["lacking"],
        excessive=summary["excessive"], leaving=summary["leaving"],
        reversed=summary["reversed"],
        errors=[ErrorOut(kind=e.kind, head_id=e.head_id,
                         connection=e.connection, tail_id=e.tail_id)
                for e in result.errors])


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
