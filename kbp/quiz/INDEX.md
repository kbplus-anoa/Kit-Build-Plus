<!-- @zone code -->

# quiz — 索引
职责：题目、整卷作答、判对、百分制。**不导出**，导出归 `export`。

> 本 feature 不在 SPEC 原定七个之内。它存在的理由：题级 CSV 需要
> `question_id` / `答对` / `time_point` / `题型` / `内容维度`，
> 这些来自测验作答，若无本层则题级表只能是空壳。

| 文件 | 内容 |
|---|---|
| `grade.py` | `is_correct`（未作答算错）、`percent`（0–100，分母题数）、题干/题套校验 |
| `quiz_store.py` | SQLite：题套表 + 逐题作答表；同一 quiz_id 不可改写，同点同题可更新 |
| `tests/quiz/test_grade.py` | 判对、百分制、漏答、空卷、非法题目与非法作答 |
| `tests/quiz/test_quiz_store.py` | 题套读写、不可改写、逐题落库、时点隔离、重开可读 |

## 契约

`kbp/contracts/quizsheet.py`。

**命名由来**：包化之前 feature 目录与契约文件同名会让 `import quiz` 解析到目录；
包化后 `kbp.contracts.quizsheet` 与 `kbp.quiz` 天然隔离，此问题不复存在，
但文件名保留不改（契约变动须走冻结流程）。

- `Question`：题号、题干、选项、正确下标、题型、内容维度
- `Answer`：题号、所选下标（`-1` 表示未作答）、时点
- `QuizRecord`：整卷一行来源，带 `participant_id/material_id/session` 关联键

## 已定

- 只用客观单选（D30）
- 前测 / 后测 / 延迟后测**同一套题**，靠 `time_point` 区分
- `得分` 列仅主观题与 TAM 量表用，全单选时为 None

<!-- /@zone code -->
