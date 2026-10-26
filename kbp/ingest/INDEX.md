<!-- @zone code -->

# ingest — 索引
职责：文件 → 纯文本，格式判定，扫描件调 MinerU。不抽取、不连库。
云端不可用时中止报错，不产出空文本。

| 文件 | 内容 |
|---|---|
| `detect.py` | `sniff`：魔数优先、扩展名兜底，判定 txt/epub/pdf |
| `textfile.py` | `read_text`：UTF-8 优先，失败退 GB18030 |
| `epub.py` | `read_epub`：按 zip 内 html 顺序拼文本；`strip_tags` 剥标签 |
| `pdf.py` | `read_pdf`：返回（文本, 页数, 是否扫描件） |
| `ocr.py` | `upload_and_parse`：MinerU 云批次上传；任一步失败都抛 `MinerUUnavailable`（不降级） |
| `service.py` | `ingest(path) -> TextDoc`：本 feature 唯一出口 |
| `tests/ingest/test_ingest.py` | 格式判定、编码回退、epub 解析、无 token 报错、扫描判定 |

配置来自 `.env`：`MINERU_TOKEN`、`MINERU_BASE_URL`、`MINERU_TIMEOUT_S`。

<!-- /@zone code -->
