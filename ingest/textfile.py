from pathlib import Path


def read_text(path: str) -> str:
    """读纯文本文件，优先 UTF-8，取不到时退回 GB18030。"""
    raw = Path(path).read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gb18030", "ignore")
