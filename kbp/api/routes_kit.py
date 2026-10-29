"""题库批次路由：列出教材已冻结的各批、取某一批的零件集、把某一批切回投用。

重抽入口在 /api/kit/auto 的 retry：跳过题库复用另抽一批，旧批不动。
切回只标投用，学生继续用该版本的 kit 作答，图本身不改不删。
"""

from fastapi import APIRouter, HTTPException, Query

import kbp.api.deps
import kbp.kit.bank_store
import kbp.kit.kit_service
from kbp.api.schemas import (
    ConceptOut, KitOut, KitUseIn, KitUseOut, KitVersionOut, KitVersionsOut,
    Vec2In)

router = APIRouter(prefix="/api/kit", tags=["教材"])


def _version_out(entry) -> KitVersionOut:
    target = entry.target_map
    return KitVersionOut(
        map_version=target.map_version, fingerprint=target.fingerprint,
        vocab_version=target.vocab.vocab_version, source=entry.source,
        in_use=bool(entry.in_use), created_at=entry.created_at,
        total_propositions=len(target.propositions))


def _vec(prop) -> Vec2In:
    return Vec2In(head_id=prop.head_id, connection=prop.connection,
                  tail_id=prop.tail_id)


def _kit_out(target, kit) -> KitOut:
    return KitOut(map_version=kit.map_version,
                  concepts=[ConceptOut(concept_id=c.concept_id, label=c.label)
                            for c in kit.concepts],
                  connections=list(kit.connections),
                  total_propositions=len(target.propositions),
                  propositions=[_vec(p) for p in target.propositions])


@router.get("/entry", response_model=KitOut)
def entry(material_id: int = Query(ge=1), map_version: str = Query(min_length=1)):
    """取某一批的零件集：切回旧批或预览一律走它；版本不存在返 404。"""
    try:
        target, kit = kbp.kit.kit_service.version_kit(
            kbp.api.deps.get_conn(), material_id, map_version)
    except kbp.kit.bank_store.BankError as exc:
        raise HTTPException(404, str(exc))
    return _kit_out(target, kit)


@router.get("/versions", response_model=KitVersionsOut)
def versions(material_id: int = Query(ge=1), vocab_version: str = ""):
    """该教材的全部批次，按入库先后；重抽出的新批排在旧批之后。"""
    entries = kbp.kit.kit_service.history(
        kbp.api.deps.get_conn(), material_id, vocab_version)
    return KitVersionsOut(material_id=material_id,
                          versions=[_version_out(e) for e in entries])


@router.post("/use", response_model=KitUseOut)
def use(body: KitUseIn) -> KitUseOut:
    """切回某一批：标记投用；版本不存在返 404，已投用的版本可再标一次。"""
    with kbp.api.deps.db_lock():
        try:
            entry = kbp.kit.kit_service.use(
                kbp.api.deps.get_conn(), body.material_id, body.map_version)
        except kbp.kit.bank_store.BankError as exc:
            raise HTTPException(404, str(exc))
    return KitUseOut(material_id=body.material_id,
                     map_version=entry.target_map.map_version,
                     in_use=bool(entry.in_use))
