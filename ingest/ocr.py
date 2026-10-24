import json
import os
import urllib.request

DEFAULT_BASE = "https://mineru.net/api/v4"


class MinerUUnavailable(RuntimeError):
    """未配置 MINERU_TOKEN，扫描件链路不可用。"""


def _token() -> str:
    token = os.environ.get("MINERU_TOKEN", "").strip()
    if not token:
        raise MinerUUnavailable("未配置 MINERU_TOKEN，扫描件无法解析")
    return token


def _base() -> str:
    return os.environ.get("MINERU_BASE_URL", DEFAULT_BASE).rstrip("/")


def _timeout() -> float:
    return float(os.environ.get("MINERU_TIMEOUT_S", "60"))


def upload_and_parse(path: str, file_name: str) -> str:
    """把扫描件交给 MinerU 云解析，返回其 markdown 结果。"""
    token = _token()
    payload = json.dumps({
        "enable_formula": False,
        "language": "ch",
        "files": [{"name": file_name, "is_ocr": True}],
    }).encode("utf-8")
    req = urllib.request.Request(
        _base() + "/file_urls/batch",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + token},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=_timeout()) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return _extract_urls(body)


def _extract_urls(body: dict) -> str:
    data = body.get("data") or {}
    urls = data.get("file_urls") or []
    if not urls:
        raise MinerUUnavailable("MinerU 未返回上传地址")
    return str(urls[0])
