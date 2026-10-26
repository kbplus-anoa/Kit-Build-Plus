<!-- @zone code -->

# extract — 索引
职责：文本 + 词表 → 候选三元组，全部落在词表内。不裁定对错、不冻结。

| 文件 | 内容 |
|---|---|
| `vocab.py` | `load` / `build`：读 JSON 词表，缺字段、重复、空串、超量均报 `VocabError` |
| `_prompt.py` | 提示词构造：词表入提示、要求有向三元组、JSON Output 的样例与 json 字样 |
| `deepseek_client.py` | httpx 直调 OpenAI 兼容接口；密钥只从 `DEEPSEEK_API_KEY` 读；空 content 重试 |
| `_normalize.py` | 模型输出 → 契约三元组，唯一收口处：越界/自环/重复一律丢弃 |
| `extract_service.py` | `extract(text, vocab, config, engine)`：编排，engine 可注入便于测试 |
| `_window.py` | 按字数上限截断（不再细切） |
| `tests/extract/` | 词表校验、提示词形状、规范化、客户端错误处理、端到端 |

词表文件格式（JSON）：

```json
{"vocab_id": "心理学", "version": "v1", "connections": ["属于", "导致"]}
```

**密钥不在此层保存**：只从环境变量 `DEEPSEEK_API_KEY` 读取，
不进配置结构、不进日志、不进异常信息。

配置见 `kbp/contracts/extractconfig.py`；抽取档案见 `kbp/contracts/extraction.py`。

<!-- /@zone code -->
