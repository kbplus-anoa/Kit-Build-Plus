<!-- @zone code -->

# quiz — 索引
职责：题目、整卷作答、判对、百分制，另含 **TAM 量表条目与各构念 Cronbach α**。**不导出**，导出归 `export`。

> 本 feature 不在 SPEC 原定七个之内。它存在的理由：题级 CSV 需要
> `question_id` / `答对` / `time_point` / `题型` / `内容维度`，
> 这些来自测验作答，若无本层则题级表只能是空壳。

| 文件 | 内容 |
|---|---|
| `grade.py` | `is_correct`（未作答算错）、`percent`（0–100，分母题数）、题干/题套校验 |
| `quiz_store.py` | SQLite：题套表 + 逐题作答表，作答表键为四元关联键 + 题号；同一 quiz_id 不可改写，同键同题可更新 |
| `scale.py` | TAM 14 题条目表（逐字原文），`items_of` / `item_ids` |
| `alpha.py` | `cronbach_alpha`（样本方差口径）、`alpha_by_construct`（缺答整人剔除） |
| `tests/quiz/test_grade.py` | 判对、百分制、漏答、空卷、非法题目与非法作答 |
| `tests/quiz/test_quiz_store.py` | 题套读写、不可改写、逐题落库、时点隔离、重开可读 |
| `tests/quiz/test_scale.py` | 14 题、题号唯一、构念题数、ATT 可选、不收人口学题 |
| `tests/quiz/test_alpha.py` | 与 R 的 `psych::alpha` 对照、样本方差、缺答剔除、判据 |

## 契约

`kbp/contracts/quizsheet.py`。

**命名由来**：包化之前 feature 目录与契约文件同名会让 `import quiz` 解析到目录；
包化后 `kbp.contracts.quizsheet` 与 `kbp.quiz` 天然隔离，此问题不复存在，
但文件名保留不改（契约变动须走冻结流程）。

- `Question`：题号、题干、选项、正确下标、题型、内容维度
- `Answer`：题号、所选下标（`-1` 表示未作答）、时点
- `QuizRecord`：整卷一行来源，带 `participant_id/material_id/time_point/submit_seq` 关联键

## 已定

- 只用客观单选（D30）
- 前测 / 后测 / 延迟后测**同一套题**，靠 `time_point` 区分
- `得分` 列仅主观题与 TAM 量表用，全单选时为 None
- TAM 用**六点** Likert（1 强不同意 … 6 强同意），源问卷自称五点，只取题目不取锚点
- 量表来源 `https://www.wjx.cn/vm/wEMzgZc.aspx`，**人口学两题不收**；态度 ATT 标为可选
- α 判据 0.7，按构念分别报；缺一题的人整人剔除

## 为什么 TAM 条目与 α 落在 quiz

TAM 的作答本来就落在题级长表里（CSV_PLAN H.5：`得分` 列存 1–6，时点为后测）。
α 只能从作答算，条目与算法若另起一个 feature，
就会出现"存一份、算一份"两处口径，迟早对不上——所以条目表与 α 跟作答同层。
本 feature 只管**算**，作答落库仍等做题表（见 TODO）。

<!-- /@zone code -->
