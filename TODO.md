<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 上一轮
- [x] 提交上一轮改动（类型 docs；prompt: 文档基线定稿）
- [x] 建 `requirements.txt`（版本均在本机 .venv 跑过）
- [x] 建 `contract-share/`：一域一文件，六域 ingest/extract/kit/rebuild/score/export
- [x] 契约测试一并通过，且故意失败一次确认有效
- [x] 修正 `SPEC.md` 的 feature 计数行
- [x] 最小服务骨架 `src/main.py`，`GET /` 返 200

## 现在
- [ ] 等用户：`SPEC.md` §待决策 2 条（内容维度取值、TAM 中文量表条目）
- [ ] 等用户：是否建七个 `{feature}/{WHY,DESIGN,TASKS}.md` 与 `{feature}/INDEX.md`
- [ ] 等用户：是否建 `docs/PROGRESS.md`（现仅有 .tpl）
- [ ] 等用户：`AGENTS.md` 完成定义里仍写 `{测试代码待定}`，是否改为 pytest 退出码 0
- [ ] 等用户：确认扫描 PDF 解析走 MinerU 云需 `.env` 里的密钥名
- [ ] 契约测试补：`ui-share/` 边界与 `src/` 路由约定

<!-- /@zone code -->
