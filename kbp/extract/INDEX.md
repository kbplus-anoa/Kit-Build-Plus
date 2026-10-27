<!-- @zone code -->

# extract — 索引
职责：文本 + 词表 → 候选三元组，全部落在词表内。不裁定对错、不冻结。

| 文件 | 内容 |
|---|---|
| `vocab.py` | `load` / `build`：读 JSON 词表，缺字段、重复、空串、超量均报 `VocabError` |
| `prompt.py` | 提示词构造：词表入提示、要求有向三元组、JSON Output 的样例与 json 字样 |
| `chat_client.py` | OpenAI 兼容接口的最小客户端；密钥只从环境变量读；空 content 与限流重试 |
| `engine.py` | `ChatEngine`：`extract(文本, 词表, 配置)` 的实现，协议与供应商无关 |
| `normalize.py` | 模型输出 → 契约三元组，唯一收口处：越界/自环/重复/概念里塞连接词一律丢弃；置信度是本地代理分 |
| `extract_service.py` | `extract(text, vocab, config, engine)`：编排；`record` 产出留档；`sha256` |
| `quality.py` | `assess(result, text, thresholds)`：抽崩检测 S1–S4；未校准只记原值不判；不改结果不拦流程 |
| `threshold_store.py` | 阈值组落库（单行）；无行即未校准；写入须记基线来源与样本量 |
| `window.py` | 按空行分段，超长段按字上限硬切；`merge_key` 去重键 |

## 协议与供应商

协议统一是 **OpenAI 兼容格式**（`{base_url}/v1/chat/completions`）。
`provider` 只决定两件事：密钥从哪个环境变量读、界面上怎么称呼。

| provider | 密钥环境变量 | 说明 |
|---|---|---|
| `openai_compatible` | `KBP_API_KEY` | 自定义 / OpenAI 兼容，唯一枚举 |

不写死任何服务商：换服务商 = 改 `base_url` + `model` + 填密钥，不改一行代码。
开发期样例是 DeepSeek（`https://api.deepseek.com` + `deepseek-chat`）。
历史配置里的 `deepseek` / `openai` 读回时归一到 `openai_compatible`。

词表文件格式（JSON）：

```json
{"vocab_id": "心理学", "version": "v1", "connections": ["属于", "导致"]}
```

**密钥不在此层保存**：只从环境变量读取，不进配置结构、不进日志、不进异常信息。

## 置信度是本地代理分

不用模型自报的 confidence（模型常不给，给了也不可比），改由本地按证据算分：
`evidence` 在原文里逐字命中得 1.0，对不上得 0.4，没证据也没原文得 0.2；
位置与输出顺序不一致（越序）乘 0.6；概念超过 20 字置 `suspect` 并封顶 0.15、排在最后。
同分按首次出现顺序，同一输入两次输出同序 —— 排序负责「先看哪条」，不负责丢人。

## 抽崩阈值

四个阈值取开发期冻结图的经验分位点，连基线来源与样本量一起存进 `quality_thresholds`。
行不存在或四阈值没齐、缺来源、样本量为 0 时，整组算未校准：信号只带原值，
`threshold` 为空、`triggered` 为假，也不出「可能不可信」提示。
命题数少于 `min_props` 时只记录不提示。提示文案固定为
「本次组件抽取可能不可信，您可重新抽取（原因）」。

配置见 `kbp/contracts/extractconfig.py`；抽取档案见 `kbp/contracts/extraction.py`。

<!-- /@zone code -->
