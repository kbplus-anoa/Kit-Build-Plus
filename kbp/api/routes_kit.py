"""题库批次路由：列出教材已冻结的各批、把某一批切回投用。

重抽入口在 /api/kit/auto 的 retry：跳过题库复用另抽一批，旧批不动。
切回只标投用，学生继续用该版本的 kit 作答，图本身不改不删。
"""

from fastapi import APIRouter, HTTPException, Query

import kbp.api.deps
import kbp.api.schemas_kit
import kbp.kit.bank_store
import kbp.kit.kit_service

router = APIRouter(prefix="/api/kit", tags=["教材"])


def _version_out(entry) -> kbp.api.schemas_kit.KitVersionOut:
    target = entry.target_map
    return kbp.api.schemas_kit.KitVersionOut(
        map_version=target.map_version, fingerprint=target.fingerprint,
        vocab_version=target.vocab.vocab_version, source=entry.source,
        in_use=bool(entry.in_use), created_at=entry.created_at,
        total_propositions=len(target.propositions))


@router.get("/versions", response_model=kbp.api.schemas_kit.KitVersionsOut)
def versions(material_id: int = Query(ge=1), vocab_version: str = ""):
    """该教材的全部批次，按入库先后；重抽出的新批排在旧批之后。"""
    entries = kbp.kit.kit_service.history(
        kbp.api.deps.get_conn(), material_id, vocab_version)
    return kbp.api.schemas_kit.KitVersionsOut(
        material_id=material_id,
        versions=[_version_out(e) for e in entries])


@router.post("/use", response_model=kbp.api.schemas_kit.KitUseOut)
def use(body: kbp.api.schemas_kit.KitUseIn) -> kbp.api.schemas_kit.KitUseOut:
    """切回某一批：标记投用；版本不存在返 404，已投用的版本可再标一次。"""
    with kbp.api.deps.db_lock():
        try:
            entry = kbp.kit.kit_service.use(
                kbp.api.deps.get_conn(), body.material_id, body.map_version)
        except kbp.kit.bank_store.BankError as exc:
            raise HTTPException(404, str(exc))
    return kbp.api.schemas_kit.KitUseOut(
        material_id=body.material_id, map_version=entry.target_map.map_version,
        in_use=bool(entry.in_use))
