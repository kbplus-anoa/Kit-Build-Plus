"""历史提交与草稿：从库里重算报告，供刷新、换设备、重开复盘。

评分不进库，每次按目标图重算；目标图取不到时只回原图，标成未评分。
"""

import kbp.api.deps
import kbp.contracts.report
import kbp.contracts.submission
import kbp.kit.bank_store
import kbp.kit.kit_service
import kbp.kit.split
import kbp.rebuild.draft_store
import kbp.score.score_service
from kbp.api.schemas import (ConceptOut, CurrentDraftIn, DraftOut, ErrorOut,
                             RecordOut, Vec2In)


def kit_for(conn, material_id: int, map_version: str, batch_id: str = ""):
    """先按版本号查题库；题库里没有才回到人工裁定批次。"""
    entry = kbp.kit.bank_store.by_version(conn, material_id, map_version)
    if entry is not None:
        return entry.target_map, kbp.kit.split.split(entry.target_map)
    target = kbp.kit.kit_service.freeze_batch(conn, batch_id, map_version)
    return target, kbp.kit.split.split(target)


def score_detail(result) -> dict:
    """四类错误按类别计数，错误链原样带出，报告页直接渲染。"""
    counts = {kind: 0 for kind in kbp.contracts.report.ERROR_KINDS}
    for err in result.errors:
        counts[err.kind] = counts.get(err.kind, 0) + 1
    return dict(
        total_propositions=result.total_propositions,
        correct_propositions=result.correct_propositions,
        **counts,
        errors=[ErrorOut(kind=e.kind, head_id=e.head_id,
                         connection=e.connection, tail_id=e.tail_id)
                for e in result.errors])


def vecs(props) -> list:
    return [Vec2In(head_id=p.head_id, connection=p.connection,
                   tail_id=p.tail_id) for p in props]


def draft_out(draft) -> DraftOut:
    return DraftOut(
        map_version=draft.map_version, fingerprint=draft.fingerprint,
        mode=draft.mode, participant_id=draft.participant_id,
        material_id=draft.material_id, time_point=draft.time_point,
        submit_seq=draft.submit_seq, propositions=vecs(draft.propositions),
        saved_at=draft.saved_at)


def record_of(conn, sub) -> RecordOut:
    """按当前目标图重算这一份提交；图不在了就只回原图。"""
    head = dict(submit_seq=sub.submit_seq, material_id=sub.material_id,
                map_version=sub.map_version, mode=sub.mode,
                submitted_at=sub.submitted_at,
                propositions=vecs(sub.propositions))
    try:
        target, kit = kit_for(conn, sub.material_id, sub.map_version)
    except Exception:
        return RecordOut(fingerprint=sub.fingerprint, fms=0.0, scored=False,
                         total_propositions=0, correct_propositions=0,
                         lacking=0, excessive=0, leaving=0, reversed=0,
                         errors=[], target_propositions=[], **head)
    result = kbp.score.score_service.score(target, sub)
    return RecordOut(fingerprint=target.fingerprint,
                     fms=kbp.score.score_service.fms(result),
                     concepts=[ConceptOut(concept_id=c.concept_id, label=c.label)
                               for c in kit.concepts],
                     connections=list(kit.connections),
                     target_propositions=[Vec2In(head_id=p.head_id,
                                                 connection=p.connection,
                                                 tail_id=p.tail_id)
                                          for p in target.propositions],
                     **head, **score_detail(result))


def records_of(conn, participant_id: int,
               material_id: int | None = None) -> list:
    return [record_of(conn, sub)
            for sub in kbp.rebuild.draft_store.submissions(
                conn, participant_id, material_id)]


def drafts_of(conn, participant_id: int,
              material_id: int | None = None) -> list:
    return [draft_out(draft)
            for draft in kbp.rebuild.draft_store.drafts(
                conn, participant_id, material_id)]


def current_draft(conn, participant_id: int, material_id: int,
                  time_point: str) -> DraftOut:
    """该教材下序号最大的草稿；没有就报错。"""
    rows = [d for d in kbp.rebuild.draft_store.drafts(
        conn, participant_id, material_id) if d.time_point == time_point]
    if not rows:
        raise kbp.rebuild.draft_store.DraftError("草稿不存在")
    return draft_out(rows[-1])


def save_current(conn, body: CurrentDraftIn) -> DraftOut:
    """存成该教材的当前草稿：序号取下一个，同一份反复存只动最新的那条。"""
    target, _ = kit_for(conn, body.material_id, body.map_version,
                        body.batch_id)
    seq = kbp.rebuild.draft_store.next_seq(
        conn, body.participant_id, body.material_id, body.time_point)
    draft = kbp.contracts.submission.Draft(
        map_version=body.map_version, fingerprint=target.fingerprint,
        mode=body.mode, propositions=tuple(
            kbp.contracts.submission.SubmittedProposition(
                head_id=p.head_id, connection=p.connection, tail_id=p.tail_id)
            for p in body.propositions),
        participant_id=body.participant_id, material_id=body.material_id,
        time_point=body.time_point, submit_seq=seq, saved_at=_now())
    kbp.rebuild.draft_store.save(conn, draft)
    return draft_out(draft)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
