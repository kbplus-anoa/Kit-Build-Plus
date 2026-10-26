<!-- @zone code -->

# rebuild — 任务

- [x] 契约 `Submission` 补齐关联键与 `Draft`
- [x] 零件校验（越界/自环/重复/超量）
- [x] 草稿落库（同键覆盖，可断电续做）
- [x] 提交落库并删除草稿，同场次不可重复
- [x] `usage` 实现 `MapUsagePort`，供 kit 自动判锁
- [ ] 重建画布：ReactFlow + 点-点连线 + 大 handle（暂不实现 GUI）
- [ ] 撤销/删除/快捷键与离开拦截（暂不实现 GUI）
- [ ] 双模式 UI 差异（暂不实现 GUI）
