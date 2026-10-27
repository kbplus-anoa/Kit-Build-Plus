"""上传落盘：浏览器给的字节先存成文件，解析仍走 ingest 那一套。"""

import hashlib
import os
import re
import uuid
from pathlib import Path

ALLOWED = ("pdf", "epub", "txt")
MAX_BYTES = 40 * 1024 * 1024
DIR_ENV = "KBP_UPLOAD_DIR"
UNSAFE = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff._-]+")


def dir_path() -> Path:
    """上传目录；默认仓库根 tmp/uploads，可用 KBP_UPLOAD_DIR 改。"""
    raw = os.environ.get(DIR_ENV, "").strip()
    base = Path(raw) if raw else Path(__file__).resolve().parents[2] / "tmp" / "uploads"
    base.mkdir(parents=True, exist_ok=True)
    return base


def ext_of(name: str) -> str:
    """取扩展名小写；没有扩展名时是空串。"""
    dot = name.rfind(".")
    return name[dot + 1:].lower() if dot > 0 else ""


def safe_stem(name: str) -> str:
    """只留安全字符，避免原文件名带路径分隔符跑出上传目录。"""
    stem = Path(name).stem or "doc"
    return UNSAFE.sub("-", stem)[:60] or "doc"


def save(data: bytes, name: str) -> tuple[Path, str]:
    """落盘并返回路径与字节哈希；同名不同内容靠随机后缀分开。"""
    target = dir_path() / (safe_stem(name) + "-" + uuid.uuid4().hex[:12]
                           + "." + ext_of(name))
    target.write_bytes(data)
    return target, hashlib.sha256(data).hexdigest()


def drop(path: Path) -> None:
    """解析失败时删掉落盘文件，别留垃圾。"""
    try:
        path.unlink()
    except OSError:
        pass
