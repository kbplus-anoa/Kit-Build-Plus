import re

DEFAULT_WINDOW = 480
DEFAULT_OVERLAP = 80
MAX_WINDOWS = 4000
BLANK = re.compile(r"\n\s*\n+")


def split(text: str, window: int = DEFAULT_WINDOW,
          overlap: int = 0) -> list[str]:
    """按段切分正文，标题、空行与超长段落都按字上限硬切。

    云端模型一次能吃的字数远大于本机窗口，因此默认不重叠：
    重叠会让同一条命题抽到两次，靠下游去重掩盖反而更难查。
    """
    body = (text or "").strip()
    if not body:
        return []
    if window <= 0:
        raise ValueError("window 必须为正")
    if overlap < 0 or overlap >= window:
        raise ValueError("overlap 须满足 0 <= overlap < window")
    return _pack(_paragraphs(body), window, window - overlap)


def _pack(paras: list[str], window: int, step: int) -> list[str]:
    """短段装进同一个窗口，只有超长段才按字上限硬切。

    一段就是一个空行分隔的语义块；窗口是模型一次能吃的量，
    因此能把许多短段合并送出，而不必一段一次请求。
    """
    chunks: list[str] = []
    buf = ""
    for para in paras:
        if len(para) > window:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_cut(para, window, step))
        elif not buf:
            buf = para
        elif len(buf) + 2 + len(para) <= window:
            buf = buf + "\n\n" + para
        else:
            chunks.append(buf)
            buf = para
        if len(chunks) >= MAX_WINDOWS:
            return chunks[:MAX_WINDOWS]
    if buf:
        chunks.append(buf)
    return chunks[:MAX_WINDOWS]


def _paragraphs(body: str) -> list[str]:
    """按空行断成语义段；段内换行保留，避免把同一句拆开。"""
    parts = (part.strip() for part in BLANK.split(body))
    return [part for part in parts if part] or [body]


def _cut(para: str, window: int, step: int) -> list[str]:
    if len(para) <= window:
        return [para]
    out: list[str] = []
    start = 0
    while start < len(para):
        out.append(para[start:start + window])
        if start + window >= len(para):
            break
        start += step
    return out


def merge_key(head: str, connection: str, tail: str) -> tuple[str, str, str]:
    """去重键：同一（概念, 连接词, 概念）只保留一次。"""
    return (normalize(head), connection, normalize(tail))


def normalize(text: str) -> str:
    """概念字面归一：去首尾空白、压连续空白、转小写。"""
    return " ".join((text or "").split()).lower()
