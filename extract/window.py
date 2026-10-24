DEFAULT_WINDOW = 480
DEFAULT_OVERLAP = 80
MAX_WINDOWS = 4000


def split(text: str, window: int = DEFAULT_WINDOW,
          overlap: int = DEFAULT_OVERLAP) -> list[str]:
    """按字符窗口切分长文本，段间重叠，避免连接词跨越边界丢失。"""
    body = (text or "").strip()
    if not body:
        return []
    if window <= 0:
        raise ValueError("window 必须为正")
    if overlap < 0 or overlap >= window:
        raise ValueError("overlap 须满足 0 <= overlap < window")
    step = window - overlap
    chunks: list[str] = []
    start = 0
    while start < len(body) and len(chunks) < MAX_WINDOWS:
        chunks.append(body[start:start + window])
        if start + window >= len(body):
            break
        start += step
    return chunks


def merge_key(head: str, connection: str, tail: str) -> tuple[str, str, str]:
    """去重键：同一（概念, 连接词, 概念）只保留一次。"""
    return (normalize(head), connection, normalize(tail))


def normalize(text: str) -> str:
    """概念字面归一：去首尾空白、压连续空白、转小写。"""
    return " ".join((text or "").split()).lower()
