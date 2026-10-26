<!-- @zone code -->

# extract — 任务

- [x] 词表读取与校验（缺字段、重复、空串、超量）
- [x] 长度上限截断与分段
- [x] OpenAI 兼容客户端（httpx 直调、密钥只从环境变量读、空 content 重试）
- [x] 提示词构造（含 json 字样与输出样例）
- [x] 输出规范化（越界/自环/重复丢弃，evidence 缺失降级）
- [x] 接到 `extract_service`：默认引擎改为 `ChatEngine`
- [x] 删除 ONNX：`onnx_uie.py`、`schema.py`、`tmp/uie/`
- [x] 留档：`ExtractionRecord` + 原文指纹
- [ ] 真实调用验证：耗时与空 content 失败率（需用户提供密钥）
- [ ] 真实调用后按实测调提示词与分段长度

<!-- /@zone code -->
