<!-- @zone code -->

# extract — 任务

- [x] 词表读取与校验（缺字段、重复、空串、超量）
- [x] 长度上限截断
- [x] DeepSeek 客户端（httpx 直调、密钥只从环境变量读、空 content 重试）
- [x] 提示词构造（含 json 字样与输出样例）
- [x] 输出规范化（越界/自环/重复丢弃，evidence 缺失降级）
- [ ] **接到 extract_service**：当前默认引擎仍是 ONNX
- [ ] 删除 ONNX：`onnx_uie.py`、`schema.py`、`tmp/uie/`
- [ ] 真实调用验证：耗时与空 content 失败率
