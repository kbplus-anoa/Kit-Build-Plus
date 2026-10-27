"""教材侧路由：读原文、抽取候选、运行期自动裁 kit。"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException


import kbp.api.config_store
import kbp.api.deps
import kbp.contracts.extractconfig
import kbp.contracts.triple
import kbp.extract.chat_client
import kbp.extract.extract_service
import kbp.extract.quality
import kbp.extract.threshold_store
import kbp.ingest.ingest_service
import kbp.ingest.ocr
import kbp.kit.bank_store
import kbp.kit.kit_service
import kbp.kit.lock
import kbp.rebuild.usage
from kbp.api.schemas import (
    ConceptOut, ExtractIn, ExtractOut, IngestIn, IngestOut, KitAutoIn, KitAutoOut,
    SignalOut, TripleOut)

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
    """运行期自动裁 kit：先查题库，命中即复用；未命中才抽取并登记新版本。"""
    vocab = _to_vocab(body.vocab)
    conn = kbp.api.deps.get_conn()
    entry = kbp.kit.kit_service.bank_find(conn, body.material_id,
                                          vocab.vocab_version)
    if entry is not None:
        target, kit = kbp.kit.kit_service.bank_kit(entry)
        return _kit_out(kit, target, from_bank=True)
    try:
        result = kbp.extract.extract_service.extract(body.text, vocab, _config())
        target, kit, _ = kbp.kit.kit_service.freeze_to_bank(
            conn, body.material_id, result, _now(), body.map_version,
            usage=kbp.rebuild.usage.SubmissionUsage(conn))
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
    report = kbp.extract.quality.assess(result, body.text, thresholds)
    return _kit_out(kit, target, report)
