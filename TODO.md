<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 交接

开场：`阅读 AGENTS.md，完成任务`。AGENTS.md 是规则入口，本文件是任务入口。

现状（已验证，勿猜）：214 passed、flake8 退出 0、`GET /` 返 200。
后端在 `kbp/` 包，测试在 `tests/{feature}/`。

**未完成**：抽取引擎换 DeepSeek API（BYOK）。`deepseek_client.py` /
`deepseek_uie.py` / `prompt.py` 已写未接入；`extract_service.py` 仍用 ONNX。

**动手前读**：`README_PLAN.md` 4.5（为什么换）、`kbp/extract/DESIGN.md`（新数据流）。

**踩过的坑**：
1. 别用正则批量改 import——`from a import B, C` 会被拆成只剩 B。用 AST 或手工改。
2. `kbp/contracts/*` 是冻结契约，改动须先给「旧→新 / 影响范围 / 迁移方式」并经用户确认。
3. 新契约文件不得与 feature 子包同名。
4. `deps` 的连接锁与写锁必须分开，合并会自锁超时。

## 上一轮
- [x] 平铺 + sys.path → 单一包 `kbp/`
- [x] 测试集中到 `tests/{feature}/`，删全部 conftest
- [x] 文档迁入 `kbp/{feature}/`，AGENTS.md 同步
- [x] 契约增量：`evidence`、`fingerprint`、`ExtractConfig`

## 现在
- [ ] 接入 DeepSeek，删 ONNX 三件与 `tmp/uie/`
- [ ] `requirements.txt` 移除 `onnxruntime`、`tokenizers`
- [ ] 真实调用验证：填密钥跑一段教材，记录耗时与失败率
- [ ] 契约 `ExtractionRecord` + 落库
- [ ] `kit/_rules` 共用冻结规则 + `freeze_auto`
- [ ] `api`：`/api/config`、`/api/kit/auto`
- [ ] `export`：CSV 加 `fingerprint` 列
- [ ] 前端：`web/` 脚手架已通，等用户提供 HTML 原型
- [ ] 等用户：抽崩检测 S1–S4、SPEC 待决策 2 条

<!-- /@zone code -->
