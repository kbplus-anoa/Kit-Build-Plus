<!-- @zone code -->

# api — 索引
职责：HTTP 入口、请求/响应模型、依赖注入。**业务都在各 feature 里**。

包化后本目录是 `kbp/api/`，不再需要任何 `sys.path` 拼装。

| 文件 | 内容 |
|---|---|
| `main.py` | FastAPI 实例、路由挂载、`/` 与 `/api/health` |
| `deps.py` | 进程级数据库连接与写锁（两把锁分开，见下） |
| `bootstrap.py` | 建表装配：各 feature 的 `ensure` + 抽取配置表、阈值表、抽取留档表、导出快照表、教材登记表、量表作答表；库默认落在仓库根 `tmp/kb.sqlite3` |
| `envfile.py` | 启动时把仓库根 `.env` 补进环境变量（已存在的变量优先；`KBP_ENV_FILE` 可指到别处），读配置时再重读一次，改文件不用重启 |
| `schemas.py` | 通用请求/响应模型，只做格式约束，不含业务规则 |
| `schemas_tam.py` | TAM 量表的请求/响应模型，独立成文件以避开 200 行上限 |
| `config_store.py` | 抽取配置表（一行一条）的读写；库里没保存过时按 `.env` 的 `KBP_EXTRACT_*` 出默认值 |
| `routes_config.py` | `GET/PUT /api/config`：读写配置；**只回显密钥是否已配置** |
| `kit_flow.py` | 运行期裁 kit 的编排：题库命中、切段预报、逐段进度回调、后台任务与结果封装 |
| `upload_flow.py` | 上传侧公共步骤：扩展名校验与落盘解析（失败即删文件） |
| `routes_text.py` | `/api/upload`（multipart 落盘→解析→登记教材，回正文）、`GET /api/materials`（只列已抽出 kit 的教材）、`DELETE /api/materials/{id}`（删登记与原文，失败上传回滚用）、`GET /api/materials/{id}/text`（按落盘文件重读旧教材正文，命中解析缓存）、`/api/ingest`、`/api/extract`、`/api/kit/preview`（切段预报）、`/api/kit/auto`（先查题库，命中不重抽；`retry` 跳过复用要求重抽）、`POST /api/kit/jobs` + `GET /api/kit/jobs/{id}`（后台抽，带真实段进度）；丢弃与整次抽取都落留档 |
| `routes_flow.py` | `/api/adjudicate`（开发期）、`/api/kit`、`/api/lock`、`/api/draft`、`/api/submit`（回提交序号、内容指纹、FMS、四类错误明细与目标命题，并落被试级快照） |
| `record_flow.py` | 历史提交与草稿：按当前目标图重算报告、列出某人的提交与草稿、读写当前草稿 |
| `routes_records.py` | `GET /api/records`（某人提交，可按教材筛）、`GET /api/drafts`、`GET/POST /api/draft/current`（当前草稿，序号服务端分配） |
| `routes_kit.py` | `GET /api/kit/versions`（列出各批）、`POST /api/kit/use`（切回某一批） |
| `routes_data.py` | `/api/quiz`（落题级快照）、`GET /api/export/subject`、`GET /api/export/question`（三条件筛选，空即全选） |
| `routes_tam.py` | `GET /api/tam/items`、`POST /api/tam/answers`（整卷落库）、`GET /api/tam/alpha`（读库算） |

`/api/ingest` 失败码：文件不存在 404、格式不支持 400、
扫描件云端不可用（`MinerUUnavailable`）503、其它解析失败 502。

`/api/upload` 失败码：不支持的扩展名 400（提示 PDF/EPUB/TXT）、空文件 400、
解析不出正文 400、正文超 200 万字 413、文件超 40 MB 413、
扫描件云端不可用 503、其它解析失败 502；失败时删掉落盘文件。
同一份字节重复上传复用同一个 `material_id`，内容一变就新开一个。

`/api/kit/preview` 只回 `segments`（按当前 `max_chars` 切几段）与 `chars`，不落库、不发模型请求。
`POST /api/kit/jobs` 开后台任务，`GET /api/kit/jobs/{id}` 回
`state`（running/done/failed）、`segments`/`done`（真实段进度）与 `result`（同 `/api/kit/auto`）；
失败时 `error` 的文案与同步路由一致。任务在内存里，进程重启即丢；只留最近 12 个已结束的。
模型请求只在后台线程里发，前端可以随时离开页面。

## 记录只认库

刷新、换设备、重开复盘都读后端：`GET /api/records` 把提交表逐条按当前目标图重算
（分数、四类错误、目标命题），图取不到时 `scored=false`，只回学生原图。
`GET /api/drafts` 与 `GET /api/draft/current` 供「继续」栏；当前草稿按四元键覆盖，
序号由服务端 `next_seq` 给，前端不必知道是第几次。
测验模式提交后再交返 409，但那份提交仍在记录里，可以据此重开报告。

## 两把锁为什么分开

`get_conn()` 与写操作曾共用一把不可重入锁，导致路由先持写锁、再取连接时**自锁超时**。
现在：`_conn_lock`（可重入）只服务首次建连，`_write_lock`（可重入）串行化写入。
回归测试 `test_裁定不死锁` 钉住这条。

## 密钥的处理

- 只从环境变量读取（统一走 `KBP_API_KEY`；协议只有一套 OpenAI 兼容）
- `/api/config` 的响应只含 `has_key: bool` 与 `key_env: str`，
  **不返回密钥本身、不返回前后缀**
- 日志与异常信息里不出现密钥
- 模型与地址可写在仓库根 `.env`：`KBP_EXTRACT_MODEL`、`KBP_EXTRACT_BASE_URL`、
  `KBP_EXTRACT_TIMEOUT_S`、`KBP_EXTRACT_MAX_CHARS`、`KBP_EXTRACT_ENABLED`；
  设置页保存过的值优先于 `.env`
- 读配置时会重读 `.env`，改完不用重启；只覆盖上次由文件写入的键，shell 里已设的变量仍优先

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
