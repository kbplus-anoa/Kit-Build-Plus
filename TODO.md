<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 上一轮
- [x] `kit`：裁定契约 + 冻结 + 拆 kit + SQLite 留档（方案 2）
- [x] 契约新增 `adjudication.py`：Adjudication / AdjudicationLog / freeze / is_locked
- [x] `kit` 三个纯函数模块：freeze / split / store，加编排入口
- [x] 驳回项与接受项一并落库，词表整份存，不从用量反推
- [x] 拆 kit 只给被命题用到的零件，避免空白干扰项

## 现在
- [ ] `rebuild`：学生组装与提交（契约 `Submission` 已就绪）
- [ ] 等用户：`rebuild` 的草稿保存要不要落库（还是只存内存）
- [ ] 等用户：`is_locked` 的"学生用过"如何判定——查提交表还是人工标记
- [ ] 等用户：`SPEC.md` §待决策 2 条（内容维度取值、TAM 中文量表条目）
- [ ] 等用户：扫描件云解析失败时中止还是降级为"无文本"

<!-- /@zone code -->
