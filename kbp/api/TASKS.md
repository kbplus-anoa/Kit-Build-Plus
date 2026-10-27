<!-- @zone code -->

# api — 任务

- [x] 包化：取消 `sys.path` 拼装
- [x] 两把锁分开（连接锁与写锁），修掉路由自锁
- [x] `/api/ingest`、`/api/extract`
- [x] `/api/adjudicate`、`/api/kit`、`/api/lock`、`/api/submit`
- [x] `/api/quiz`、两张 CSV 导出
- [x] `/` 与 `/api/health`
- [x] `GET/PUT /api/config`：读写抽取配置，只回显密钥是否已配置
- [x] `POST /api/kit/auto`：先查题库，命中直接复用；未命中才抽取 → 冻结 → 登记新版本 → 拆 kit
- [x] `/api/submit` 回提交序号与内容指纹；测验模式同一键重复提交返 409
- [ ] 前端对接（等用户提供 HTML 原型）

<!-- /@zone code -->
