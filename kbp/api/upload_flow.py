"""上传侧的公共步骤：扩展名校验与落盘解析。"""

import dataclasses
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException

import kbp.ingest.ingest_service
import kbp.ingest.ocr
import kbp.ingest.uploads
from kbp.api.schemas import MAX_TEXT


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ext_of(name: str) -> str:
    """只收 PDF、EPUB、TXT；其余格式给出可照做的提示。"""
    ext = kbp.ingest.uploads.ext_of(name)
    if ext not in kbp.ingest.uploads.ALLOWED:
        raise HTTPException(
            400, "这个格式暂不支持：「" + (ext or "未知") + "」。"
                 "请上传 PDF、EPUB 或 TXT 文件。")
    return ext


def ingest(path: Path, name: str, keep: bool = False):
    """解析落盘的文件；新上传失败时删掉它，别留半个教材。

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
