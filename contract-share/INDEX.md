<!-- @zone code -->

# contract-share — 契约索引
只放契约：类型、字段语义、纯函数签名、Protocol。无实现、无 IO、无业务转换。

| 文件 | 契约域 | 提供方 → 消费方 |
|---|---|---|
| `textdoc.py` | TextDoc、IngestPort | ingest → extract、kit |
| `triple.py` | Vocab、TripleCandidate、ExtractionResult | extract → kit |
| `targetmap.py` | Concept、Proposition、TargetMap、Kit | kit → rebuild、score |
| `submission.py` | SubmittedProposition、Submission、模式枚举 | rebuild → score、export |
| `report.py` | ErrorChain、ScoreResult、四类错误枚举 | score → export |
| `exportcsv.py` | SubjectRow、CsvPayload、UTF8_BOM | export → CSV 文件 |

冻结规则：契约被第二个 feature 消费即冻结；改动先给旧→新、影响范围、迁移方式，经用户确认。

<!-- /@zone code -->
