<!-- @zone code -->

# TODO — kb-mixed
任务版，只留两轮。每轮整体重写。复选框可由 agent 勾选。

## 交接

已验证：.venv/bin/python -m pytest 483 passed；.venv/bin/python -m flake8 . 退出 0；GET / 返 200。
真实调用已跑通：本机 OpenAI 兼容代理 127.0.0.1:8788，deepseek-v4.1-flash，8 句教材得 5 条、0 越界、31.85s。
TAM 已通：POST /api/tam/answers 整卷落库，GET /api/tam/alpha 从库算 α。

未完成：见未解决。研究线（R 脚本、双人标注、docs/research）不在本板。

动手前读：SPEC.md 决策段 D01–D12、kbp/extract/DESIGN.md、kbp/kit/INDEX.md。

踩过的坑：
1 契约冻结，改前给旧→新、影响范围、迁移方式，等用户确认
2 新契约文件不得与 feature 子包同名
3 deps 的连接锁与写锁必须分开，合并会自锁超时
4 导出表按列名取值测试，别用数字下标
5 flake8 上限 100 列，配置在 .flake8
6 base_url 填到根，代码自己拼 /v1/chat/completions
7 密钥只走环境变量，不进文件、日志、响应、commit
8 测完服务用 fuser -k 端口/tcp；pkill -f uvicorn 会连承载 shell 一起杀掉
9 pydantic 字段名不能叫 construct，会与 BaseModel 自带方法撞名
10 变异验证后必须删 __pycache__：改回同长度的源码若落在同一秒，pyc 被认为有效，跑的还是旧代码

## 上一轮

- [x] 抽取引擎换 OpenAI 兼容接口，供应商枚举不写死厂商
- [x] 置信度改本地代理分，概念塞连接词与超长概念两条硬规则
- [x] 抽崩检测 S1–S4 与提示文案
- [x] 扫描件云端解析失败即中止报错
- [x] TAM 量表 14 题与各构念 Cronbach α
- [x] kit 共用冻结规则 + freeze_auto + 内容指纹
- [x] /api/config、/api/kit/auto、/api/tam/items、/api/tam/alpha
- [x] 导出加 fingerprint 列

## 未解决

### 阶段 0 等用户确认，阻塞后续

- [x] 关联键改四元：被试标识 + 教材 + 时点 + 提交序号（D09）。已直接换库，不写迁移。
      旧 participant_id + material_id + session；新 participant_id + material_id + time_point + submit_seq。
      影响 kbp/contracts/submission.py、quizsheet.py、exportcsv.py；kbp/rebuild/draft_store.py、
      rebuild_service.py、rebuild_validate.py；kbp/quiz/quiz_store.py、grade.py；kbp/api/schemas.py；
      kbp/export/subject_table.py、question_table.py；两处 store 表主键与全部相关测试。需换库或写迁移。
- [x] FMS 改 0–100（D04）。旧 ratio 返回 0–1，新 × 100。
      影响 kbp/contracts/report.py、kbp/score/score_service.py、kbp/export/subject_table.py、ScoreOut 与相关测试。
- [x] 重建提交的时点取值：保留 pre / post / delayed 三种（用户定）。

### 阶段 1 契约（一个契约域一次提交，先契约测试后实现）

- [x] 落 D09 四元关联键
- [x] 落 D04 FMS 0–100
- [x] 新契约 targetbank：按教材与词表版本登记、按内容指纹查已冻结目标图
- [x] extraction 契约补存储语义

### 阶段 2 kit 落库与题库命中

- [x] target_map 表落库：版本、指纹、概念、命题、来源批次、创建时间、是否投用
- [x] /api/kit/auto 先查题库（教材 + 词表版本），命中直接复用，不再重抽
- [x] 未命中才自动抽，冻结成新版本新指纹，不复用旧版本号
- [x] 已投用版本拒改：lock.assert_mutable 接在落库入口
- [ ] 人工裁定路（/api/kit/build）冻结后落库：缺 material_id 关联，待补

### 阶段 3 rebuild

- [x] 学习模式允许回改重交：按 mode 放行，submit_seq 自增；测验模式仍锁一次
- [x] 白名单校验挂到编辑动作：草稿保存也按 kit 校验，覆盖提交后回改（D11）
- [x] 草稿 HTTP 入口：POST/GET /api/draft，接 rebuild_service.save_draft
- [x] 提交落库带指纹、时点、提交序号

### 阶段 4 extract

- [x] 抽崩阈值配置化：写进配置项，记录基线来源与样本量；冻结图出现前阈值留空并标未校准（D08）。
      已落 `quality_thresholds` 单行表与 `Thresholds` 契约；未校准时信号只带原值。
- [x] 越界丢弃留档：机器侧一本，与人工裁定留档分开（D12）。
      丢弃由 normalize.collect 收口，引擎逐段带回，落 `discarded_candidate` 表。
- [x] ExtractionRecord 落库：原始输出与配置快照存库，不进 CSV。
      自动路每批一条 `auto-*`，含候选、丢弃、原始输出与段数；冻结后回填版本与指纹。

### 阶段 5 ingest

- [x] 解析结果缓存：键 = 源文件字节哈希 + 解析器版本，落盘 tmp 不入 git（D10）。
      实现在 ingest，空文本不缓存，损坏当未命中。

### 阶段 6 api 与数据出口

- [x] 导出改服务端检索：按被试、教材、时点单多全选，前端不再自己攒数
- [x] 量表作答落库，α 从库算
- [ ] 学生重抽：新旧两批并存不覆盖，旧批可切回

### 阶段 7 前端

- [ ] ui-share/styles：颜色、字号、间距、动效令牌
- [ ] ui-share/atoms：按钮、复选框、进度条、提示条
- [ ] ui-share/layout：顶栏、侧栏、底部操作条
- [ ] ui-share/canvas：ReactFlow 封装，connectOnClick 点-点连线，handle ≥ 24px
- [ ] 页面：教材准备含抽崩警告 → 模式选择 → 重建 → 提交 → 差异图 → 测验 → 量表 → 导出
- [ ] web 与 ui-share 集成
- 页面设计等用户提供 HTML 原型

### 阶段 8 文档

- [ ] 34 份 feature 文档按新风格重写：极简，无表格、无粗体、无引用块、无代码围栏、无跨文件引用
- [ ] 每份随所属 feature 的提交一起改，不单开纯文档提交

<!-- /@zone code -->
