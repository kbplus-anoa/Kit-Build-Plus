"""Kit-Build-Plus 的 HTTP 入口。只做参数收口与错误映射，业务在 feature 里。"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent
for _p in (str(_SRC), str(_SRC.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI  # noqa: E402

import routes_data  # noqa: E402
import routes_flow  # noqa: E402
import routes_text  # noqa: E402
from bootstrap import install_paths  # noqa: E402

install_paths()

app = FastAPI(title="Kit-Build-Plus", version="0.1.0")
app.include_router(routes_text.router)
app.include_router(routes_flow.router)
app.include_router(routes_data.router)


@app.get("/")
def index() -> dict:
    """服务存活检查。"""
    return {"ok": "Kit-Build-Plus", "version": "0.1.0"}


@app.get("/api/health")
def health() -> dict:
    """确认数据库与装配层可用。"""
    from deps import get_conn
    cur = get_conn().execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    return {"ok": True, "tables": cur.fetchone()[0]}
