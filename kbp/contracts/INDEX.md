<!-- @zone code -->

# kbp/contracts — 契约索引
只放契约：类型、字段语义、纯函数签名、Protocol。无实现、无 IO、无业务转换。

| 文件 | 契约域 | 提供方 → 消费方 |
|---|---|---|
| `textdoc.py` | TextDoc、IngestPort | ingest → extract、kit |
| `triple.py` | Vocab、TripleCandidate、ExtractionResult、in_vocab | extract → kit |
| `extractconfig.py` | ExtractConfig、PROVIDERS、config_error、key_env、default_config | 用户配置 → extract、api |
| `extraction.py` | ExtractionRecord（含 discards）、ExtractPort、ExtractionStore、DiscardedCandidate | extract → kit（留档）；存储协议按批次与原文指纹查，可回填冻结图的版本与指纹 |
| `quality.py` | Signal、Thresholds、QualityReport、assess 签名 | extract → api（抽崩体检） |
| `adjudication.py` | Adjudication、AdjudicationLog、MapUsagePort | kit → rebuild（反向注入） |
| `targetmap.py` | Concept、Proposition、TargetMap、Kit、content_fingerprint | kit → rebuild、score |
| `targetbank.py` | BankEntry（含来源批次 batch_id）、check_entry、same_map、TargetMapBank 协议 | kit → kit 存储与 api（题库命中）；来源枚举 adjudicated / auto |
| `submission.py` | 四元关联键 `KEY_FIELDS`、`check_key`、SubmittedProposition、Submission、Draft、模式与时点枚举 | rebuild → score、quiz、export |
| `report.py` | ErrorChain、ScoreResult、四类错误枚举 | score → export |
| `quizsheet.py` | Question、Answer、QuizRecord | quiz → export |
| `tam.py` | ScaleItem、AlphaReport、ScoreRow、CONSTRUCTS、alpha_by_construct 签名 | quiz → api（量表条目与信度） |
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
| `tam` | 整套（含 `CONSTRUCTS`、`MIN_ALPHA`、`alpha_by_construct` 签名） | TAM 量表条目与各构念信度；实现在 `kbp/quiz/{scale,alpha}.py` |
| `report` | `fms` 量纲 0~100，`FMS_MIN` / `FMS_MAX` | 与文献口径一致（D04）；实现只此一份，score 与 export 共用 |
| `submission` | 关联键改四元 `(participant_id, material_id, time_point, submit_seq)`，加 `check_key`；`Submission` 加 `fingerprint` / `time_point` / `submit_seq` | 同一人同一教材同一时点可多次提交，靠序号区分（D09） |
| `quizsheet.QuizRecord` | 去 `session`，改四元键 | 与提交表同键对齐 |
| `exportcsv.SubjectRow` / `QuestionRow` | 关联键改四元 | 两张表可按同一键联结 |
| `targetbank` | 整套（来源枚举、`check_entry`、`same_map`、`TargetMapBank`） | 题库命中与冻结图落库（D02）；实现在 kit |
| `extraction` | 加 `map_version` / `fingerprint` 回填字段与 `ExtractionStore` | 留档要能追溯"这条命题出自哪张图" |
| `quality` | `Signal.threshold` 可空；加 `Thresholds`（四阈值 + `min_props` + 基线来源与样本量 + `calibrated`）；`QualityReport` 加 `calibrated` / `baseline_n` / `baseline_source`；`assess` 加 `thresholds` | 阈值取开发期冻结图分位点；未校准只记录不提示（D08） |
| `extraction` | 加 `DiscardedCandidate`，`ExtractionRecord` 加 `discards` | 越界丢弃也要留档；机器侧一本，与人工裁定留档分开（D12） |
| `extraction.ExtractionStore` | 实现在 `kbp/extract/record_store.py`；一批一条，含原始输出与配置快照 | 自动路每次抽取留档，冻结后回填图版本与指纹 |

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
