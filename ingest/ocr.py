import io
import json
import os
import time
import urllib.request
import zipfile

DEFAULT_BASE = "https://mineru.net/api/v4"
DONE = "done"
FAILED = ("failed",)


class MinerUUnavailable(RuntimeError):
    """未配置 MINERU_TOKEN，或云端解析不可用。"""


def _token() -> str:
    token = os.environ.get("MINERU_TOKEN", "").strip()
    if not token:
        raise MinerUUnavailable("未配置 MINERU_TOKEN，扫描件无法解析")
    return token


def _base() -> str:
    return os.environ.get("MINERU_BASE_URL", DEFAULT_BASE).rstrip("/")


def _timeout() -> float:
    return float(os.environ.get("MINERU_TIMEOUT_S", "60"))


def _poll_interval() -> float:
    return float(os.environ.get("MINERU_POLL_S", "3"))


def _max_polls() -> int:
    return int(os.environ.get("MINERU_MAX_POLLS", "200"))


def _headers() -> dict:
    return {"Content-Type": "application/json",
            "Authorization": "Bearer " + _token()}


def _post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers=_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=_timeout()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def request_upload(file_name: str) -> tuple[str, str]:
    """第一步：申请预签名上传地址，返回（batch_id, 上传 URL）。"""
    body = _post(_base() + "/file-urls/batch", {
        "files": [{"name": file_name}],
        "model_version": os.environ.get("MINERU_MODEL", "pipeline"),
        "language": os.environ.get("MINERU_LANG", "ch"),
    })
    data = body.get("data") or {}
    batch_id = str(data.get("batch_id") or "")
    urls = data.get("file_urls") or []
    if not batch_id or not urls:
        raise MinerUUnavailable("申请上传地址失败: " + str(body.get("msg")))
    return batch_id, str(urls[0])


def put_file(upload_url: str, path: str) -> None:
    """第二步：把本地文件 PUT 到预签名地址，不得带 Authorization 头。"""
    blob = open(path, "rb").read()
    req = urllib.request.Request(upload_url, data=blob, method="PUT")
    with urllib.request.urlopen(req, timeout=_timeout()) as resp:
        if resp.status not in (200, 201):
            raise MinerUUnavailable("上传失败，状态 " + str(resp.status))


def poll(batch_id: str) -> dict:
    """第三步：轮询批次，直到 done 或 failed，返回单条结果。"""
    url = _base() + "/extract-results/batch/" + batch_id
    for _ in range(_max_polls()):
        req = urllib.request.Request(url, headers=_headers())
        with urllib.request.urlopen(req, timeout=_timeout()) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        item = _first_result(body)
        if item:
            state = item.get("state", "")
            if state == DONE:
                return item
            if state in FAILED:
                raise MinerUUnavailable("云端解析失败: " + str(item.get("err_msg", "")))
        time.sleep(_poll_interval())
    raise MinerUUnavailable("云端解析超时")


def _first_result(body: dict) -> dict:
    data = body.get("data") or {}
    items = data.get("extract_result") or []
    if isinstance(items, dict):
        return items
    return items[0] if items else {}


def download_markdown(zip_url: str) -> str:
    """第四步：下载结果 zip，取出其中的 markdown 正文本。"""
    with urllib.request.urlopen(zip_url, timeout=_timeout()) as resp:
        blob = resp.read()
    return markdown_from_zip(blob)


def markdown_from_zip(blob: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(".md")]
        if not names:
            return ""
        names.sort(key=lambda n: (n.count("/"), n))
        return "\n".join(archive.read(n).decode("utf-8", "ignore")
                         for n in names)


def upload_and_parse(path: str, file_name: str) -> str:
    """扫描件完整云端流程：申请地址 → 上传 → 轮询 → 下载，返回 markdown。"""
    batch_id, upload_url = request_upload(file_name)
    put_file(upload_url, path)
    item = poll(batch_id)
    zip_url = str(item.get("full_zip_url") or "")
    if not zip_url:
        raise MinerUUnavailable("云端未返回结果包地址")
    return download_markdown(zip_url)
