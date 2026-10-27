"""TAM 量表路由：出条目、收作答落库、按库里的作答算各构念 Cronbach α。

写侧一人一题一行，重答覆盖；读侧只从库取数，报告可随时重算。
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

import kbp.api.deps
import kbp.api.schemas_tam
import kbp.contracts.tam
import kbp.quiz.alpha
import kbp.quiz.tam_store
from kbp.quiz.scale import TAM_ITEMS

router = APIRouter(prefix="/api/tam", tags=["量表"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _item_out(item: kbp.contracts.tam.ScaleItem) -> kbp.api.schemas_tam.TamItemOut:
    return kbp.api.schemas_tam.TamItemOut(
        item_id=item.item_id, construct_code=item.construct,
        construct_label=kbp.contracts.tam.CONSTRUCT_LABELS[item.construct],
        text=item.text, optional=item.optional)


def _check(answers) -> list:
    """题号须在量表内，同一份卷子不许同题两答；返回（题号, 得分）序列。"""
    known = {i.item_id for i in TAM_ITEMS}
    unknown = sorted({a.item_id for a in answers if a.item_id not in known})
    if unknown:
        raise HTTPException(400, "未知题号: " + "、".join(unknown))
    ids = [a.item_id for a in answers]
    repeated = sorted({i for i in ids if ids.count(i) > 1})
    if repeated:
        raise HTTPException(400, "同题重复作答: " + "、".join(repeated))
    return [(a.item_id, a.score) for a in answers]


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


@router.post("/answers", response_model=kbp.api.schemas_tam.TamSavedOut)
def save_answers(body: kbp.api.schemas_tam.TamAnswersIn) -> kbp.api.schemas_tam.TamSavedOut:
    """整份量表落库；同人同题重答以最后一次为准，不追加行。"""
    scores = _check(body.answers)
    answered_at = body.answered_at or _now()
    with kbp.api.deps.db_lock():
        conn = kbp.api.deps.get_conn()
        saved = kbp.quiz.tam_store.save_all(
            conn, body.participant_id, scores, answered_at)
    return kbp.api.schemas_tam.TamSavedOut(
        participant_id=body.participant_id, saved=saved)


@router.get("/alpha", response_model=kbp.api.schemas_tam.TamAlphaOut)
def alpha() -> kbp.api.schemas_tam.TamAlphaOut:
    """按构念算 α；数来自库里全部作答，缺答的人整人剔除。"""
    conn = kbp.api.deps.get_conn()
    reports = kbp.quiz.alpha.alpha_by_construct(kbp.quiz.tam_store.rows(conn))
    return kbp.api.schemas_tam.TamAlphaOut(reports=[
        kbp.api.schemas_tam.TamAlphaReportOut(
            construct_code=r.construct,
            construct_label=kbp.contracts.tam.CONSTRUCT_LABELS[r.construct],
            k=r.k, n=r.n, alpha=r.alpha, threshold=r.threshold, passed=r.passed)
        for r in reports])
