<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 上一轮
- [x] 确定抽取引擎迁移：本机 UIE → DeepSeek API（BYOK），实测依据记入 README_PLAN 4.5
- [x] 确定目录重构：平铺 + sys.path → 单一包 `kbp/`
- [x] 确定运行期全自动裁 kit；人工裁定仅开发期
- [x] `AGENTS.md` 改完（Commands / 约定 / 文档结构 / 完成定义），经用户批准
- [x] 文档改写完成并经 subagent 三批只读核对：SPEC、README_PLAN 4.5、
      extract 四件、kit 四件、ingest、src 三件、ui-share 三件、
      rebuild/score/quiz/export 的 INDEX 与 DESIGN、契约索引
- [x] 契约新增 `ExtractConfig`（已实现并测试）；`evidence` / `fingerprint` 已在契约中

## 现在
- [ ] 契约 `ExtractionRecord` 落地 + 契约测试（当前只在索引里标"待建"）
- [ ] 重构第 1 步：建 `kbp/` 包骨架，旧目录暂留，测试保持全绿
- [ ] 重构第 2 步：迁移实现进包，删全部 `sys.path` 与 8 份 conftest
- [ ] 重构第 3 步：换抽取引擎、加自动冻结、加 config 与 kit/auto 路由
- [ ] 删 ONNX 资产：`onnx_uie.py`、`tmp/uie/` 449MB、`onnxruntime` 与 `tokenizers` 依赖
- [ ] 真实调用验证：填密钥跑一段教材，记录耗时与空 content 失败率
- [ ] 等用户：抽崩检测 S1–S4（自动裁后已从可选变必需）
- [ ] 等用户：`SPEC.md` §待决策 2 条（内容维度取值、TAM 中文量表条目）

<!-- /@zone code -->
