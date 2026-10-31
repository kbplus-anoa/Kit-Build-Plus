"""一键启动：一个端口同时给前端页面和 /api 后端。

前端取 web/dist（已随仓库提供），没有就退回 web/ 的开发入口；
后端是 FastAPI（kbp.api.main:app）。/api 开头的请求交给后端，
其余按文件路径从静态目录里取，取不到就给 index.html 让前端自己认路由。
第一次启动把 data/ 里的种子库与示例教材放进 tmp/，之后只动 tmp/ 那一份。
"""

import mimetypes
import os
import shutil
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

import uvicorn

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
TMP = BASE / "tmp"
SEED = DATA / "kb.seed.sqlite3"
DB = TMP / "kb.sqlite3"
UPLOADS = TMP / "uploads"
HOST = "127.0.0.1"
PORT = 8848


def web_root() -> Path:
    """构建产物优先，其次开发入口。"""
    for name in ("dist", "web"):
        path = BASE / "web" / name if name == "dist" else BASE / "web"
        if (path / "index.html").is_file():
            return path
    return BASE / "web"


WEB = web_root()
INDEX = WEB / "index.html"


def _body(path: Path) -> tuple:
    kind = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    if path.suffix == ".js":
        kind = "text/javascript; charset=utf-8"
    elif path.suffix in (".css", ".html"):
        kind = kind + "; charset=utf-8"
    return path.read_bytes(), kind


def _target(path: str) -> tuple:
    """路径换成文件；越界或不存在则回 index.html。"""
    rel = urllib.parse.unquote(path).lstrip("/") or "index.html"
    file = (WEB / rel).resolve()
    if WEB not in file.parents and file != WEB:
        return INDEX, 200
    if file.is_file():
        return file, 200
    return INDEX, 200


class Site:
    """静态文件包在 ASGI 后端外面，/api 原样转给 FastAPI。"""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or scope["path"].startswith("/api"):
            await self.app(scope, receive, send)
            return
        file, status = _target(scope["path"])
        data, kind = _body(file)
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", kind.encode()),
                                (b"content-length", str(len(data)).encode()),
                                (b"cache-control", b"no-cache")]})
        await send({"type": "http.response.body", "body": data})


def seed() -> None:
    """第一次启动把种子库与示例教材放进 tmp/。"""
    TMP.mkdir(parents=True, exist_ok=True)
    if SEED.is_file() and not DB.exists():
        shutil.copyfile(SEED, DB)
        print("已放开种子库：%s" % DB)
    sample = DATA / "materials"
    if sample.is_dir():
        UPLOADS.mkdir(parents=True, exist_ok=True)
        for src in sorted(sample.iterdir()):
            dst = UPLOADS / src.name
            if src.is_file() and not dst.exists():
                shutil.copyfile(src, dst)
                print("已放开示例教材：%s" % dst)


def port_of(argv: list) -> int:
    """--port N 或 KBP_PORT 指定端口，默认 8848。"""
    if "--port" in argv:
        spot = argv.index("--port") + 1
        if spot < len(argv) and argv[spot].isdigit():
            return int(argv[spot])
    got = os.environ.get("KBP_PORT", "").strip()
    return int(got) if got.isdigit() else PORT


def main() -> int:
    os.chdir(BASE)
    if not INDEX.is_file():
        print("缺少前端文件：先在本机执行 cd web && npm install && npm run build。",
              file=sys.stderr)
        return 1
    seed()
    port = port_of(sys.argv)
    from kbp.api.main import app
    print("打开 http://%s:%d/  ；按 Ctrl+C 停。" % (HOST, port))
    if "--open" in sys.argv:
        threading.Timer(1.5, lambda: webbrowser.open(
            "http://%s:%d/" % (HOST, port))).start()
    uvicorn.run(Site(app), host=HOST, port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
