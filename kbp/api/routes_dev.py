"""开发者模式的落库入口：读这一批改后的样子、整份改写、撤销改写。

改的是这一批在界面上长什么样，冻结图与指纹不动；撤销只是删掉改写行。
密码在服务端再验一次：前端那道门只是顺手，真正的门在这里。
"""

from fastapi import APIRouter, HTTPException, Query

import kbp.api.deps
import kbp.api.dev_gate
import kbp.api.kit_flow
import kbp.api.routes_kit
import kbp.contracts.targetmap
import kbp.kit.bank_store
import kbp.kit.dev_overlay
import kbp.kit.kit_service
import kbp.kit.split
from kbp.api.schemas import DevKitIn, DevKitOut

router = APIRouter(prefix="/api/dev", tags=["开发者模式"])


def _now() -> str:
    return kbp.api.kit_flow.now()


def _entry(conn, material_id: int, map_version: str):
    entry = kbp.kit.bank_store.by_version(conn, material_id, map_version)
    if entry is None:
        raise HTTPException(404, "版本不存在: " + map_version)
    return entry


def _payload(conn, entry, overlay) -> DevKitOut:
    try:
        target, kit = kbp.kit.kit_service.target_kit(conn, entry)
    except kbp.kit.split.SplitError as exc:
        raise HTTPException(400, str(exc))
    base = kbp.api.routes_kit._kit_out(target, kit)
    return DevKitOut(**base.model_dump(), edited=overlay is not None,
                     updated_at=overlay.updated_at if overlay else "")


def _overlay_of(body: DevKitIn) -> kbp.kit.dev_overlay.Overlay:
    return kbp.kit.dev_overlay.Overlay(
        concepts=tuple(kbp.contracts.targetmap.Concept(concept_id=c.concept_id,
                                                       label=c.label)
                       for c in body.concepts),
        connections=tuple(body.connections),
        propositions=tuple(
            kbp.contracts.targetmap.Proposition(head_id=p.head_id,
                                                connection=p.connection,
                                                tail_id=p.tail_id)
            for p in body.propositions))


@router.get("/kit", response_model=DevKitOut)
def read(material_id: int = Query(ge=1),
         map_version: str = Query(min_length=1)) -> DevKitOut:
    """这一批当前的样子：改过就是改后的，没改过就是冻结图原样。"""
    conn = kbp.api.deps.get_conn()
    entry = _entry(conn, material_id, map_version)
    overlay = kbp.kit.dev_overlay.load(conn, material_id, map_version)
    return _payload(conn, entry, overlay)


@router.put("/kit", response_model=DevKitOut)
def write(body: DevKitIn) -> DevKitOut:
    """整份改写这一批的概念、连接词与目标命题；密码不对 403，图不成立 400。"""
    try:
        kbp.api.dev_gate.assert_open(body.password)
    except kbp.api.dev_gate.GateError as exc:
        raise HTTPException(403, str(exc))
    with kbp.api.deps.db_lock():
        conn = kbp.api.deps.get_conn()
        entry = _entry(conn, body.material_id, body.map_version)
        try:
            overlay = kbp.kit.dev_overlay.save(conn, body.material_id,
                                               body.map_version,
                                               _overlay_of(body), _now())
        except kbp.kit.dev_overlay.OverlayError as exc:
            raise HTTPException(400, str(exc))
        return _payload(conn, entry, overlay)


@router.delete("/kit", response_model=DevKitOut)
def reset(body: DevKitIn) -> DevKitOut:
    """撤销这一批的改写，回到冻结图原样；本来没改过也不报错。"""
    try:
        kbp.api.dev_gate.assert_open(body.password)
    except kbp.api.dev_gate.GateError as exc:
        raise HTTPException(403, str(exc))
    with kbp.api.deps.db_lock():
        conn = kbp.api.deps.get_conn()
        entry = _entry(conn, body.material_id, body.map_version)
        kbp.kit.dev_overlay.drop(conn, body.material_id, body.map_version)
        return _payload(conn, entry, None)
