from pathlib import Path

TXT = "txt"
EPUB = "epub"
PDF = "pdf"
UNKNOWN = "unknown"

TXT_EXTS = (".txt", ".md")
_EPUB_MAGIC = b"PK\x03\x04"
_PDF_MAGIC = b"%PDF"


def _by_magic(head: bytes) -> str:
    if head.startswith(_PDF_MAGIC):
        return PDF
    if head.startswith(_EPUB_MAGIC):
        return EPUB
    return UNKNOWN


def _by_suffix(suffix: str) -> str:
    if suffix.lower() in TXT_EXTS:
        return TXT
    if suffix.lower() == ".epub":
        return EPUB
    if suffix.lower() == ".pdf":
        return PDF
    return UNKNOWN


def sniff(path: str) -> str:
    """按魔数优先、扩展名兜底，判定文件属于哪种输入格式。"""
    head = Path(path).open("rb").read(8)
    magic = _by_magic(head)
    if magic is not UNKNOWN:
        return magic
    return _by_suffix(Path(path).suffix)
