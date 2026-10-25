<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 上一轮
- [x] `ingest`：格式判定 / txt / epub / pdf / MinerU 云四步（真实跑通，11855 字）
- [x] `extract`：词表、schema、窗口、ONNX UIE 引擎、去重排序
- [x] 选 B：弃 paddlenlp，换 ONNX 运行时（依赖 1.7GB → 22MB）
- [x] ONNX 权重转换 + 修复 dynamo 导出器导致数值错误
- [x] 删除 `uie.py`，默认引擎改 ONNX，真实抽取 6 条命题
- [x] `.env` 建好并确认被 git 忽略；MinerU token 由用户填写

## 现在
- [ ] `kit`：人工裁定 + 冻结 + 拆 kit
- [ ] `kit` 里程碑需先定：裁定结果如何存（表结构）
- [ ] 等用户：`SPEC.md` §待决策 2 条（内容维度取值、TAM 中文量表条目）
- [ ] 等用户：扫描件云解析失败时中止还是降级为"无文本"

<!-- /@zone code -->
