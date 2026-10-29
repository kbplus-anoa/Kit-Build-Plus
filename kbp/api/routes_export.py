"""导出路由：按库检索被试级快照，拼成 CSV 交给前端下载，另给一份预览。"""

import csv
import io
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response

import kbp.api.deps
import kbp.api.schemas
import kbp.contracts.exportcsv
import kbp.export.csv_writer
import kbp.export.row_store
import kbp.export.subject_table

router = APIRouter(prefix="/api", tags=["导出"])


@router.get("/export/subject")
def export_subject(
        participant_id: Annotated[list[int] | None, Query()] = None,
        material_id: Annotated[list[int] | None, Query()] = None,
        time_point: Annotated[list[str] | None, Query()] = None) -> Response:
    """被试级 CSV：按被试、教材、时点筛选，空条件即全选。"""
    rows = _rows(participant_id, material_id, time_point)
    return _csv(kbp.export.csv_writer.to_csv(_payload(rows)),
                "subject_" + date.today().isoformat() + ".csv")


@router.get("/export/preview")
def preview_subject(
        participant_id: Annotated[list[int] | None, Query()] = None,
        material_id: Annotated[list[int] | None, Query()] = None,
        time_point: Annotated[list[str] | None, Query()] = None,
        limit: Annotated[int, Query(ge=1, le=50)] = 8
) -> kbp.api.schemas.ExportPreviewOut:
    """表头加前几行：同一个筛选条件，先看再下，避免下到一半才发现选错人。"""
    table = _table(_payload(_rows(participant_id, material_id, time_point)))
    return kbp.api.schemas.ExportPreviewOut(
        header=table[0], rows=table[1:limit + 1], total=len(table) - 1)


def _rows(participant_id, material_id, time_point):
    return kbp.export.row_store.subjects(
        kbp.api.deps.get_conn(), _values(participant_id), _values(material_id),
        _values(time_point))


def _values(raw):
    return tuple(raw) if raw else ()


def _payload(rows) -> kbp.contracts.exportcsv.CsvPayload:
    """没有记录就报 404；行不合法报 400，不导出半坏文件。"""
    if not rows:
        raise HTTPException(404, "没有符合条件的记录")
    try:
        return kbp.export.subject_table.build(rows)
    except Exception as exc:
        raise HTTPException(400, str(exc))


def _table(payload) -> list[list[str]]:
    """预览直接读回 CSV 文本：单元格怎么转成字，与下载文件是同一套。"""
    blob = kbp.export.csv_writer.to_csv(payload)
    return list(csv.reader(io.StringIO(blob.decode(payload.encoding))))


def _csv(blob: bytes, name: str) -> Response:
    return Response(content=blob, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition":
                             'attachment; filename="' + name + '"'})
