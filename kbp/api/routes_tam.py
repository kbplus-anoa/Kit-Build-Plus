"""TAM 量表路由：出条目、算各构念 Cronbach α。

本层只算不存：作答落库等做题表（见 TODO「夹具与记录落库」）。
"""

from fastapi import APIRouter, HTTPException

import kbp.api.schemas_tam
import kbp.contracts.tam
import kbp.quiz.alpha
from kbp.quiz.scale import TAM_ITEMS

router = APIRouter(prefix="/api/tam", tags=["量表"])


def _item_out(item: kbp.contracts.tam.ScaleItem) -> kbp.api.schemas_tam.TamItemOut:
    return kbp.api.schemas_tam.TamItemOut(
        item_id=item.item_id, construct_code=item.construct,
        construct_label=kbp.contracts.tam.CONSTRUCT_LABELS[item.construct],
        text=item.text, optional=item.optional)


@router.get("/items", response_model=kbp.api.schemas_tam.TamItemsOut)
def items() -> kbp.api.schemas_tam.TamItemsOut:
    """量表条目：六点 Likert、判据、构念中文名、哪些题可选。"""
    return kbp.api.schemas_tam.TamItemsOut(
        likert_min=kbp.contracts.tam.LIKERT_MIN,
        likert_max=kbp.contracts.tam.LIKERT_MAX,
        min_alpha=kbp.contracts.tam.MIN_ALPHA,
        constructs=[kbp.api.schemas_tam.TamConstructOut(
            code=c, label=kbp.contracts.tam.CONSTRUCT_LABELS[c])
            for c in kbp.contracts.tam.CONSTRUCTS],
        items=[_item_out(i) for i in TAM_ITEMS])


@router.post("/alpha", response_model=kbp.api.schemas_tam.TamAlphaOut)
def alpha(body: kbp.api.schemas_tam.TamAlphaIn) -> kbp.api.schemas_tam.TamAlphaOut:
    """按构念算 α；题号须在量表内，缺答的人整人剔除。"""
    known = {i.item_id for i in TAM_ITEMS}
    unknown = sorted({r.item_id for r in body.rows if r.item_id not in known})
    if unknown:
        raise HTTPException(400, "未知题号: " + "、".join(unknown))
    rows = [(r.participant_id, r.item_id, r.score) for r in body.rows]
    reports = kbp.quiz.alpha.alpha_by_construct(rows)
    return kbp.api.schemas_tam.TamAlphaOut(reports=[
        kbp.api.schemas_tam.TamAlphaReportOut(
            construct_code=r.construct,
            construct_label=kbp.contracts.tam.CONSTRUCT_LABELS[r.construct],
            k=r.k, n=r.n, alpha=r.alpha, threshold=r.threshold, passed=r.passed)
        for r in reports])
