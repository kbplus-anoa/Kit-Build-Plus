import hashlib
import json
import os
from pathlib import Path

import kbp.contracts.textdoc
from kbp.contracts.textdoc import TextDoc

PARSER_VERSION = "1"
DIR_ENV = "KBP_INGEST_CACHE"


def dir_path() -> Path:
    """缓存目录：默认仓库根 tmp/ingest_cache，可用环境变量改。"""
    got = os.environ.get(DIR_ENV, "").strip()
    if got:
        return Path(got)
    return Path(__file__).resolve().parents[2] / "tmp" / "ingest_cache"


def digest(file_path: str) -> str:
    """文件字节哈希：内容变了，键就变。"""
    sha = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            sha.update(block)
    return sha.hexdigest()


def path_for(file_path: str, version: str = PARSER_VERSION) -> str:
    """缓存文件路径：字节哈希 + 解析器版本。"""
    return str(dir_path() / (digest(file_path) + "-" + version + ".json"))


def load(file_path: str, version: str = PARSER_VERSION) -> TextDoc | None:
    """按字节哈希与解析器版本读缓存；缺失或损坏都当未命中。"""
    try:
        raw = Path(path_for(file_path, version)).read_text("utf-8")
        return _doc(json.loads(raw))
    except (OSError, ValueError, TypeError):
        return None


def save(file_path: str, doc: TextDoc, version: str = PARSER_VERSION) -> None:
    """写缓存；空文本不写，写失败也不影响解析结果。"""
    if not doc.text:
        return
    try:
        target = Path(path_for(file_path, version))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(_data(doc), ensure_ascii=False), "utf-8")
    except (OSError, TypeError):
        return


def _data(doc: TextDoc) -> dict:
    return {"text": doc.text, "source": doc.source, "has_ocr": doc.has_ocr,
            "page_count": doc.page_count}


def _doc(got) -> TextDoc | None:
    if not isinstance(got, dict):
        return None
    source = got.get("source")
    text = got.get("text")
    if source not in kbp.contracts.textdoc.TEXT_SOURCES:
        return None
    if not isinstance(text, str):
        return None
    return TextDoc(text=text, source=source, file_name="",
                   has_ocr=bool(got.get("has_ocr")),
                   page_count=int(got.get("page_count") or 0))
