import dataclasses
from pathlib import Path

import kbp.ingest.cache
import kbp.ingest.detect
import kbp.ingest.epub
import kbp.ingest.ocr
import kbp.ingest.pdf
import kbp.ingest.textfile
from kbp.contracts.textdoc import EPUB, OCR_CLOUD, TEXT_LAYER, TextDoc

MAX_NAME = 255


def _meta(path: str) -> tuple[str, int]:
    name = Path(path).name[:MAX_NAME]
    return name, Path(path).stat().st_size


def _from_text(path: str, source: str) -> TextDoc:
    name, _ = _meta(path)
    return TextDoc(text=kbp.ingest.textfile.read_text(path), source=source,
                   file_name=name, has_ocr=False, page_count=0)


def _from_pdf(path: str) -> TextDoc:
    name, _ = _meta(path)
    text, pages, scanned = kbp.ingest.pdf.read_pdf(path)
    if not scanned:
        return TextDoc(text=text, source=TEXT_LAYER, file_name=name,
                       has_ocr=False, page_count=pages)
    ocr_text = kbp.ingest.ocr.upload_and_parse(path, name)
    return TextDoc(text=ocr_text, source=OCR_CLOUD, file_name=name,
                   has_ocr=True, page_count=pages)


def _from_epub(path: str) -> TextDoc:
    name, _ = _meta(path)
    return TextDoc(text=kbp.ingest.epub.read_epub(path), source=EPUB, file_name=name,
                   has_ocr=False, page_count=0)


def ingest(path: str) -> TextDoc:
    """文件进，TextDoc 出。格式判定在此收口，下游只见纯文本。"""
    kind = kbp.ingest.detect.sniff(path)
    cached = kbp.ingest.cache.load(path)
    if cached is not None:
        return dataclasses.replace(cached, file_name=_meta(path)[0])
    doc = _parse(path, kind)
    kbp.ingest.cache.save(path, doc)
    return doc


def _parse(path: str, kind: str) -> TextDoc:
    if kind == kbp.ingest.detect.TXT:
        return _from_text(path, TEXT_LAYER)
    if kind == kbp.ingest.detect.PDF:
        return _from_pdf(path)
    if kind == kbp.ingest.detect.EPUB:
        return _from_epub(path)
    raise ValueError("不支持的文件类型: " + Path(path).suffix)
