<!-- @zone code -->

# rebuild — 任务

- [x] 契约 `Submission` 补齐关联键与 `Draft`
- [x] 零件校验（越界/自环/重复/超量）
- [x] 草稿落库（同键覆盖，可断电续做）
- [x] 提交落库并删除草稿；测验模式同一四元键不可重复，学习模式可换序号重交
- [x] 关联键改四元（时点 + 提交序号），草稿表与提交表同键
- [x] 提交记录带目标图内容指纹
- [x] `load_draft` 供路由层按四元键读回草稿（POST/GET `/api/draft`）
- [x] `usage` 实现 `MapUsagePort`，供 kit 自动判锁
- [ ] 重建画布：ReactFlow + 点-点连线 + 大 handle（暂不实现 GUI）
- [ ] 撤销/删除/快捷键与离开拦截（暂不实现 GUI）
- [ ] 双模式 UI 差异（暂不实现 GUI）
