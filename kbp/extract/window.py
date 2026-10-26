DEFAULT_WINDOW = 480
DEFAULT_OVERLAP = 80
MAX_WINDOWS = 4000


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
    step = window - overlap
    chunks: list[str] = []
    for para in _paragraphs(body):
        chunks.extend(_cut(para, window, step))
        if len(chunks) >= MAX_WINDOWS:
            return chunks[:MAX_WINDOWS]
    return chunks


def _paragraphs(body: str) -> list[str]:
    """先按空行与换行断开，让每段语义尽量完整。"""
    out: list[str] = []
    for line in body.splitlines():
        line = line.strip()
        if line:
            out.append(line)
    return out or [body]


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
