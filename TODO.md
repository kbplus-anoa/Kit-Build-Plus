<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 交接
**已验证**：`.venv/bin/python -m pytest` 274 passed、`flake8 .` 退出 0、
`GET /` 返 200、`GET/PUT /api/config` 正常、未配密钥时 `/api/kit/auto` 返 503 带中文原因。
真实调用已跑通：本机 OpenAI 兼容代理 `127.0.0.1:8788`，
`deepseek-v4.1-flash` 抽 8 句教材得 5 条、0 越界、耗时 31.85s。

**未完成**：见「未解决」。研究线（R 脚本、双人标注）本轮搁置。

**动手前读**：`kbp/extract/DESIGN.md`（数据流）、`kbp/kit/INDEX.md`（两条路与指纹）、
`SPEC.md` 已决策段。

**踩过的坑**：
1. `kbp/contracts/*` 是冻结契约，改动须先给「旧→新 / 影响范围 / 迁移方式」并经用户确认。
2. 新契约文件不得与 feature 子包同名。
3. `deps` 的连接锁与写锁必须分开，合并会自锁超时。
4. 导出表按列名取值测试，别用数字下标——加一列就全线错位。
5. flake8 上限是 AGENTS.md 的 100 列，配置在 `.flake8`；别按默认 79 改代码。
6. `base_url` 填到根（`http://127.0.0.1:8788`），代码自己拼 `/v1/chat/completions`；
   填成带 `/v1` 会变成 `/v1/v1/...`。
7. 密钥只走环境变量，不写进任何文件、日志、响应、commit。

## 上一轮
- [x] 抽取引擎换 OpenAI 兼容接口（开发期样例 DeepSeek）
- [x] 删 ONNX 三件与 `tmp/uie/`
- [x] 契约：`evidence`、`fingerprint`、`ExtractionRecord`、`ExtractPort`
- [x] `kit/_rules` 共用规则 + `freeze_auto` + 内容指纹
- [x] `api`：`/api/config`、`/api/kit/auto`
- [x] `export`：CSV 加 `fingerprint` 列

## 现在
- [ ] 前端：`web/` 脚手架已通，等用户提供 HTML 原型
- [ ] 研究线暂搁置：R 脚本真实数据、双人标注入口

## 未解决
> 已定方案，尚未动工。按阻断程度排序，逐条做完再往下。
> 研究线不在本节：用户已明确搁置。

- [ ] **目标图落库**：新开 `target_map` 表存冻结结果（版本+指纹+概念+命题），
      `/api/kit/auto` 返回 `target_map_id`，`/api/submit` 按它读图，不再经 `freeze_batch`
- [ ] 学习模式允许回改重交：`draft_store.submit` 对 `study` 放行重复提交，`test` 仍硬锁
- [ ] 草稿续做补 HTTP 入口：`POST/GET /api/draft`，接 `rebuild_service.save_draft`
- [ ] 导出改为服务端检索：按 `participant_id`/`material_id`/`session` 单/多/全选，前端不再自己攒数
- [ ] 夹具与记录落库：`ExtractionRecord` 写入 `extraction` 表，供事后追溯
- [ ] 锁真正生效：改图/换版本前调 `kit.lock.assert_mutable`，`/api/lock` 只是查询不够
- [ ] 学生重抽：记录并存不覆盖，旧批可切回
- [ ] TAM 量表：条目取自 `https://www.wjx.cn/vm/wEMzgZc.aspx`，**人口学题目除外**；
      六点 Likert，存 1–6，报各构念 Cronbach α（判据 0.7）
- [ ] 抽崩检测 S1–S4：孤立概念率、连接词覆盖率、概念集中度、基线偏离度
- [ ] 抽崩阈值先取：S1 > 0.30、S2 < 0.50、S3 > 0.60、S4 |Z| > 2.0（可跑后按实测定）
- [ ] 抽崩触发文案：`本次组件抽取可能不可信，您可重新抽取（{不可信的原因}）`
- [ ] 抽崩触发时存信号原值与阈值，照常计分，只加“可能不准”标记
- [ ] 云解析失败终止报错：MinerU 失败即抛错中止，不降级为“无文本”继续
- [ ] 解析结果缓存：同文件按内容指纹复用，不再重复付费，缓存不入 git
- [x] 供应商枚举改为「自定义 / OpenAI 兼容」，不写死 `deepseek`
- [x] 置信度改本地代理分：按 `evidence` 是否在原文逐字命中、位置是否一致打分；
      代理分负责排序，同分按首次出现顺序，输出稳定可复现
- [x] 提示词补一条：概念 = 名词或名词性短语（术语、实体、类别），不含谓语动词；
      一句话里找不到两个名词性概念就跳过这一句
- [x] 规范化硬规则一：`head`/`tail` 含词表内连接词 → 直接丢（塞了整个从句最强信号）
- [x] 规范化硬规则二：概念超长（> 20 字）→ 不丢，标记可疑并排到后面

<!-- /@zone code -->
