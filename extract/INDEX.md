<!-- @zone code -->

# extract — 索引
职责：纯文本 + 连接词表 → 候选三元组，全部落在词表内。不裁定对错、不冻结。

| 文件 | 内容 |
|---|---|
| `vocab.py` | `load` / `build`：读 JSON 词表，缺字段、重复、空串、超量均报 `VocabError` |
| `schema.py` | `to_schema`：UIE 的 schema 是 `{"概念": [连接词...]}`，故越界不可能 |
| `window.py` | `split` 按字符窗口切分并重叠；`merge_key` / `normalize` 供去重 |
| `uie.py` | `UieExtractor` 惰性加载模型；`raw_to_triples` 把输出转契约类型并丢弃越界连接词 |
| `extract_service.py` | `extract(text, vocab, engine)`：切窗、抽取、去重、按置信度降序 |
| `test/test_extract.py` | 词表校验、schema 形状、窗口切分、越界丢弃、去重排序、未装模型报错 |

词表文件格式（JSON）：

```json
{"vocab_id": "心理学", "version": "v1", "connections": ["属于", "导致"]}
```

调用方在测试或离线场景可传入自己的 `engine`，不必加载模型。
未安装 `paddlenlp` 时 `UieExtractor` 抛 `UieUnavailable`，不静默返回空结果。

<!-- /@zone code -->
