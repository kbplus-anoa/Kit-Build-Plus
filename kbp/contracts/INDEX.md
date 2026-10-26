<!-- @zone code -->

# kbp/contracts — 契约索引
只放契约：类型、字段语义、纯函数签名、Protocol。无实现、无 IO、无业务转换。

| 文件 | 契约域 | 提供方 → 消费方 |
|---|---|---|
| `textdoc.py` | TextDoc、IngestPort | ingest → extract、kit |
| `triple.py` | Vocab、TripleCandidate、ExtractionResult、in_vocab | extract → kit |
| `extractconfig.py` | ExtractConfig、PROVIDERS、config_error、key_env、default_config | 用户配置 → extract、api |
| `extraction.py` | ExtractionRecord、ExtractPort | extract → kit（留档） |
| `quality.py` | Signal、QualityReport、assess 签名 | extract → api（抽崩体检） |
| `adjudication.py` | Adjudication、AdjudicationLog、MapUsagePort | kit → rebuild（反向注入） |
| `targetmap.py` | Concept、Proposition、TargetMap、Kit、content_fingerprint | kit → rebuild、score |
| `submission.py` | SubmittedProposition、Submission、Draft、模式枚举 | rebuild → score、quiz、export |
| `report.py` | ErrorChain、ScoreResult、四类错误枚举 | score → export |
| `quizsheet.py` | Question、Answer、QuizRecord、三时点枚举 | quiz → export |
| `exportcsv.py` | SubjectRow、QuestionRow、CsvPayload、UTF8_BOM | export → CSV 文件 |

冻结规则：契约被第二个 feature 消费即冻结；改动先给旧→新、影响范围、迁移方式，经用户确认。

## 本轮增量

| 契约 | 增量 | 用途 |
|---|---|---|
| `triple.TripleCandidate` | `evidence: str = ""` | 记录命题依据的原文片段，供裁定与追溯 |
| `targetmap.TargetMap` | `fingerprint: str = ""` | 区分同一教材在不同机器裁出的不同 kit |
| `extractconfig` | 整套（含 `key_env`、`default_config`） | 抽取配置；**不含密钥** |
| `extraction` | `ExtractionRecord` + `ExtractPort` | 抽取留档与引擎协议 |
| `exportcsv.SubjectRow` | `fingerprint: str = ""` | 导出可直接按指纹筛同批 |
| `targetmap` | `content_fingerprint` 签名 | 实现在 `kbp/kit/_rules.py` |
| `quality` | `Signal` / `QualityReport` / `assess` 签名 | 抽崩信号要带出到界面，故为契约；实现在 `kbp/extract/quality.py` |
| `triple.TripleCandidate` | `suspect: bool = False` | 概念过长的可疑项：不静默丢，标出来排到最后 |
| `triple.TripleCandidate.confidence` | 语义改为本地代理分 | 按 evidence 是否逐字命中原文算分，只用于排序，不采用模型自报值 |

全部有默认值，向后兼容。

## 指纹为什么是契约

它不是工具函数而是一条**跨 feature 的约定**：`export` 不懂图结构，
但它要能按"同一批人"筛，就必须认得出"同一份目标图"。
所以签名放契约层，实现在提供方 `kit`，消费方只调签名。

## 协议与供应商

`ExtractConfig.provider` 只决定密钥环境变量与界面文案；
协议统一是 OpenAI 兼容格式，provider 只有一个值 `openai_compatible`
（界面文案「自定义 / OpenAI 兼容」），不写死服务商；密钥走 `KBP_API_KEY`。
历史值 `deepseek` / `openai` 由 `canonical_provider` 归一到当前枚举。

<!-- /@zone code -->
