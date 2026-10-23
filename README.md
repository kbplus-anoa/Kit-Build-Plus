<!-- @zone user -->

# kb-mixed

把 KB-Mixed（Prasetya / Hirashima / Hayashi 2019）两阶段概念图计算机化：
LLM 抽 goal map → 用户审核 → 裁 kit → 学生重建/扩展 → 命题级比对 → 评分报告（JSON + Markdown）。
单机 Web（FastAPI + vanilla JS），无数据库，全部 JSON 文件。

## 从哪开始读

| 你是 | 读 |
|---|---|
| 编码 agent | `AGENTS.md` → `docs/contract/SPEC.md` |
| 想懂为什么这么设计 | `memory-bank/`、`docs/adr/` |
| 想跑起来 | 下面「起服务」 |
| 想知道做到哪了 | `memory-bank/progress.md`、`docs/plan/ROADMAP.md` |

文档分层规则见 `docs/AGENTS.md`。**评分契约以 `docs/contract/SPEC.md` 为唯一真相。**

<!-- /@zone user -->
<!-- @zone code -->

## 起服务

```bash
cd ~/kb-mixed
.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8848
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8848/     # 期望 200
```

配置在 `config.yaml`；key 只在 `.env` 的 `KB_MIXED_LLM_KEY`（600 权限），不写进配置。

## 跑测试

```bash
cd ~/kb-mixed && .venv/bin/python -m pytest test/ -q
```

测试不调 LLM；真实 e2e 由 `KB_MIXED_E2E=1` 门控。

## 一次完整流程

```bash
# 1. 生成材料包（PDF / StudyMate 只读 / 手写）
curl -s -X POST http://127.0.0.1:8848/api/material/from-pdf \
  -H 'Content-Type: application/json' \
  -d '{"path":"/path/to/paper.pdf","title":"倾诉的力量"}'

# 2. 抽 goal map（LLM）
curl -s -X POST http://127.0.0.1:8848/api/goalmap -H 'Content-Type: application/json' \
  -d '{"run_id":"<run_id>"}'

# 3. 人工审核 + 裁 kit（未审核不得裁 kit）
curl -s -X POST http://127.0.0.1:8848/api/goalmap/<run_id>/review \
  -H 'Content-Type: application/json' -d '{"core":["n1","n2"]}'
curl -s -X POST http://127.0.0.1:8848/api/kit -H 'Content-Type: application/json' \
  -d '{"run_id":"<run_id>"}'

# 4. 提交学生图 → 评分
curl -s -X POST http://127.0.0.1:8848/api/attempt -H 'Content-Type: application/json' \
  -d '{"run_id":"<run_id>","graph":{"nodes":[],"edges":[]}}'
curl -s -X POST http://127.0.0.1:8848/api/score -H 'Content-Type: application/json' \
  -d '{"run_id":"<run_id>"}'
```

页面：`/`（首页）、`/review/{run_id}`（审核）、`/build/{run_id}?stage=rebuild|extend`、
`/report/{run_id}`（六板块 + 对照表 + 修正前后对比）。

<!-- /@zone code -->
<!-- @zone user -->

## 目录

```
src/            内核；模块 docstring 指向它落地的 SPEC 章节
src/adapters/   pdf / studymate（只读）/ manual
src/web/        模板（自写极简引擎）+ static
test/           pytest（命令见上）
scripts/        一次性脚本与文档事实来源（docs_numbers.py）
data/<run_id>/  运行产物：material / goalmap / kit / attempt / report / history / verdicts
tmp/            草稿与缓存，可随时删
docs/           按读者分层 → docs/AGENTS.md
memory-bank/    跨会话记忆六件套
specs/          复杂功能三件套
_forks/         文档方案试验副本，不参与运行
```

## 几个实现决定（细节见 docs/adr/）

- 模板引擎自写，不引 jinja2；依赖清单保持不变。
- FMS 只算重建阶段（扩展阶段的边没有参照分母）。
- 两次评分可复现：`tmp/cache/` 删掉也能复现同一 run，裁决结果归档在
  `data/<run_id>/verdicts/`。
- 安全边界：`GET /api/kit/{run_id}` 剥掉 `withheld` 与 `sections`，重建页拿不到 goal map。
- 报告措辞受实证约束：不出现结论性评价，只描述状态。

<!-- /@zone user -->
