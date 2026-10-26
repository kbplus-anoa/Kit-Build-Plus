<!-- @zone code -->

# kbp/contracts — 契约索引
只放契约：类型、字段语义、纯函数签名、Protocol。无实现、无 IO、无业务转换。

## 现状说明

本目录当前物理位置是 `contract-share/`，重构完成后将迁入 `kbp/contracts/`。
迁入后模块名为 `kbp.contracts.*`，与 feature 子包天然隔离。

| 文件 | 契约域 | 提供方 → 消费方 |
|---|---|---|
| `textdoc.py` | TextDoc、IngestPort | ingest → extract、kit |
| `triple.py` | Vocab、TripleCandidate、ExtractionResult | extract → kit |
| `extractconfig.py` | ExtractConfig、config_error | 用户配置 → extract、api |
| `extraction.py` | ExtractionRecord（**待建**） | extract → kit（留档） |
| `adjudication.py` | Adjudication、AdjudicationLog、MapUsagePort | kit → rebuild（反向注入） |
| `targetmap.py` | Concept、Proposition、TargetMap、Kit | kit → rebuild、score |
| `submission.py` | SubmittedProposition、Submission、Draft、模式枚举 | rebuild → score、quiz、export |
| `report.py` | ErrorChain、ScoreResult、四类错误枚举 | score → export |
| `quizsheet.py` | Question、Answer、QuizRecord、三时点枚举 | quiz → export |
| `exportcsv.py` | SubjectRow、QuestionRow、CsvPayload、UTF8_BOM | export → CSV 文件 |

冻结规则：契约被第二个 feature 消费即冻结；改动先给旧→新、影响范围、迁移方式，经用户确认。

## 本轮增量（全部有默认值，向后兼容）

| 契约 | 增量 | 用途 |
|---|---|---|
| `triple.TripleCandidate` | `evidence: str = ""` | 记录命题依据的原文片段，供裁定与追溯 |
| `targetmap.TargetMap` | `fingerprint: str = ""` | 区分同一教材在不同机器裁出的不同 kit |
| `extractconfig.ExtractConfig` | 新增整套 | 抽取配置；**不含密钥** |

## 命名注意

包化之前，契约文件与 feature 目录同名会让 import 解析错位（`quiz.py` 与 `quiz/`）。
包化后 `kbp.contracts.quizsheet` 与 `kbp.quiz` 天然隔离，**此问题不复存在**；
现有带后缀的名字（`quizsheet.py`）保留不改，避免触碰冻结契约。

## 反向依赖的处理

`kit` 要知道"版本是否已被学生用过"，但它不能 import `rebuild`。
解法是把这条能力写成 `MapUsagePort` 协议放在本目录，
由装配层把 `rebuild` 的实现注入给 `kit`——两边都不知道对方存在。

<!-- /@zone code -->
