"""历史与草稿路由：刷新或换设备后，做过的记录要能找回来。

记录只认库，不认浏览器；分数每次按目标图重算。
"""

from fastapi import APIRouter, HTTPException

import kbp.api.deps
import kbp.api.record_flow
import kbp.kit.bank_store
import kbp.rebuild.draft_store
from kbp.api.schemas import (CurrentDraftIn, DraftOut, DraftsOut, RecordsOut)

router = APIRouter(prefix="/api", tags=["记录"])


@router.get("/records", response_model=RecordsOut)
def list_records(participant_id: int,
                 material_id: int | None = None) -> RecordsOut:
    """列出某人的提交，新的在后；每份按当前目标图重算。"""
    conn = kbp.api.deps.get_conn()
    return RecordsOut(items=kbp.api.record_flow.records_of(
        conn, participant_id, material_id))


@router.get("/drafts", response_model=DraftsOut)
def list_drafts(participant_id: int,
                material_id: int | None = None) -> DraftsOut:
    """列出某人的草稿，供「继续」栏直接用。"""
    conn = kbp.api.deps.get_conn()
    return DraftsOut(items=kbp.api.record_flow.drafts_of(
        conn, participant_id, material_id))


@router.get("/draft/current", response_model=DraftOut)
def read_current(participant_id: int, material_id: int,
                 time_point: str) -> DraftOut:
    """读该教材当前草稿；没保存过就 404。"""
    try:
        return kbp.api.record_flow.current_draft(
            kbp.api.deps.get_conn(), participant_id, material_id, time_point)
    except kbp.rebuild.draft_store.DraftError as exc:
        raise HTTPException(404, str(exc))


@router.post("/draft/current", response_model=DraftOut)
def write_current(body: CurrentDraftIn) -> DraftOut:
    """保存该教材当前草稿；序号由服务端分配。"""
    with kbp.api.deps.db_lock():
        try:
            return kbp.api.record_flow.save_current(
                kbp.api.deps.get_conn(), body)
        except kbp.kit.bank_store.BankError as exc:
            raise HTTPException(404, str(exc))
        except kbp.rebuild.draft_store.DraftError as exc:
            raise HTTPException(409, str(exc))
        except Exception as exc:
            raise HTTPException(400, str(exc))
