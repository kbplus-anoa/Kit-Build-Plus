from dataclasses import dataclass
from typing import Protocol

TEXT_LAYER = "TEXT_LAYER"
EPUB = "EPUB"
OCR_CLOUD = "OCR_CLOUD"

TEXT_SOURCES = (TEXT_LAYER, EPUB, OCR_CLOUD)


@dataclass(frozen=True)
class TextDoc:
    """ingest 契约：原文转出的纯文本及其来历。"""

    text: str  # 全文纯文本，UTF-8；可为空串（解析降级），不可为 None
    source: str  # 处理路径枚举，取值见 TEXT_SOURCES；不可空
    file_name: str  # 原文件名含扩展名，仅用于展示；不可空
    has_ocr: bool  # 文本是否含 OCR 成分；不可空，True 时下游应提示可能有识别错误
    page_count: int  # 原始页数；单位：页；不可空，0 表示页数未知


class IngestPort(Protocol):
    """行为契约：文件路径进，TextDoc 出。不做抽取、不连库。"""

    def ingest(self, file_path: str) -> TextDoc: ...


def is_scanned(doc: TextDoc) -> bool:
    """纯函数契约：是否需要提示 OCR 风险。"""
    ...
