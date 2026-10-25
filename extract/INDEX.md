<!-- @zone code -->

# extract — 索引
职责：纯文本 + 连接词表 → 候选三元组，全部落在词表内。不裁定对错、不冻结。

| 文件 | 内容 |
|---|---|
| `vocab.py` | `load` / `build`：读 JSON 词表，缺字段、重复、空串、超量均报 `VocabError` |
| `schema.py` | `to_schema`：UIE 的 schema 是 `{"概念": [连接词...]}`，故越界不可能 |
| `window.py` | `split` 按字符窗口切分并重叠；`merge_key` / `normalize` 供去重 |
| `onnx_uie.py` | **唯一引擎**：ONNX 版 UIE。`OnnxUieExtractor` 惰性建会话，分词用 tokenizers；`raw_to_triples` 兼两种原始输出 |
| `extract_service.py` | `extract(text, vocab, engine)`：切窗、抽取、去重、按置信度降序；engine 缺省即 ONNX |
| `build_onnx.md` | ONNX 权重如何重建（含 dynamo 导出器的坑） |
| `test/test_extract.py` | 词表校验、schema 形状、窗口切分、越界丢弃、去重排序、缺权重报错 |
| `test/test_onnx_uie.py` | CLS/SEP id、句类型、span 配对、越界丢弃、单概念不成对 |

词表文件格式（JSON）：

```json
{"vocab_id": "心理学", "version": "v1", "connections": ["属于", "导致"]}
```

权重落在 `tmp/uie/`（`inference.onnx` 448MB + `vocab.txt`），不入 git，路径可用
`KBP_UIE_DIR` 覆盖。测试或离线场景可注入自己的 `engine`，不加载模型。

<!-- /@zone code -->
