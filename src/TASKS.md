<!-- @zone code -->

# src — 任务
一项一个可验证的完成态。用户授权前不勾选。

## 里程碑

- [ ] `bootstrap`：paths 装配 + 七张表建进同一个库
- [ ] `deps`：连接复用；连接锁与写锁分开，允许持锁取连接
- [ ] `/api/ingest`：本地路径→纯文本，扫描件走 MinerU
- [ ] `/api/extract`：文本+词表→候选三元组（ONNX UIE 真跑通）
- [ ] `/api/adjudicate`、`/api/kit`、`/api/lock`、`/api/submit`
- [ ] `/api/quiz`：题套+作答落库并返回百分制
- [ ] `/api/export/subject`、`/api/export/question`：两张 CSV 带 BOM
- [ ] `/` 与 `/api/health`：存活与表数自检
- [ ] 路由测试含死锁回归（`test_裁定不死锁`）
- [ ] 前端工程（Vite + React + TS + ReactFlow）接入（**未开始**）

<!-- /@zone code -->
