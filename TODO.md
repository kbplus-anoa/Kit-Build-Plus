<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 上一轮
- [x] `quiz`：题目/作答契约、判对、百分制、题套与逐题作答落库
- [x] `export`：被试级 21 列 + 题级 10 列，UTF-8 带 BOM，列宽校验
- [x] 契约 `exportcsv.py` 扩为 `SubjectRow` / `QuestionRow`，与 CSV_PLAN 逐列对齐
- [x] 端到端：作答 → 判分 → 两张 CSV 落盘（含 BOM 与中文列名验证）
- [x] 修掉 `quiz/` 与契约 `quiz.py` 同名导致的 import 冲突（契约改名 `quizsheet.py`）

## 现在
- [ ] 装配层：目前各 feature 靠测试里的路径拼接，缺一个真正的组装入口
- [ ] `src/` 路由：把 feature 暴露成 HTTP 接口（当前仍是最小骨架）
- [ ] `ui-share/` + 前端：0 行 UI，七步流程无法给学生用
- [ ] 等用户：是否现在动 `src/` 与 UI，还是先补 `score` 的抽崩检测（S1–S4）
- [ ] 等用户：`SPEC.md` §待决策 2 条（内容维度取值、TAM 中文量表条目）
- [ ] 等用户：扫描件云解析失败时中止还是降级为"无文本"

<!-- /@zone code -->
