<!-- @zone code -->

# src — 索引
职责：HTTP 入口、请求/响应模型、装配层。**业务都在 feature 里**，这里只做参数收口、
错误映射与依赖注入。

| 文件 | 内容 |
|---|---|
| `bootstrap.py` | 装配层：把 contract-share 与各 feature 目录接入 `sys.path`；把各 feature 的表建进同一个库 |
| `deps.py` | 进程级数据库连接与写锁（两把锁分开，见下） |
| `schemas.py` | 全部请求/响应模型，只做格式约束，不含业务规则 |
| `routes_text.py` | `/api/ingest`、`/api/extract` |
| `routes_flow.py` | `/api/adjudicate`、`/api/kit`、`/api/lock`、`/api/submit` |
| `routes_data.py` | `/api/quiz`、`/api/export/subject`、`/api/export/question` |
| `main.py` | FastAPI 实例、路由挂载、`/` 与 `/api/health` |
| `test/test_routes.py` | 用 TestClient 走真实 HTTP，每个用例独立 `:memory:` 库 |

## 为什么需要装配层

约定要求 feature 之间禁止 import 彼此，但**总得有人把它们拼起来**。
`bootstrap.py` 就是这个唯一的拼装点：它知道 `kit` 与 `rebuild` 共享一个库、
`rebuild` 的 `SubmissionUsage` 要注入给 `kit` 的锁定判定。
测试里那些临时拼 `sys.path` 的做法，靠这一层收敛。

## 两把锁为什么分开

`get_conn()` 与写操作都曾共用一把不可重入锁，导致路由先持写锁、再取连接时**自锁超时**。
现在：`_conn_lock`（可重入）只服务首次建连，`_write_lock`（可重入）串行化写入。
回归测试 `test_裁定不死锁` 钉住这条。

## 边界（不做什么）

不含业务规则、不直接 SQL（表结构在各 feature 的 store 里）、不渲染页面。
当前**无任何前端**：所有接口返回 JSON 或 CSV。

<!-- /@zone code -->
