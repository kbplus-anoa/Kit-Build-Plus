"""教材侧路由：收上传、读原文、抽取候选、运行期自动裁 kit。"""

import dataclasses
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile


import kbp.api.config_store
import kbp.api.deps
import kbp.contracts.extractconfig
import kbp.contracts.triple
import kbp.extract.chat_client
import kbp.extract.discard_store
import kbp.extract.extract_service
import kbp.extract.quality
import kbp.extract.record_store
import kbp.extract.threshold_store
import kbp.ingest.ingest_service
import kbp.ingest.materials
import kbp.ingest.ocr
import kbp.ingest.uploads
import kbp.kit.bank_store
import kbp.kit.kit_service
import kbp.kit.lock
import kbp.rebuild.usage
from kbp.api.schemas import (
    ConceptOut, ExtractIn, ExtractOut, IngestIn, IngestOut, KitAutoIn, KitAutoOut,
    MaterialOut, MaterialsOut, MaterialTextOut, MAX_TEXT, SignalOut, TripleOut,
    UploadOut)

router = APIRouter(prefix="/api", tags=["教材"])


def _to_vocab(v) -> kbp.contracts.triple.Vocab:
    return kbp.contracts.triple.Vocab(vocab_id=v.vocab_id, vocab_version=v.version,
                                      connections=tuple(v.connections))


def _config() -> kbp.contracts.extractconfig.ExtractConfig:
    """读已保存的配置；没保存过时是空配置，抽取会提示先填模型与地址。"""
    import kbp.api.deps
    return kbp.api.config_store.load_config(kbp.api.deps.get_conn())


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


def _upload_ext(name: str) -> str:
    ext = kbp.ingest.uploads.ext_of(name)
    if ext not in kbp.ingest.uploads.ALLOWED:
        raise HTTPException(
            400, "这个格式暂不支持：「" + (ext or "未知") + "」。"
                 "请上传 PDF、EPUB 或 TXT 文件。")
    return ext


def _ingest_upload(path: Path, name: str, keep: bool = False):
    """解析上传的文件；新上传失败时删掉落盘文件，别留半个教材。

    keep 为重读旧教材用：解析失败也不能删它，那是别的教材的原文。
    """
    drop = (lambda: None) if keep else (lambda: kbp.ingest.uploads.drop(path))
    try:
        doc = kbp.ingest.ingest_service.ingest(str(path))
    except kbp.ingest.ocr.MinerUUnavailable as exc:
        drop()
        raise HTTPException(503, "扫描件需要云端解析，云端不可用: " + str(exc))
    except Exception as exc:
        drop()
        raise HTTPException(502, "解析失败: " + str(exc))
    if not doc.text.strip():
        drop()
        raise HTTPException(400, "这个文件里没有可用的文字")
    if len(doc.text) > MAX_TEXT:
        raise HTTPException(413, "正文太长，上限 200 万字")
    return dataclasses.replace(doc, file_name=name)


@router.post("/upload", response_model=UploadOut)
async def upload(file: UploadFile = File(...)) -> UploadOut:
    """收浏览器上传的文件：落盘、解析成正文、登记成一份教材。"""
    name = Path(file.filename or "").name or "未命名"
    ext = _upload_ext(name)
    data = await file.read()
    if not data:
        raise HTTPException(400, "文件是空的")
    if len(data) > kbp.ingest.uploads.MAX_BYTES:
        raise HTTPException(413, "文件太大，上限 40 MB")
    path, digest = kbp.ingest.uploads.save(data, name)
    doc = _ingest_upload(path, name)
    conn = kbp.api.deps.get_conn()
    with kbp.api.deps.db_lock():
        material_id = kbp.ingest.materials.add_or_get(
            conn, name, ext, doc.source, len(doc.text), digest, _now(),
            path=str(path))
    return UploadOut(material_id=material_id, file_name=name, ext=ext,
                     source=doc.source, chars=len(doc.text),
                     has_ocr=doc.has_ocr, page_count=doc.page_count,
                     text=doc.text)


@router.get("/materials", response_model=MaterialsOut)
def materials(limit: int = 200) -> MaterialsOut:
    """上传过的教材，新的在前；limit 上限 1000。"""
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
    doc = _ingest_upload(path, row[1], keep=True)
    return MaterialTextOut(material_id=int(row[0]), file_name=row[1],
                           ext=row[2], chars=len(doc.text), text=doc.text)


@router.post("/extract", response_model=ExtractOut)
def extract(body: ExtractIn) -> ExtractOut:
    """从纯文本抽候选三元组，全部落在词表内。"""
    vocab = _to_vocab(body.vocab)
    cfg = _config()
    try:
        result = kbp.extract.extract_service.extract(body.text, vocab, cfg)
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _signals(report) -> list[SignalOut]:
    return [SignalOut(name=s.name, label=s.label, value=s.value,
                      threshold=s.threshold, triggered=s.triggered)
            for s in report.signals]


def _kit_out(kit, target, report=None, from_bank=False) -> KitAutoOut:
    return KitAutoOut(
        map_version=kit.map_version,
        concepts=[ConceptOut(concept_id=c.concept_id, label=c.label)
                  for c in kit.concepts],
        connections=list(kit.connections),
        total_propositions=len(target.propositions),
        fingerprint=target.fingerprint, from_bank=from_bank,
        possibly_inaccurate=bool(report and report.possibly_inaccurate),
        message=report.message if report else "",
        signals=_signals(report) if report else [],
        calibrated=bool(report and report.calibrated),
        baseline_n=report.baseline_n if report else 0,
        baseline_source=report.baseline_source if report else "")


@router.post("/kit/auto", response_model=KitAutoOut)
def kit_auto(body: KitAutoIn) -> KitAutoOut:
    """运行期自动裁 kit：先查题库，命中即复用；未命中或要求重抽才抽取。

    retry 是学生看到抽崩提示后的重抽：不问题库另抽一批；内容指纹相同的
    仍回旧图，内容不同则登记新版本，旧批原样留着，可随时切回。
    """
    vocab = _to_vocab(body.vocab)
    conn = kbp.api.deps.get_conn()
    entry = None
    if not body.retry:
        entry = kbp.kit.kit_service.bank_find(conn, body.material_id,
                                              vocab.vocab_version)
    if entry is not None:
        target, kit = kbp.kit.kit_service.bank_kit(entry)
        return _kit_out(kit, target, from_bank=True)
    try:
        cfg = _config()
        details = kbp.extract.extract_service.extract_details(
            body.text, vocab, cfg)
        digest = kbp.extract.extract_service.sha256(body.text)
        kbp.extract.discard_store.save(conn, digest, vocab,
                                       details.discards, _now())
        target, kit, _ = kbp.kit.kit_service.freeze_to_bank(
            conn, body.material_id, details.result, _now(), body.map_version,
            usage=kbp.rebuild.usage.SubmissionUsage(conn))
        batch_id = "auto-" + uuid.uuid4().hex[:16]
        kbp.extract.record_store.save(conn, kbp.extract.extract_service.record(
            details.result, batch_id, cfg, body.text,
            sections=details.sections, raw=details.raw, created_at=_now(),
            discards=details.discards))
        kbp.extract.record_store.attach_map(conn, batch_id,
                                            target.map_version,
                                            target.fingerprint)
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
    thresholds = kbp.extract.threshold_store.load(conn)
    report = kbp.extract.quality.assess(details.result, body.text,
                                        thresholds)
    return _kit_out(kit, target, report)
