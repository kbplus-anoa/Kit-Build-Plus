"""Kit-Build-Plus 的 HTTP 入口。只做参数收口与错误映射，业务在 feature 里。"""

from fastapi import FastAPI

import kbp.api.envfile
import kbp.api.routes_config
import kbp.api.routes_data
import kbp.api.routes_flow
import kbp.api.routes_kit
import kbp.api.routes_tam
import kbp.api.routes_text

kbp.api.envfile.apply()

app = FastAPI(title="Kit-Build-Plus", version="0.1.0")
app.include_router(kbp.api.routes_config.router)
app.include_router(kbp.api.routes_text.router)
app.include_router(kbp.api.routes_flow.router)
app.include_router(kbp.api.routes_kit.router)
app.include_router(kbp.api.routes_data.router)
app.include_router(kbp.api.routes_tam.router)


@app.get("/")
def index() -> dict:
    """服务存活检查。"""
    return {"ok": "Kit-Build-Plus", "version": "0.1.0"}


@app.get("/api/health")
def health() -> dict:
    """确认数据库与装配层可用。"""
    from kbp.api.deps import get_conn
    cur = get_conn().execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    return {"ok": True, "tables": cur.fetchone()[0]}
