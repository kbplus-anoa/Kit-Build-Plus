import zipfile
from pathlib import Path

_CONTAINER = "META-INF/container.xml"
_OPF_SUFFIX = ".opf"
_HTML_EXTS = (".xhtml", ".html", ".htm")


def _opf_path(archive: zipfile.ZipFile) -> str:
    root = archive.read(_CONTAINER).decode("utf-8", "ignore")
    start = root.find("full-path=")
    if start < 0:
        raise ValueError("epub 缺少 rootfile 声明")
    quote = root[start + len("full-path=")]
    rest = root[start + len("full-path=") + 1:]
    return rest[: rest.find(quote)]


def _html_names(archive: zipfile.ZipFile) -> list[str]:
    return [n for n in archive.namelist() if n.lower().endswith(_HTML_EXTS)]


def read_epub(path: str) -> str:
    """把 epub 的全部章节按骨架顺序拼成一个纯文本，去掉标签。"""
    with zipfile.ZipFile(Path(path)) as archive:
        names = _html_names(archive)
        if not names:
            return ""
        parts = [archive.read(n).decode("utf-8", "ignore") for n in names]
    return "\n".join(strip_tags(part) for part in parts)


def strip_tags(html: str) -> str:
    """极简标签剥离：只保留文本与换行，不做结构还原。"""
    out = []
    depth = 0
    for char in html:
        if char == "<":
            depth += 1
        elif char == ">":
            depth = max(depth - 1, 0)
            if depth == 0:
                out.append(" ")
        elif depth == 0:
            out.append(char)
    return " ".join("".join(out).split())
