import logging

from pypdf import PdfReader

MIN_TEXT_CHARS_PER_PAGE = 30

logging.getLogger("pypdf").setLevel(logging.ERROR)


def _pages(reader: PdfReader) -> list[str]:
    out = []
    for page in reader.pages:
        try:
            out.append(page.extract_text() or "")
        except Exception:
            out.append("")
    return out


def _looks_scanned(pages: list[str]) -> bool:
    if not pages:
        return True
    dense = sum(1 for p in pages if len(p.strip()) >= MIN_TEXT_CHARS_PER_PAGE)
    return dense * 2 < len(pages)


def read_pdf(path: str) -> tuple[str, int, bool]:
    """读 PDF：返回（文本, 页数, 是否扫描件）。扫描件由调用方转 MinerU。"""
    reader = PdfReader(path)
    pages = _pages(reader)
    return "\n".join(pages), len(pages), _looks_scanned(pages)
