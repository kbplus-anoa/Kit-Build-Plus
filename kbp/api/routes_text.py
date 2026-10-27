"""教材侧路由：收上传、读原文、抽取候选、运行期自动裁 kit。"""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

import kbp.api.deps
import kbp.api.kit_flow
import kbp.api.upload_flow
import kbp.extract.chat_client
import kbp.extract.extract_service
import kbp.ingest.ingest_service
import kbp.ingest.materials
import kbp.ingest.ocr
import kbp.ingest.uploads
import kbp.kit.bank_store
import kbp.kit.freeze
import kbp.kit.lock
from kbp.api.schemas import (
    ExtractIn, ExtractOut, IngestIn, IngestOut, JobOut, KitAutoIn, KitAutoOut,
    MaterialOut, MaterialsOut, MaterialTextOut, PreviewIn, PreviewOut,
    TripleOut, UploadOut)

router = APIRouter(prefix="/api", tags=["教材"])


@router.post("/ingest", response_model=IngestOut)
def ingest(body: IngestIn) -> IngestOut:
    """把本地文件读成纯文本。扫描件会自动走 MinerU 云。"""
    try:
        doc = kbp.ingest.ingest_service.ingest(body.path)
    except FileNotFoundError:
        raise HTTPException(404, "文件不存在: " + body.path)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except kbp.ingest.ocr.MinerUUnavailable as exc:
        raise HTTPException(503, "扫描件需要云端解析，云端不可用: " + str(exc))
    except Exception as exc:
        raise HTTPException(502, "解析失败: " + str(exc))
    return IngestOut(file_name=doc.file_name, source=doc.source,
                     has_ocr=doc.has_ocr, page_count=doc.page_count,
                     chars=len(doc.text))


@router.post("/upload", response_model=UploadOut)
async def upload(file: UploadFile = File(...)) -> UploadOut:
    """收浏览器上传的文件：落盘、解析成正文、登记成一份教材。"""
    name = Path(file.filename or "").name or "未命名"
    ext = kbp.api.upload_flow.ext_of(name)
    data = await file.read()
    if not data:
        raise HTTPException(400, "文件是空的")
    if len(data) > kbp.ingest.uploads.MAX_BYTES:
        raise HTTPException(413, "文件太大，上限 40 MB")
    path, digest = kbp.ingest.uploads.save(data, name)
    doc = kbp.api.upload_flow.ingest(path, name)
    conn = kbp.api.deps.get_conn()
    with kbp.api.deps.db_lock():
        material_id = kbp.ingest.materials.add_or_get(
            conn, name, ext, doc.source, len(doc.text), digest,
            kbp.api.upload_flow.now(), path=str(path))
    return UploadOut(material_id=material_id, file_name=name, ext=ext,
                     source=doc.source, chars=len(doc.text),
                     has_ocr=doc.has_ocr, page_count=doc.page_count,
                     text=doc.text)


@router.delete("/materials/{material_id}")
def remove_material(material_id: int) -> dict:
    """删掉一份教材与它的原文；上传失败回滚时前端调这里。"""
    conn = kbp.api.deps.get_conn()
    with kbp.api.deps.db_lock():
        row = kbp.ingest.materials.remove(conn, material_id)
    if row is None:
        raise HTTPException(404, "教材不存在: " + str(material_id))
    if row[6]:
        kbp.ingest.uploads.drop(Path(row[6]))
    return {"ok": True}


@router.get("/materials", response_model=MaterialsOut)
def materials(limit: int = 200) -> MaterialsOut:
    """上传过的教材，新的在前；只列已经抽出 kit 的。"""
    rows = kbp.ingest.materials.list_all(kbp.api.deps.get_conn(), limit)
    return MaterialsOut(items=[
        MaterialOut(material_id=r[0], file_name=r[1], ext=r[2], chars=r[4],
                    created_at=r[5]) for r in rows])


@router.get("/materials/{material_id}/text", response_model=MaterialTextOut)
def material_text(material_id: int) -> MaterialTextOut:
    """重读一份旧教材的正文：命中解析缓存，不重复上传也不重复花算力。"""
    row = kbp.ingest.materials.get(kbp.api.deps.get_conn(), material_id)
    if row is None:
        raise HTTPException(404, "教材不存在: " + str(material_id))
    path = Path(row[6] or "")
    if not row[6] or not path.is_file():
        raise HTTPException(404, "这份教材的原文不在了，请重新上传")
    doc = kbp.api.upload_flow.ingest(path, row[1], keep=True)
    return MaterialTextOut(material_id=int(row[0]), file_name=row[1],
                           ext=row[2], chars=len(doc.text), text=doc.text)


@router.post("/extract", response_model=ExtractOut)
def extract(body: ExtractIn) -> ExtractOut:
    """从纯文本抽候选三元组，全部落在词表内。"""
    vocab = kbp.api.kit_flow.to_vocab(body.vocab)
    try:
        result = kbp.extract.extract_service.extract(
            body.text, vocab, kbp.api.kit_flow.load_config())
    except kbp.extract.extract_service.ExtractError as exc:
        raise HTTPException(400, str(exc))
    except kbp.extract.chat_client.MissingKey as exc:
        raise HTTPException(503, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(503, "抽取不可用: " + str(exc))
    return ExtractOut(
        vocab_id=result.vocab.vocab_id,
        vocab_version=result.vocab.vocab_version,
        count=len(result.triples),
        triples=[TripleOut(head=t.head, connection=t.connection,
                           tail=t.tail, confidence=t.confidence,
                           evidence=t.evidence, suspect=t.suspect)
                 for t in result.triples])


@router.post("/kit/preview", response_model=PreviewOut)
def kit_preview(body: PreviewIn) -> PreviewOut:
    """抽之前先回段数：前端据此显示真实进度，而不是干等。"""
    segments, chars = kbp.api.kit_flow.preview(body.text)
    return PreviewOut(segments=segments, chars=chars)


@router.post("/kit/auto", response_model=KitAutoOut)
def kit_auto(body: KitAutoIn) -> KitAutoOut:
    """同步裁 kit：先查题库，命中即复用；未命中或要求重抽才抽取。"""
    try:
        return kbp.api.kit_flow.auto(body)
    except kbp.extract.extract_service.ExtractError as exc:
        raise HTTPException(400, str(exc))
    except kbp.extract.chat_client.MissingKey as exc:
        raise HTTPException(503, str(exc))
    except kbp.kit.freeze.FreezeError as exc:
        raise HTTPException(422, "抽出的图不足以成题: " + str(exc))
    except kbp.kit.bank_store.BankError as exc:
        raise HTTPException(409, "题库拒绝登记: " + str(exc))
    except kbp.kit.lock.LockError as exc:
        raise HTTPException(409, str(exc))
    except Exception as exc:
        raise HTTPException(503, "自动裁 kit 不可用: " + str(exc))


@router.post("/kit/jobs", response_model=JobOut)
def kit_job_start(body: KitAutoIn) -> JobOut:
    """开一个后台裁 kit 任务：前端轮询进度，抽完取结果。"""
    return JobOut(**kbp.api.kit_flow.start(body))


@router.get("/kit/jobs/{job_id}", response_model=JobOut)
def kit_job(job_id: str) -> JobOut:
    """查任务进度；done 时 result 即裁好的 kit。"""
    snap = kbp.api.kit_flow.status(job_id)
    if snap is None:
        raise HTTPException(404, "任务不存在或已过期: " + job_id)
    return JobOut(**snap)
