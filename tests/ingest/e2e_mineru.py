"""真实调用 MinerU 的端到端冒烟脚本，需已填 MINERU_TOKEN。

不属于 pytest 用例：会消耗云端配额且有网络依赖，需手工运行：
    set -a; . .env; set +a
    .venv/bin/python tests/ingest/e2e_mineru.py
"""

import pathlib
import sys

import kbp.ingest.ocr

PDF = "docs/research/papers/10.58459_icce_2016_1012.pdf"


def main() -> int:
    name = pathlib.Path(PDF).name
    batch_id, upload_url = kbp.ingest.ocr.request_upload(name)
    print("batch_id:", bool(batch_id))
    kbp.ingest.ocr.put_file(upload_url, PDF)
    print("upload: ok")
    item = kbp.ingest.ocr.poll(batch_id)
    print("state:", item.get("state"))
    markdown = kbp.ingest.ocr.download_markdown(str(item.get("full_zip_url")))
    print("chars:", len(markdown))
    return 0 if markdown.strip() else 1


if __name__ == "__main__":
    sys.exit(main())
