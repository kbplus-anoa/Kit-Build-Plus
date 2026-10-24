<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 上一轮
- [x] 建 `.env`（MinerU 令牌与路径），已确认被 git 忽略
- [x] 契约层六域 `contract-share/`，17 项测试全通过
- [x] `ingest` feature：格式判定 / txt / epub / pdf / MinerU 云通道
- [x] 装 `pypdf`（用户批准），消掉字体告警
- [x] 每次通过测试后故意失败一次，确认测试有效

## 现在
- [ ] `extract`：UIE 抽取，schema 即连接词表
- [ ] 等用户：PaddleNLP 2.8.1 在本机 Python 3.12 的兼容性是否要实测
- [ ] 等用户：扫描件云解析失败时中止还是降级为"无文本"
- [ ] `SPEC.md` §待决策 2 条（内容维度取值、TAM 中文量表条目）

<!-- /@zone code -->
