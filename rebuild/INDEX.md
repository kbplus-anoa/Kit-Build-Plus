<!-- @zone code -->

# rebuild — 索引
职责：学生组装与提交。**不做任何评分或对错提示**。

| 文件 | 内容 |
|---|---|
| `rebuild_validate.py` | `check_against_kit`：只用 kit 内零件；越界概念/连接词、自环、重复、超量均拒绝 |
| `draft_store.py` | SQLite：草稿表 + 提交表；草稿可覆盖，提交后草稿删除，同场次不可重复提交 |
| `usage.py` | 实现 `MapUsagePort`：查提交表回答"某版本是否已被学生用过" |
| `rebuild_service.py` | 编排入口：`save_draft` / `submit`，落库前一律先校验 |

## 与 kit 的关系

`rebuild` 不 import `kit`，只消费 `contract-share/targetmap.py` 的 `Kit`。
`kit` 需要知道版本是否锁定，但它也不能 import `rebuild`——
装配层把 `usage.SubmissionUsage` 注入 `kit/lock.py`，两边都不知道对方存在。

## 草稿语义（已定：落库）

- 键是 `(participant_id, material_id, session)`
- 同一键反复保存＝覆盖，学生可断电、关页面后继续
- 提交成功后草稿被删除，此后既不能再存草稿也不能重复提交

<!-- /@zone code -->
