<!-- @zone code -->

# api — 索引
职责：HTTP 入口、请求/响应模型、依赖注入。**业务都在各 feature 里**。

包化后本目录是 `kbp/api/`，不再需要任何 `sys.path` 拼装。

| 文件 | 内容 |
|---|---|
| `main.py` | FastAPI 实例、路由挂载、`/` 与 `/api/health` |
| `deps.py` | 进程级数据库连接与写锁（两把锁分开，见下） |
| `bootstrap.py` | 建表装配：各 feature 的 `ensure` + 抽取配置表；库默认落在仓库根 `tmp/kb.sqlite3` |
| `schemas.py` | 通用请求/响应模型，只做格式约束，不含业务规则 |
| `schemas_tam.py` | TAM 量表的请求/响应模型，独立成文件以避开 200 行上限 |
| `config_store.py` | 抽取配置表（一行一条）的读写 |
| `routes_config.py` | `GET/PUT /api/config`：读写配置；**只回显密钥是否已配置** |
| `routes_text.py` | `/api/ingest`、`/api/extract`、`/api/kit/auto`（先查题库，命中不重抽） |
| `routes_flow.py` | `/api/adjudicate`（开发期）、`/api/kit`、`/api/lock`、`/api/draft`、`/api/submit`（回提交序号、内容指纹、FMS） |
| `routes_data.py` | `/api/quiz`、`/api/export/subject`、`/api/export/question` |
| `routes_tam.py` | `GET /api/tam/items`、`POST /api/tam/alpha`（只算不存） |

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

`/api/submit` 与 `/api/draft` 取图走 `_kit_for`：先按 `material_id` + `map_version` 查题库，
命中就直接用（自动路的图没有 `batch_id`），没命中才回退人工裁定批次。

TAM：`GET /api/tam/items` 出量表条目（六点上下限、判据、构念中文名、可选题）；
`POST /api/tam/alpha` 按构念算 α，题号不在量表内返 400（原因里带题号），
得分越界（不在 1–6）由本层模型返 422。本层**只算不存**，作答落库等题级表。

`/api/extract` 的每条候选带 `confidence`（本地代理分，只用于排序）、`evidence`（逐字原文片段）与 `suspect`（概念过长等可疑项，不丢、排最后）。

`/api/kit/auto` 回 `possibly_inaccurate` + `message` + `signals`：
每条信号带原值、阈值、是否触发；触发才有文案，命题太少时只记录不提示。

## 边界（不做什么）

不含业务规则、不渲染页面。前端位于**仓库根目录 `web/`**（Vite + React + TS），
不进 `kbp/` 包；页面设计由用户以 HTML 原型提供。

<!-- /@zone code -->
