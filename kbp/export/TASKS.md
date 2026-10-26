<!-- @zone code -->

# export — 任务

- [x] 契约 `SubjectRow`（22 列）与 `QuestionRow`（10 列）
- [x] `to_csv`：UTF-8 带 BOM，空值空串，小数 8 位
- [x] 列宽校验、分子不超过分母
- [x] 导出层只做一次除法，不重跑评分
- [x] CSV 增加 `fingerprint` 列（乙方案下区分不同机器裁出的 kit）
- [x] 修正错误列名 `is_partice` → `is_practice`
- [ ] 导出页：筛选与预估条数（暂不实现 GUI）

<!-- /@zone code -->
