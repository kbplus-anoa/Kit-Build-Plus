<!-- @zone code -->

# kit — 索引
职责：冻结目标图、拆 kit。**运行期全自动**；人工裁定路径只属开发期。

| 文件 | 内容 |
|---|---|
| `_rules.py` | **共用冻结规则**：命题去重、去自环、首次出现编号、内容指纹 |
| `freeze.py` | `freeze_auto(result, ver)`：运行期自动路；`freeze(log, ver)`：开发期人工路 |
| `split.py` | `split(target)`：只留零件，未被命题用到的零件不入 kit |
| `store.py` | SQLite：裁定表 + 词表表；同批次不可覆盖、词表不可静默改写 |
| `bank_store.py` | SQLite 题库 `target_map`：版本号与内容指纹唯一，概念/命题/词表整份存 |
| `lock.py` | 改图前门槛：已被学生用过即拒改（`MapUsagePort` 注入） |
| `kit_service.py` | 编排入口：`build_kit_auto` / `build_kit` / `adjudicate` / `bank_find` / `freeze_to_bank` / `history` / `use` |

## 两条路

```
运行期  ExtractionResult → freeze_auto → TargetMap → split → Kit
开发期  AdjudicationLog  → freeze      → TargetMap → split → Kit
                  └────────── _rules 共用 ──────────┘
```

**共用规则是硬要求**：两条路若各写一套，开发期评估结论不能迁移到运行期。
测试 `test_两条路对同一组命题给出相同指纹` 钉住这条。

## 内容指纹

`fingerprint` = 概念字面集合 + 命题三元组的 SHA-256 前 16 位，
**与编号无关、与输入顺序无关**，只认结构。

为什么需要它：同一教材在不同机器上自动裁 kit，可能得到不同概念与命题，
但版本号都叫 `v1`。群体统计前必须按 `map_version + fingerprint` 筛同一批人，
否则分母不同的人被混在一起算。

表结构：
- `vocab(vocab_id, vocab_version, connections)` —— 词表整份存，避免从用量反推而丢词
- `adjudication(batch_id, head, connection, tail, confidence, decision, reason)`
- `target_map(material_id, map_version, fingerprint, vocab_id, vocab_version, source, in_use, created_at, batch_id, connections, concepts, propositions)`

## 题库命中

命中条件是教材 + 词表版本：同教材同词表已有冻结图，直接复用，不再调模型。
未命中才抽取：冻结后先按内容指纹查重，同指纹回旧图，不新开版本；不同指纹才登记新版本。
期望版本号被占就往后排（v 号只区分第几版，同一张图靠指纹认）。
入库前过 `lock.assert_mutable`，已投用版本拒改。

## 重抽与切回

抽崩提示后学生可要求重抽：请求带 `retry`，跳过题库复用另抽一次。
重抽不覆盖旧批——同指纹仍回旧图，不同指纹登记新版本；旧批原样留着。

`history` 按入库先后列出该教材各批（版本、指纹、词表版本、来源、是否投用、
命题数），`use` 把某一批标为投用。切回旧批只是标投用，学生继续拿旧 `map_version`
走草稿与提交，图不改不删；同教材可先后有多个版本被投用，标记只增不减。

<!-- /@zone code -->
