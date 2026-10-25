<!-- @zone code -->

# kit — 索引
职责：人工裁定 → 冻结目标图 → 拆 kit。不评分、不渲染。

| 文件 | 内容 |
|---|---|
| `freeze.py` | `freeze(log, map_version)`：接受项凝固为目标图；概念按标签去重、按首次出现编号；越界连接词、空版本、无概念均报 `FreezeError` |
| `split.py` | `split(target)`：只留零件（概念集 + 连接词集），未被命题用到的零件不入 kit |
| `store.py` | SQLite 持久化：裁定表 + 词表表；同批次不可覆盖、词表不可静默改写 |
| `kit_service.py` | 编排入口：`adjudicate` / `freeze_batch` / `build_kit` / `load_batch` |
| `test/test_freeze.py` | 接受/驳回取出、编号顺序、去重、自环、越界词、空版本 |
| `test/test_split.py` | 零件过滤、连接词顺序、空图拒绝、kit 不含连接信息 |
| `test/test_store.py` | 写入读回、完整词表、批次不可覆盖、词表改写拒绝、重开可读 |
| `test/test_kit_service.py` | 落库到拆 kit 全流程、驳回项留档 | 

表结构（`store.py` 内 `SCHEMA`）：
- `vocab(vocab_id, vocab_version, connections)` —— 词表整份存 JSON，避免从用量反推而丢词
- `adjudication(batch_id, head, connection, tail, confidence, decision, reason)` —— 驳回项与接受项并存

<!-- /@zone code -->
