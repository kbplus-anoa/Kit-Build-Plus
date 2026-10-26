"""教材侧路由：读原文、抽取候选、运行期自动裁 kit。"""

from fastapi import APIRouter, HTTPException


import kbp.api.config_store
import kbp.contracts.extractconfig
import kbp.contracts.triple
import kbp.extract.chat_client
import kbp.extract.extract_service
import kbp.ingest.ingest_service
import kbp.kit.kit_service
from kbp.api.schemas import (
    ConceptOut, ExtractIn, ExtractOut, IngestIn, IngestOut, KitAutoIn, KitAutoOut,
    TripleOut)

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
                           evidence=t.evidence)
                 for t in result.triples])


@router.post("/kit/auto", response_model=KitAutoOut)
def kit_auto(body: KitAutoIn) -> KitAutoOut:
    """运行期自动裁 kit：文本 → 抽取 → 冻结 → 拆零件，全程无人裁定。"""
    vocab = _to_vocab(body.vocab)
    try:
        result = kbp.extract.extract_service.extract(body.text, vocab, _config())
        target, kit = kbp.kit.kit_service.build_kit_auto(result, body.map_version)
    except kbp.extract.extract_service.ExtractError as exc:
        raise HTTPException(400, str(exc))
    except kbp.extract.chat_client.MissingKey as exc:
        raise HTTPException(503, str(exc))
    except kbp.kit.freeze.FreezeError as exc:
        raise HTTPException(422, "抽出的图不足以成题: " + str(exc))
    except Exception as exc:
        raise HTTPException(503, "自动裁 kit 不可用: " + str(exc))
    return KitAutoOut(map_version=kit.map_version,
                      concepts=[ConceptOut(concept_id=c.concept_id, label=c.label)
                                for c in kit.concepts],
                      connections=list(kit.connections),
                      total_propositions=len(target.propositions),
                      fingerprint=target.fingerprint)
