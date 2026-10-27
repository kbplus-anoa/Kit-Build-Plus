<!-- @zone code -->

# kit — 任务

- [x] 裁定契约（接受项与驳回项并存，理由留档）
- [x] 人工裁定路径 `freeze`
- [x] `split`：只留被命题用到的零件
- [x] `store`：裁定表 + 词表表，不可覆盖/改写
- [x] `lock`：已被学生用过即拒改（`MapUsagePort` 注入）
- [x] `_rules`：抽出两条路共用的冻结规则
- [x] `freeze_auto`：运行期自动路径
- [x] 内容指纹写入 `TargetMap.fingerprint`
- [x] 抽崩检测 S1–S4（阈值与触发文案已定）
- [x] `bank_store`：`target_map` 表落库，版本号与指纹唯一
- [x] 自动路先查题库，命中不重抽；未命中才登记新版本
- [x] 落库前过 `lock.assert_mutable`
- [ ] 人工裁定路 freeze 后落库（`/api/kit/build` 还缺 material_id）
- [ ] 自动路界面（暂不实现 GUI）

<!-- /@zone code -->
