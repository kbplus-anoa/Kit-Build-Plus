<!-- @zone code -->

# contract-share — 契约索引
只放契约：类型、字段语义、纯函数签名、Protocol。无实现、无 IO、无业务转换。

| 文件 | 契约域 | 提供方 → 消费方 |
|---|---|---|
| `textdoc.py` | TextDoc、IngestPort | ingest → extract、kit |
| `triple.py` | Vocab、TripleCandidate、ExtractionResult | extract → kit |
| `adjudication.py` | Adjudication、AdjudicationLog、MapUsagePort | kit → rebuild（反向注入） |
| `targetmap.py` | Concept、Proposition、TargetMap、Kit | kit → rebuild、score |
| `submission.py` | SubmittedProposition、Submission、Draft、模式枚举 | rebuild → score、quiz、export |
| `report.py` | ErrorChain、ScoreResult、四类错误枚举 | score → export |
| `quizsheet.py` | Question、Answer、QuizRecord、三时点枚举 | quiz → export |
| `exportcsv.py` | SubjectRow、QuestionRow、CsvPayload、UTF8_BOM | export → CSV 文件 |

冻结规则：契约被第二个 feature 消费即冻结；改动先给旧→新、影响范围、迁移方式，经用户确认。

## 命名注意

契约文件名**不得与 feature 目录同名**：`quiz` 契约曾叫 `quiz.py`，
与 `quiz/` 目录冲突，`import quiz` 会解析到目录而非契约文件。
现名 `quizsheet.py`。新增契约时先查有无同名目录。

## 反向依赖的处理

`kit` 要知道"版本是否已被学生用过"，但它不能 import `rebuild`。
解法是把这条能力写成 `MapUsagePort` 协议放在本目录，
由装配层把 `rebuild` 的实现注入给 `kit`——两边都不知道对方存在。

<!-- /@zone code -->
