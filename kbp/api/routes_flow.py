"""流程路由：裁定 → 冻结 → 拆 kit → 提交 → 评分。

所有落库写操作都持同一把锁：SQLite 连接跨线程共享。
"""

from fastapi import APIRouter, HTTPException


import kbp.contracts.adjudication
import kbp.contracts.report
import kbp.contracts.submission
import kbp.api.deps
import kbp.export.row_build
import kbp.export.row_store
import kbp.kit.bank_store
import kbp.kit.kit_service
import kbp.kit.lock
import kbp.rebuild.rebuild_service
import kbp.score.score_service
import kbp.kit.split
import kbp.kit.store
import kbp.contracts.submission
import kbp.contracts.triple
import kbp.api.record_flow
import kbp.rebuild.draft_store
import kbp.rebuild.usage
from kbp.api.schemas import (
    BatchIn, BatchOut, BuildKitIn, ConceptOut, DraftIn, DraftOut,
    KitOut, ReadyOut, SubmitIn, SubmitOut, Vec2In)

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


@router.post("/draft", response_model=DraftOut)
def save_draft(body: DraftIn) -> DraftOut:
    """保存草稿：按 kit 白名单校验，作答期随时可改，关联键同提交。"""
    conn = kbp.api.deps.get_conn()
    with kbp.api.deps.db_lock():
        try:
            target, kit = kbp.api.record_flow.kit_for(
                conn, body.material_id, body.map_version, body.batch_id)
            draft = _draft(body, target.fingerprint)
            kbp.rebuild.rebuild_service.save_draft(conn, kit, draft)
        except kbp.kit.bank_store.BankError as exc:
            raise HTTPException(404, str(exc))
        except Exception as exc:
            raise HTTPException(400, str(exc))
    return kbp.api.record_flow.draft_out(draft)


@router.get("/draft", response_model=DraftOut)
def load_draft(participant_id: int, material_id: int, time_point: str,
               submit_seq: int) -> DraftOut:
    """读回该四元键的草稿；没有就 404。"""
    try:
        draft = kbp.rebuild.rebuild_service.load_draft(
            kbp.api.deps.get_conn(), participant_id, material_id, time_point,
            submit_seq)
    except kbp.rebuild.draft_store.DraftError as exc:
        raise HTTPException(404, str(exc))
    return kbp.api.record_flow.draft_out(draft)


@router.post("/submit")
def submit(body: SubmitIn) -> SubmitOut:
    """提交并立即评分。服务端分配提交序号，学习模式多次提交各自成行。"""
    conn = kbp.api.deps.get_conn()
    try:
        target, kit = kbp.api.record_flow.kit_for(
            conn, body.material_id, body.map_version, body.batch_id)
    except Exception as exc:
        raise HTTPException(404, "批次不可用: " + str(exc))
    with kbp.api.deps.db_lock():
        seq = _assign_seq(conn, body)
        sub = _submission(body, target.fingerprint, seq)
        try:
            kbp.rebuild.rebuild_service.submit(conn, kit, sub)
        except Exception as exc:
            raise HTTPException(400, str(exc))
        result = kbp.score.score_service.score(target, sub)
        kbp.export.row_store.save_subject(
            conn, kbp.export.row_build.subject_row(
                sub, result, condition=body.condition,
                is_practice=body.is_practice,
                possibly_inaccurate=body.possibly_inaccurate,
                signals=(body.signal_isolated, body.signal_coverage,
                         body.signal_concentration, body.signal_baseline)))
    return SubmitOut(submit_seq=seq, fingerprint=target.fingerprint,
                     fms=kbp.score.score_service.fms(result),
                     target_propositions=[
                         Vec2In(head_id=p.head_id, connection=p.connection,
                                tail_id=p.tail_id)
                         for p in target.propositions],
                     **kbp.api.record_flow.score_detail(result))


def _assign_seq(conn, body: SubmitIn) -> int:
    """测验模式只允许一次；学习模式每次提交取下一个序号。"""
    used = kbp.rebuild.draft_store.counts(
        conn, body.participant_id, body.material_id, body.time_point,
        kbp.contracts.submission.TEST)
    if body.mode == kbp.contracts.submission.TEST and used:
        raise HTTPException(409, "测验模式已提交，不可重复提交")
    return kbp.rebuild.draft_store.next_seq(
        conn, body.participant_id, body.material_id, body.time_point)


def _submission(body: SubmitIn, fingerprint: str, seq: int):
    return kbp.contracts.submission.Submission(
        map_version=body.map_version, fingerprint=fingerprint, mode=body.mode,
        propositions=tuple(kbp.contracts.submission.SubmittedProposition(
            head_id=p.head_id, connection=p.connection, tail_id=p.tail_id)
            for p in body.propositions),
        started_at="", submitted_at=_now(),
        participant_id=body.participant_id, material_id=body.material_id,
        time_point=body.time_point, submit_seq=seq)


def _draft(body: DraftIn, fingerprint: str):
    return kbp.contracts.submission.Draft(
        map_version=body.map_version, fingerprint=fingerprint, mode=body.mode,
        propositions=tuple(kbp.contracts.submission.SubmittedProposition(
            head_id=p.head_id, connection=p.connection, tail_id=p.tail_id)
            for p in body.propositions),
        participant_id=body.participant_id, material_id=body.material_id,
        time_point=body.time_point, submit_seq=body.submit_seq,
        saved_at=_now())


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
