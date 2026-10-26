<!-- @zone code -->

# api（原 src/）— 索引
职责：HTTP 入口、请求/响应模型、依赖注入。**业务都在各 feature 里**。

包化后本目录是 `kbp/api/`，不再需要任何 `sys.path` 拼装（`bootstrap.py` 已删）。

| 文件 | 内容 |
|---|---|
| `main.py` | FastAPI 实例、路由挂载、`/` 与 `/api/health` |
| `deps.py` | 进程级数据库连接与写锁（两把锁分开，见下） |
| `schemas.py` | 全部请求/响应模型，只做格式约束，不含业务规则 |
| `routes_text.py` | `/api/ingest`、`/api/extract` |
| `routes_flow.py` | `/api/adjudicate`（开发期）、`/api/kit`、`/api/kit/auto`、`/api/lock`、`/api/submit` |
| `routes_data.py` | `/api/quiz`、`/api/export/subject`、`/api/export/question` |
| `routes_config.py` | `GET/PUT /api/config`：读写抽取配置；**只回显密钥是否已配置，绝不回显密钥** |

## 两把锁为什么分开

`get_conn()` 与写操作曾共用一把不可重入锁，导致路由先持写锁、再取连接时**自锁超时**。
现在：`_conn_lock`（可重入）只服务首次建连，`_write_lock`（可重入）串行化写入。
回归测试 `test_裁定不死锁` 钉住这条。

## 密钥的处理

- 只从环境变量 `DEEPSEEK_API_KEY` 读取
- `/api/config` 的响应只包含 `has_key: bool`，**不返回密钥本身、不返回前后缀**
- 日志与异常信息里不出现密钥

## 边界（不做什么）

不含业务规则、不直接 SQL（表结构在各 feature 的 store 里）、不渲染页面。
前端位于**仓库根目录 `web/`**（Vite + React + TS），不进 `kbp/` 包；
页面设计由用户以 HTML 原型提供。

<!-- @zone code -->
