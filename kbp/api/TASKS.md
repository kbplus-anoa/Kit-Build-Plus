<!-- @zone code -->

# api（原 src/）— 任务
一项一个可验证的完成态。用户授权前不勾选。

## 里程碑

- [ ] 包化：本目录成为 `kbp/api/`，删 `bootstrap.py`，取消所有 `sys.path` 拼装
- [ ] `deps`：连接复用；连接锁与写锁分开，允许持锁取连接
- [ ] `/api/ingest`：本地路径→纯文本，扫描件走 MinerU
- [ ] `/api/extract`：文本+词表+配置→候选三元组（云端模型）
- [ ] `GET /api/config`、`PUT /api/config`：读写抽取配置；**只回显密钥是否已配置**
- [ ] `POST /api/kit/auto`：文本→自动抽取→自动冻结→拆 kit（运行期主路径）
- [ ] `POST /api/adjudicate`：保留，文档标注「开发期专用」
- [ ] `/api/kit`、`/api/lock`、`/api/submit`
- [ ] `/api/quiz`：题套+作答落库并返回百分制
- [ ] `/api/export/subject`、`/api/export/question`：两张 CSV 带 BOM
- [ ] `/` 与 `/api/health`：存活与表数自检
- [ ] 路由测试含死锁回归（`test_裁定不死锁`）与密钥不外泄断言

<!-- @zone code -->
