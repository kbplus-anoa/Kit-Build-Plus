<!-- @zone code -->

# kit — 索引
职责：冻结目标图、拆 kit。**运行期全自动**；人工裁定路径只属开发期。

| 文件 | 内容 |
|---|---|
| `_rules.py` | **共用冻结规则**：概念去重编号、命题去重、去自环、内容指纹 |
| `freeze.py` | `freeze_auto(result, map_version)`：运行期自动路；`freeze(log, ver)`：开发期人工路 |
| `split.py` | `split(target)`：只留零件，未被命题用到的零件不入 kit |
| `store.py` | SQLite：裁定表 + 词表表；同批次不可覆盖、词表不可静默改写 |
| `lock.py` | 改图前门槛：已被学生用过即拒改（`MapUsagePort` 注入） |
| `kit_service.py` | 编排入口：`build_kit_auto` / `build_kit` / `adjudicate` |

## 两条路

```
运行期  ExtractionResult → freeze_auto → TargetMap → split → Kit
开发期  AdjudicationLog  → freeze      → TargetMap → split → Kit
                  └────────── _rules 共用 ──────────┘
```

**共用规则是硬要求**：两条路若各写一套，开发期评估结论不能迁移到运行期。

表结构：
- `vocab(vocab_id, vocab_version, connections)` —— 词表整份存，避免从用量反推而丢词
- `adjudication(batch_id, head, connection, tail, confidence, evidence, decision, reason)`

<!-- @zone code -->
