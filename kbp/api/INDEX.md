<!-- @zone code -->

# api — 索引
职责：HTTP 入口、请求/响应模型、依赖注入。**业务都在各 feature 里**。

包化后本目录是 `kbp/api/`，不再需要任何 `sys.path` 拼装。

| 文件 | 内容 |
|---|---|
| `main.py` | FastAPI 实例、路由挂载、`/` 与 `/api/health` |
| `deps.py` | 进程级数据库连接与写锁（两把锁分开，见下） |
| `bootstrap.py` | 建表装配：各 feature 的 `ensure` + 抽取配置表、阈值表、抽取留档表、导出快照表、教材登记表、量表作答表；库默认落在仓库根 `tmp/kb.sqlite3` |
| `schemas.py` | 通用请求/响应模型，只做格式约束，不含业务规则 |
| `schemas_tam.py` | TAM 量表的请求/响应模型，独立成文件以避开 200 行上限 |
| `config_store.py` | 抽取配置表（一行一条）的读写 |
| `routes_config.py` | `GET/PUT /api/config`：读写配置；**只回显密钥是否已配置** |
| `routes_text.py` | `/api/upload`（multipart 落盘→解析→登记教材，回正文）、`GET /api/materials`、`/api/ingest`、`/api/extract`、`/api/kit/auto`（先查题库，命中不重抽；`retry` 跳过复用要求重抽）；丢弃与整次抽取都落留档 |
| `routes_flow.py` | `/api/adjudicate`（开发期）、`/api/kit`、`/api/lock`、`/api/draft`、`/api/submit`（回提交序号、内容指纹、FMS 与四类错误明细，并落被试级快照） |
| `routes_kit.py` | `GET /api/kit/versions`（列出各批）、`POST /api/kit/use`（切回某一批） |
| `routes_data.py` | `/api/quiz`（落题级快照）、`GET /api/export/subject`、`GET /api/export/question`（三条件筛选，空即全选） |
| `routes_tam.py` | `GET /api/tam/items`、`POST /api/tam/answers`（整卷落库）、`GET /api/tam/alpha`（读库算） |

`/api/ingest` 失败码：文件不存在 404、格式不支持 400、
扫描件云端不可用（`MinerUUnavailable`）503、其它解析失败 502。

`/api/upload` 失败码：不支持的扩展名 400（提示 PDF/EPUB/TXT）、空文件 400、
解析不出正文 400、正文超 200 万字 413、文件超 40 MB 413、
扫描件云端不可用 503、其它解析失败 502；失败时删掉落盘文件。
同一份字节重复上传复用同一个 `material_id`，内容一变就新开一个。

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

自动路每次抽一条留档（批次号 `auto-*`）：配置快照、候选、丢弃、逐段原始输出与段数；
冻结成功后回填图版本与指纹，回填失败即 503。留档不进 CSV。

批次重抽与切回：`POST /api/kit/auto` 带 `retry: true` 时跳过题库复用另抽，
旧批不动；`GET /api/kit/versions?material_id=` 按入库先后列出各批（可再带
`vocab_version` 筛），`POST /api/kit/use` 把某一批标为投用，版本不存在返 404。
切回只标投用，学生用旧 `map_version` 继续草稿与提交，图不改不删。

导出：筛选条件走查询参数（`participant_id`、`material_id`、`time_point`，可重复给），
查不到记录返 404，行不合法返 400。组别 `condition` 在提交时必填（exp/con），
因为导出契约不允许空组别；未分组的提交直接 422，不在库里补默认值。

`/api/submit` 与 `/api/draft` 取图走 `_kit_for`：先按 `material_id` + `map_version` 查题库，
命中就直接用（自动路的图没有 `batch_id`），没命中才回退人工裁定批次。

TAM：`GET /api/tam/items` 出量表条目（六点上下限、判据、构念中文名、可选题）；
`POST /api/tam/answers` 收整卷落库（一人一题一行，重答覆盖），题号不在量表内
或同一份卷子同题两答返 400（原因里带题号），得分越界（不在 1–6）由本层模型返 422；
`GET /api/tam/alpha` 按构念算 α，数只来自库里的作答，缺答整人剔除。

`/api/extract` 的每条候选带 `confidence`（本地代理分，只用于排序）、`evidence`（逐字原文片段）与 `suspect`（概念过长等可疑项，不丢、排最后）。

`/api/kit/auto` 回 `possibly_inaccurate` + `message` + `signals` + `calibrated`：
每条信号带原值、阈值、是否触发；阈值取自 `quality_thresholds`，
没有校准就只带原值（阈值空、不触发、不提示）；命题太少时只记录不提示。

## 边界（不做什么）

不含业务规则、不渲染页面。前端位于**仓库根目录 `web/`**（Vite + React + TS），
不进 `kbp/` 包；页面设计由用户以 HTML 原型提供。

<!-- /@zone code -->
