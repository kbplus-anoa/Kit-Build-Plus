<!-- @zone code -->

# quiz — 任务

- [x] 契约 `Question`/`Answer`/`QuizRecord`，三时点与题型枚举
- [x] 判对（未作答算错），规则只此一份
- [x] 百分制 0–100
- [x] 题套与逐题作答落库，同题套不可改写
- [x] TAM 量表条目表 14 题（PU 4 / PEOU 4 / BI 3 / ATT 3 可选）
- [x] 契约 `ScaleItem` / `AlphaReport` / `alpha_by_construct` 签名
- [x] Cronbach α：样本方差口径，与 R `psych::alpha` 对照一致
- [x] 按构念分别报 α、缺答整人剔除、判据 0.7
- [ ] TAM 作答落库：等题级作答表（与「夹具与记录落库」同批）
- [ ] 量表页：条目由 `GET /api/tam/items` 出，页面原型待用户提供（暂不实现 GUI）
- [ ] 测验页：一屏一题、三时点同版式（暂不实现 GUI）
- [ ] 提交前未答清单与断线恢复（暂不实现 GUI）
