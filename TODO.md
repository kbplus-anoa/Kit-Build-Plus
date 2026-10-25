<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 上一轮
- [x] `score`：命题级查表、四类错误链、分数与摘要
- [x] 四类判定顺序固定（reversed → leaving → excessive → lacking），保证一条错写只归一类
- [x] 契约 `ratio` / `ScoreResult` 落地为实际实现，分数只存分子分母
- [x] 全链路端到端：教材文本 → 抽取 → 裁定 → 冻结 → 拆 kit → 提交 → 评分

## 现在
- [ ] `export`：CSV 导出（两张表、UTF-8 带 BOM、单/多/全选）
- [ ] 等用户：`export` 是否需要界面（当前 0 行 UI），还是先只出后端函数
- [ ] 等用户：`ui-share/` 与 `src/` 路由层，何时动工
- [ ] 等用户：`SPEC.md` §待决策 2 条（内容维度取值、TAM 中文量表条目）
- [ ] 等用户：扫描件云解析失败时中止还是降级为"无文本"

<!-- /@zone code -->
