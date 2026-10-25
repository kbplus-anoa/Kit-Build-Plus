<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 上一轮
- [x] 契约补 `Submission` 关联键（被试/教材/场次）与 `Draft`
- [x] 契约加 `MapUsagePort` + `locked_by_usage`，kit 不反向依赖 rebuild
- [x] `rebuild`：零件校验、草稿落库、提交落库、草稿覆盖与提交后删除
- [x] `rebuild/usage.py` 实现 MapUsagePort，查提交表回答"是否被用过"
- [x] `kit/lock.py`：改图前门槛，锁定即拒改
- [x] 端到端：裁定 → 冻结 → 拆 kit → 提交 → 版本自动锁定

## 现在
- [ ] `score`：命题级查表、四类错误、报告（契约 `ScoreResult` 已就绪）
- [ ] 等用户：`score` 的四类错误是否需要给出每条错误链的置信度/来源
- [ ] 等用户：`SPEC.md` §待决策 2 条（内容维度取值、TAM 中文量表条目）
- [ ] 等用户：扫描件云解析失败时中止还是降级为"无文本"
- [ ] 等用户：`ui-share/` 与 `src/` 路由层何时动工（当前 0 行 UI）

<!-- /@zone code -->
