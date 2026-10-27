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
| `ingest_service.py` | `ingest(path) -> TextDoc`：本 feature 唯一出口；先查缓存，未命中才解析 |
| `uploads.py` | `save(data, name) -> (路径, 字节哈希)`：浏览器上传落盘；`ext_of`/`ALLOWED` 判格式；默认目录 `tmp/uploads`，可用 `KBP_UPLOAD_DIR` 改 |
| `materials.py` | 教材登记表：`add_or_get` 按字节哈希复用 `material_id` 并记落盘 `path`，`get`/`list_all` 供重建、列表与重读正文用 |
| `cache.py` | 解析缓存：键 = 文件字节哈希 + 解析器版本；默认落仓库根 `tmp/ingest_cache`，不入 git |
| `tests/ingest/test_ingest.py` | 格式判定、编码回退、epub 解析、无 token 报错、扫描判定 |
| `tests/ingest/test_materials.py` | 登记一行、同字节复用、内容变新开、列表顺序与上限 |
| `tests/api/test_upload.py` | 上传回正文与教材号、重复复用、格式与空文本拒绝、失败不留文件 |

## 解析缓存

同一文件的字节哈希与解析器版本都相同时，直接复用上次的文本、来源、是否 OCR 与页数，
不再读文件、不再调云端。文件内容一改哈希就变；解析行为一改就抬 `PARSER_VERSION`。
空文本不缓存（避免把一次失败固化）；缓存缺失、损坏或写不进都当未命中，不影响解析。
文件名不进键，改名不失效，读回时换成当前文件名。目录可用 `KBP_INGEST_CACHE` 改。

配置来自 `.env`：`MINERU_TOKEN`、`MINERU_BASE_URL`、`MINERU_TIMEOUT_S`。

<!-- /@zone code -->
