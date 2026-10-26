"""教材侧路由：读原文、抽取候选。"""

from fastapi import APIRouter, HTTPException


import kbp.extract.extract_service
import kbp.ingest.ingest_service
import kbp.contracts.triple
from kbp.api.schemas import ExtractIn, ExtractOut, IngestIn, IngestOut, TripleOut

router = APIRouter(prefix="/api", tags=["教材"])


def _to_vocab(v) -> kbp.contracts.triple.Vocab:
    return kbp.contracts.triple.Vocab(vocab_id=v.vocab_id, vocab_version=v.version,
                                      connections=tuple(v.connections))


@router.post("/ingest", response_model=IngestOut)
def ingest(body: IngestIn) -> IngestOut:
    """把本地文件读成纯文本。扫描件会自动走 MinerU 云。"""
    try:
        doc = kbp.ingest.ingest_service.ingest(body.path)
    except FileNotFoundError:
        raise HTTPException(404, "文件不存在: " + body.path)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(502, "解析失败: " + str(exc))
    return IngestOut(file_name=doc.file_name, source=doc.source,
                     has_ocr=doc.has_ocr, page_count=doc.page_count,
                     chars=len(doc.text))


@router.post("/extract", response_model=ExtractOut)
def extract(body: ExtractIn) -> ExtractOut:
    """从纯文本抽候选三元组，全部落在词表内。"""
    vocab = _to_vocab(body.vocab)
    try:
        result = kbp.extract.extract_service.extract(body.text, vocab)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(503, "抽取不可用: " + str(exc))
    return ExtractOut(
        vocab_id=result.vocab.vocab_id,
        vocab_version=result.vocab.vocab_version,
        count=len(result.triples),
        triples=[TripleOut(head=t.head, connection=t.connection,
                           tail=t.tail, confidence=t.confidence)
                 for t in result.triples])
