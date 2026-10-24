from fastapi import FastAPI

app = FastAPI(title="Kit-Build-Plus")


@app.get("/")
def index() -> dict[str, str]:
    return {"ok": "Kit-Build-Plus"}
