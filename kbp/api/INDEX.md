<!-- @zone code -->

# api — 索引
职责：HTTP 入口、请求/响应模型、依赖注入。**业务都在各 feature 里**。

包化后本目录是 `kbp/api/`，不再需要任何 `sys.path` 拼装。

| 文件 | 内容 |
|---|---|
| `main.py` | FastAPI 实例、路由挂载、`/` 与 `/api/health` |
| `deps.py` | 进程级数据库连接与写锁（两把锁分开，见下） |
| `bootstrap.py` | 建表装配：各 feature 的 `ensure` + 抽取配置表 |
| `schemas.py` | 全部请求/响应模型，只做格式约束，不含业务规则 |
| `config_store.py` | 抽取配置表（一行一条）的读写 |
| `routes_config.py` | `GET/PUT /api/config`：读写配置；**只回显密钥是否已配置** |
| `routes_text.py` | `/api/ingest`、`/api/extract`、`/api/kit/auto` |
| `routes_flow.py` | `/api/adjudicate`（开发期）、`/api/kit`、`/api/lock`、`/api/submit` |
| `routes_data.py` | `/api/quiz`、`/api/export/subject`、`/api/export/question` |

`/api/ingest` 失败码：文件不存在 404、格式不支持 400、
扫描件云端不可用（`MinerUUnavailable`）503、其它解析失败 502。

## 两把锁为什么分开

`get_conn()` 与写操作曾共用一把不可重入锁，导致路由先持写锁、再取连接时**自锁超时**。
现在：`_conn_lock`（可重入）只服务首次建连，`_write_lock`（可重入）串行化写入。
回归测试 `test_裁定不死锁` 钉住这条。

## 密钥的处理

- 只从环境变量读取（统一走 `KBP_API_KEY`；协议只有一套 OpenAI 兼容）
- `/api/config` 的响应只含 `has_key: bool` 与 `key_env: str`，
  **不返回密钥本身、不返回前后缀**
- 日志与异常信息里不出现密钥

## 自动路与人工路的接口分工

| 路 | 接口 | 是否需要人 |
|---|---|---|
| 运行期 | `POST /api/kit/auto`：文本 → 抽取 → 冻结 → 拆零件 | 否 |
| 开发期 | `POST /api/adjudicate` → `POST /api/kit` | 是（逐条裁定） |

自动路返回 `fingerprint`，导出与统计按它筛同一批人。

`/api/extract` 的每条候选带 `confidence`（本地代理分，只用于排序）、`evidence`（逐字原文片段）与 `suspect`（概念过长等可疑项，不丢、排最后）。

## 边界（不做什么）

不含业务规则、不渲染页面。前端位于**仓库根目录 `web/`**（Vite + React + TS），
不进 `kbp/` 包；页面设计由用户以 HTML 原型提供。

<!-- /@zone code -->
