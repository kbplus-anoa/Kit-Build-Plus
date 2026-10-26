<!-- @zone research -->
# README_PLAN — Kit-Build-Plus 技术方案与决策记录

> 本文件是本项目的**决策草稿与讨论记录**，给人读。
> 技术选型、流程取舍、待议事项都落在这里，先议后写码。
> 契约、接口、字段定义一律不进本文件；定稿后再进 `kbp/contracts/`。
>
> **与 `SPEC.md` 的分工（用户已定）：**
> - `README_PLAN.md`（本文件）：临时草稿、讨论过程、论证与出处，**给人读**
> - `SPEC.md`：讨论结束后写入，**给 AI 读，极度精简**，只留结论与约束
>
> 因此本文件**故意冗长**——它承载"为什么"，而 SPEC 只承载"是什么"。
> 定稿时从本文件提炼 SPEC，**不是把本文件压缩成 SPEC**。

---

## 0. 定位：这是一个创新，不是论文复刻

### 0.1 与论文的根本差异

论文（`docs/research/papers/10.58459_rptel.2026.21021.txt` 行 265–269）描述的 Kit-Build 流程是三步：

1. **专家**创建概念图
2. 专家图被拆解（去掉连接），成为 kit
3. kit 交给学生重组回专家图

**本项目去掉第 1 步的"专家"，换成 LLM。**

系统只有两个角色：**学生** 与 **LLM**。没有老师。

### 0.2 由此产生的核心张力

论文里"专家图"是校本知识的**权威基准**，评分之所以成立，是因为基准可信。
现在基准由 LLM 产出 —— 于是 **LLM 从"工具"升格为"出题人+阅卷标准"**。

这是本项目的创新点，同时是最大的效度威胁。第 4 节专门讨论。

---

## 1. 已定决策

| 编号 | 决策 | 依据 / 影响 |
|---|---|---|
| D1 | 技术栈 FastAPI + SQLite + React + TS + Vite + ReactFlow | 已写入 AGENTS.md |
| D2 | 评分只判**结构**，不判版面图像 | 命题级评分，见 D4 |
| D3 | 学生**只能从 kit 内**重组，不许加新概念/新连接词 | 封闭零件集是 Kit-Build 的定义 |
| D4 | 连接词来自**固定词表**，不是模型自由生成 | 见 1.1 |
| D5 | 输入兼容文字（txt/epub 等）与扫描版 PDF | 见第 5 节 |
| D6 | 扫描件解析走 **MinerU 云服务**；应用阶段再考虑降级本地 | 本机内存与 GPU 条件所限 |
| D7 | 抽取推理**在本机 CPU 上跑**（实验阶段） | 价格敏感，不接受 API 付费 |
| D8 | 实验阶段用**够用且本机可跑**的档位；应用阶段再降档 | 不用最弱档 |
| D9 | 效度走**方案 A（开发期校正版）**：开发阶段人标注，运行期 LLM 按标注抽取 | 见 4.2，已澄清 |
| D10 | 标注由**用户本人提前完成**，不用 LLM 预标 | 见 8.2，已拍板 |
| D11 | 先搭出来，再用用户提供的教材看效果，之后再谈微调 | 见 8.4，已拍板 |
| D12 | 共享层命名：`contract-share/`（契约）、`ui-share/`（组件） | 见 7.8；**2026-10-26 起契约层改为 `kbp/contracts/`，见 4.5** |
| D13 | 评分口径取**无部分分**；错误链用**四分类**（原三分类 + 方向反转） | 见 7.5 |
| D14 | 产品双模式：**测验模式**（锁定）/ **学习模式**（可循环修改） | 见 7.4.1 |
| D15 | 抽崩检测：先找现成方法，无成熟方法再用自研信号 | 见 12 |
| D16 | 检测到抽崩时：**警告框提示可重抽，但允许继续** | 见 12.4 |
| D17 | **模式由学生自选**（HCAI / 人本主义 / 有意义学习） | 见 7.4.2 |
| D18 | 警告下的测验结果**照常计分**，但带"可能不准"布尔标记 | 见 12.5 |
| D19 | 新增**导出测验结果为 CSV**，支持单个/多选/全选 | 见 7.7 |
| D20 | 抽崩检测方案：**S1–S4 必做，S5 只作否定证据** | 见 12A |
| D21 | **模式在进画布前选定并锁定**，中途不可切 | 见 7.4.2 |
| D22 | CSV **带 UTF-8 BOM** | 见 7.7 |
| D23 | 重抽记录**并存**，不覆盖 | 见 12.5 |
| D24 | README（面向用户）**披露** MinerU 云端解析 | 见 5.3 |
| D25 | **必须适应所有学科**；开发与论文阶段的教材由用户自选 | 见 14 |
| D26 | **不微调，学科适配靠词表**（产品全学科）；**论文只用理论心理学** | 见 14.2.1 |

### 1.1 为什么连接词必须固定（不反驳，且理由比"学生困惑"更强）

原始动机是体验：AI 自造连接词会产出同义词/近义词，学生分不清。
但更根本的是**方法论**：

- kit 的定义就是封闭零件集。允许学生造 kit 外的东西，方法就从
  Kit-Build 变成开放式概念图（open-ended），是另一套评分口径。
  论文里恰好有这两者的对照实验（EKB vs ESB）。
- 命题级评分的分母是**目标图的命题总数**。
  `10.1186_s41039-022-00189-9.txt` 行 676 原文：
  > "score is the ratio of the number of correct propositions in learner map
  > to the number [of propositions in the expert map]"

**分母必须固定，分数才可比。连接词一旦开放，分母就浮动。**

所以"只 kit"与"固定连接词列表"是同一件事的两面，互相支撑。

---

## 2. 模型选型：为什么排除决策模型

用户的初始猜想是找"专攻这方向"的 embedding / 决策模型（Jev、Laya 一类）。
查证后**结论是排除**，理由如下（均有原文支持）。

### 2.1 Jev（TypeSafe）

- 官方 `docs.typesafe.ai/models`：输入仅 Text，**不接受 audio/video**；
  上下文 64k 每请求 / 32k 每问题；价格 $42/Btok。
- 官方 `docs.typesafe.ai/concepts/state.md` 原文：
  > "Jev's primary training language is **English**; other languages,
  > including **CJK scripts, are accepted but currently have lower accuracy**"
- 原语只有 Choice / Score / Noul（闭集选择、打分、是非），外加实验性 Box。

### 2.2 Laya（convaiinnovations / NandhaKishorM）

- GitHub README：
  > "**Multilingual, non-autoregressive System 1 decision engine.**
  > Typed decisions over 100+ languages in a single forward pass — 33 ms"
- 仓库 34037 stars，Apache-2.0，2026-09-18 创建（**非常新**，93 open issues）。
- 中文实测（仓库自带 `research/benchmarks/feishu_zh/README.zh-CN.md`）：

  | 项目 | Laya 多语言版 | Jev 1.13.0 |
  |---|---:|---:|
  | 单选择题 | 20/64 | 64/64 |
  | 四问组合 | 18/64 | 63/64 |

  但该报告自带限定："2026-09-21 的历史快照，不是当前 main 分支的成绩"、
  "不含中文后训练权重，不宣称通用模型排名"。**且是 Laya 自己做的对比，有利益冲突。**
  故这组数字只当"两边中文都不稳"的旁证，不当结论。

### 2.3 GLiNER / RelEx

- GLiNER 多语言是**实体抽取**（`gliner_multi-v2.1`，100+ 语言）。
- 关系抽取权重 `knowledgator/gliner-relex-large-v1.0` 的 `gliner_config.json`
  经 `hf-mirror.com` 取得，其 `encoder_config._name_or_path` 为
  **`microsoft/deberta-v3-large`** —— 英文编码器。
  **故 RelEx 的关系抽取基本不适用于中文。**
- 该权重下载量 1253、likes 11，社区验证样本很少。

### 2.4 共同排除理由

这三个模型的设计目标是**在给定闭集中做判断**（每秒几十次、高频低难）。
本任务需要的是**从连续文本中产出开放集合的三元组**。
两者方向相反：

- 闭集判断模型：选项必须事先枚举 → 无法枚举"所有可能的三元组"
- 本任务：输出空间是组合爆炸的 → 需要 span 抽取或生成

---

## 3. 抽取模型：UIE 两档候选

### 3.1 候选 A：PaddleNLP UIE（BERT 式 span 抽取）

- 官方 Taskflow 文档列明：信息抽取 → 实体抽取 / **关系抽取** / 事件抽取 / 跨任务抽取
- 关系抽取的 schema 正好是本项目要的形态：

  ```python
  { "概念": ["爱吃", "属于", "导致", ...] }
  #          └──── 固定连接词列表 ────┘
  ```

- 档位（官方文档）：

  | 模型 | 结构 | 语言 |
  |---|---|---|
  | uie-base（默认） | 12L 768H 12heads | 中文 |
  | uie-medium | 6L 768H 12heads | 中文 |
  | uie-mini | 6L 384H 12heads | 中文 |
  | uie-micro | 4L 384H 12heads | 中文 |
  | uie-nano | 4L **312H** 12heads | 中文 |

- 零样本 / 5-shot 实测 F1（**来源是二手 CSDN 整理，非官方 README，需自行复核**）：

  | 模型 | 金融 0-shot | 医疗 0-shot | 互联网 0-shot |
  |---|---:|---:|---:|
  | uie-base | 46.43 | 71.83 | 78.33 |
  | uie-medium | 41.11 | 65.40 | 78.32 |
  | uie-mini | 37.04 | 60.50 | 72.09 |
  | uie-micro | 37.53 | 57.04 | 66.00 |

**关键优势（结构性，不是调参得来的）：**
UIE 是 span 抽取模型，能不能吐出某个关系类型，取决于 schema 里有没有。
**它无法产出 schema 之外的连接词。** 这正是 D4 想要的性质，无需 prompt 约束 + 校验重试。

### 3.2 候选 B：PP-UIE（生成式）

- 官方 `llm/application/information_extraction/README.md`：
  0.5B / 1.5B / 7B / 14B 四档，中英文，支持 8192 token 文档级抽取。
- 0.5B 结构：24L 896H 14heads。
- 官方宣称相对 UIE-Base 零样本平均提升 66%（宣传口径，未经本机复核）。

**关键劣势：**
PP-UIE 是 causal LM 生成结构化输出 —— **它可能生成 schema 之外的连接词**，
即 D4 要防的那类同义词污染会重新出现。

### 3.3 本机条件（实测）

```
CPU    AMD Ryzen 7 7735U（16 逻辑核），支持 avx2
GPU    无（无 nvidia-smi）
内存   总计 15290 MB，可用约 3128 MB（低内存为暂时现象）
swap   4G 分区 + 14.9G zram
```

无 CUDA → 全部走 CPU。

### 3.4 建议档位

**实验阶段：`uie-base`（12L768H）。**

- 参数量约 1.1亿 量级，CPU 推理可行，AVX2 有现成加速
- 中文原生，不是"多语言里的中文子集"
- span 抽取，结构上符合 D4
- 零样本 F1 在 46–78 区间，够做可行性验证

**不用 nano/micro 的理由（回应用户的担忧）：**
用户担心 nano 太弱导致质量差 —— 这个担心是对的。nano 是 4L312H，
在上表互联网域 0-shot 已明显低于 base。既然应用阶段才降档，实验阶段没有理由自缚。

**质量不足时的升级路径（不建议一上来就用）：**
改用 `PP-UIE-0.5B`，但**必须额外加"连接词白名单校验 + 重试"**，
因为它会生成 schema 外的值。这一步只能靠工程兜，代价要提前计入。

> ⚠️ **本节后半（微调思路）已被 D25 降级，见第 14 节。**
> D25 要求"适应所有学科"，而微调会引入灾难性遗忘
> （`arXiv:2401.05605` 原文："forgetting cannot be avoided through early
> stopping or by varying the number of parameters fine-tuned"）。
> **本节保留原文，但仅在"确定单学科"时适用。**

**降档路径（应用阶段）：**
`uie-base` → `uie-mini`（6L384H）。是否可接受，取决于实验期微调后的模型在
mini 档上的 F1 衰减，需要届时实测，现在不预设。

---

## 4. 没有老师之后：目标图的效度问题（✅ 已定：方案 A）

### 4.1 问题陈述

论文的评分有效性建立在"专家图 = 权威基准"上。
本项目里 LLM 同时是**抽题人**和**评分标准的来源**。
若 LLM 抽错（漏概念、错连接），错误会**贯穿整条链路**：

- 错误的连接进入 kit → 学生被迫在错误选项里选
- 错误答案进入基准 → 学生答对反而被判错

**这不是精度问题，是效度问题。**

### 4.2 三个可选应对（已拍板：A，但语义已澄清）

**方案 A：开发期人工校正（✅ 已选定，D9；语义见 4.2.1）**
- **不是**"每份目标图运行时抽检"，而是"开发阶段校正抽取能力，运行期直接放行"
- 优点：成本可控，保留"无老师"的产品定位
- 缺点：运行期的错误不受任何拦截

**方案 B：LLM 出图 + 多模型互证**
- 用两个不同模型各抽一次，取交集为 kit，差集降级为"可选连接"
- 优点：无需人；缺点：成本翻倍且只降低不消除错误
- "与 D7（不付费）冲突"这条已失效：D7 于 2026-10-26 改为「走云端 API，BYOK」，
  付费由使用方承担。但**本方案仍未采用**，理由是成本随机器数线性增长，
  而下面记载的替代路线（单一强模型的自动抽取）在实测中已足够。

**方案 C：封闭性作为结构性补救**
- 论点：kit 一旦裁定，学生只在零件集内组合，**错误的上界被 kit 本身锁死**
- 局限：这只约束"答案空间"，不保证"正确答案"是对的

**结论：A 的"运行期放行"思路保留，但抽取引擎于 2026-10-26 换为云端大模型**
（见 4.5）。C 的论证写进 WHY.md 作为补充。B 不采用。

### 4.2.1 用户对 A 的澄清（本节是理解 D9 的关键）

用户原话：

> "我想要的是——开发阶段[编程→标注]→用户使用阶段[llm根据我开发阶段的标注进行抽取]。
> 也就是说，当我的应用交给学生，他的流程中没有抽检的流程。"

**即：人的介入全部前移到开发阶段，运行期零人工。**

```
开发阶段：编程 → 标注 →（校准/微调）→ 抽取能力定型
                ↓
使用阶段：LLM 按已定型的抽取能力直接抽     ← 没有人在这条线上
```

这个理解改变了我原先对 A 的描述。必须写清楚**它解决了什么、没解决什么**：

**解决了**：判断标准只有一套（同一个人的标注），不会运行时分裂；
标注成本一次性投入，不随使用量线性增长。

**没解决**：运行期抽错了，**没有人会拦**。错误直接进 kit、进分母。

**因此 A 的成败完全取决于一件事：开发阶段的标注，能不能让抽取能力
在不熟悉的教材上依然可靠。** 这正好解释了 D11（先搭再看效果）为什么是对的——
它是验证这件事的唯一手段。

**由此产生的必须回答的问题（新增，见 10 节）**：
运行期如何**事后**发现"这份教材抽崩了"？开发阶段的校正无法覆盖运行期的新教材，
所以需要某种**运行期可观测性**（哪怕不是人工逐条审）。

### 4.5 抽取引擎迁移：本机 UIE → 云端大模型（2026-10-26）

**触发原因**：用户要求「运行期全自动裁 kit，没有人工标注」。
在这个前提下，抽取错误不再是可容忍的瑕疵，而是**评分分母错误**——
分母错了，所有学生的分数都不作数。

#### 4.5.1 本机 UIE 的实测缺陷

在本机 ONNX 版 UIE（PaddleNLP uie-base 权重，离线转换）上实测：

| 原文 | 结果 | 问题 |
|---|---|---|
| 情绪影响记忆，睡眠影响记忆。 | 用「影响」只给 [记忆]；换「影响的因素」只给 [情绪, 睡眠] | **一次只能覆盖关系一侧** |
| 认知失调属于动机理论的研究范畴。 | 宾语侧有，主语侧 pmax=0.397 无 span | **主语侧哑火** |
| 记忆包括感觉、短时、长时。 | 3 个 span → 按同连接词两两成对 → 6 条，含 3 条反向 | **方向被抹掉** |

三个后果：

1. **方向反转整类错误失效**：目标图变成双向，学生写反方向会被判对。
   实测：人工裁定（单向）得 0 分且报 reversed；自动抽取（双向）得 0.5 分、不报 reversed。
2. **单侧抽取不可预测**：从文本外观无从判断哪句会只抽到一侧。
3. **规则无底**：要靠后处理拼回主宾关系，等于承担中文句法全部例外，
   换学科即失效，与 D25（全学科）冲突。

#### 4.5.2 提示词层面的补救无效

试过把标注样例塞进正文前（少样本）：

| 示例数 | start pmax | 结果 |
|---|---|---|
| 0 | 0.000 | 模型完全无响应 |
| 1 | 0.995 | 有响应，与 0 例相比是"从哑火到能抽" |
| 3 | 0.990 | 与 1 例无差别，**精度没有提升** |

结论：少样本只解决"哑火"，不提高精度，且会污染位置坐标需要额外剥离。

#### 4.5.3 选定方案与代价

- 引擎：DeepSeek API（OpenAI 兼容格式），固定 `deepseek-flash`
- 付费方式：**BYOK**，使用方自配密钥、自付费用
- 量级估算：一章 1.2 万字、6 个连接词，空闲时段约 0.08 元；
  缓存命中后约 0.03 元；2000 章累计约 60 元

**已知风险（须写进论文局限）**：

| 风险 | 说明 |
|---|---|
| 不可复现 | 官方无 `seed` 参数，temperature=0 也不保证逐字相同 |
| 模型会变 | 已有先例：deepseek-v4-flash 下线后请求转由新模型服务 |
| 空 content | 官方文档自述 JSON Output 有此问题，客户端做最多 2 次重试 |
| 抽崩无人拦 | 自动裁 + 无人把关，须靠抽崩检测事后发现（SPEC 已定，未实现） |

**分数可比性的后果**：各机器自行裁 kit ⇒ 同一教材分母可能不同。
论文通过「固定教材 + 固定 kit」规避；产品运行期只主张自比。
### 4.3 需要写进 WHY.md 的论证

"AI 生成目标图是否损害 Kit-Build 的效度"必须正面回应，
因为这是本项目与论文最大的偏离点，也是审稿人第一个会问的。

---

## 5. 输入处理：MinerU 的边界

### 5.1 实测结论

- **txt 不需要 MinerU。** MinerU 官方 `docs/zh/index.md` 原文：
  > "Office、OpenDocument、EPUB、OFD、HTML/MHTML、CSV/TSV 使用本地 Flash 原生解析。
  > **纯文本直接读取，不进入解析流程。**"

  故 txt 直接 `open().read()`，是**短路**而非功能缺失。

- **epub 支持。** 官方文档多格式输入列表明确含 EPUB，且由 DocVortex 原生解析。

- **扫描 PDF 需要 OCR 档位。** 官方四档：
  > "Flash 用于快速预览与索引，Basic 提供基础 OCR/模型解析，
  > Standard 与 Advanced 面向更复杂的版面和更高的质量需求。"

  **扫描件至少 Basic，Flash 不够。**

### 5.2 决策：走云（D6）

- 本机无 GPU、可用内存受限，本地部署 MinerU 需装 torch 全家桶并走 ONNX CPU 后端
  （官方说明：小模型只有在检测到非 CPU 设备时才用 Torch 后端，否则 ONNX）
- 用户已定：实验阶段走云服务，应用阶段再考虑降级
- **必须注意**：MinerU 默认模型源 `auto` 会先探测 Hugging Face。
  本机实测 `huggingface.co` 不可达（000），需设
  `export MINERU_MODEL_SOURCE=modelscope`（官方文档明确给出该环境变量）。
  若将来本地部署，这是必需前置。

### 5.3 云服务带来的新约束（D24 已定：披露）

教材上传到第三方 → **必须在 README（面向用户）中明确披露**。

**披露至少要写清三件事，只说"会用到云服务"不够：**
1. **什么文件**会被上传（仅扫描件；文字层/pdf 与 txt/epub 不经过云端）
2. **传给谁**（MinerU 官方服务）
3. **为什么**（扫描件没有文字层，需要 OCR）

**同时必须说明"可以不用云"**：若用户只提供文字层文件，全流程离线。
否则用户无法判断自己是否受影响。

若将来面向真实课堂，这是合规项，不是技术项。

---

## 6. 流程（文字描述，不含契约）

### 6.1 离线：目标图生成

```
原文（txt / epub / 扫描 PDF）
  → 文字层：直接读取
  → 扫描层：MinerU 云解析 → Markdown
  → UIE（本机 CPU，schema = 概念 + 固定连接词表）
  → 候选三元组草稿
  → 人工抽检（方案 A）
  → 目标图（冻结）
  → 拆 kit：概念集 + 连接词集（去掉连接）
```

### 6.2 在线：学生重建

```
学生拖拽 kit → 组装图
  → 提交
  → 逐条查表：(A, r, B) 是否在目标图命题集内
  → 分数 = 正确命题数 / 目标图命题总数
  → 报告（错在哪些命题，而非只给分）
```

**注意：评分是 O(E) 查表，不是图匹配。**
GED 是 NP-hard（NetworkX 官方文档明确说明），且 D3 保证候选集封闭，
根本不需要图匹配算法。

### 6.3 触摸屏约束（D1 相关，影响 DESIGN.md）

ReactFlow 官方 Exampes 页 `examples/interaction/touch-device` 原文：
> "You can connect nodes on a touch device by tapping two handles in a row.
> In this example we increased the size of the handles so that they are better tappable.
> You can disable this behavior by setting the `connectOnClick` prop to false."

**即：触摸屏上是"点-点连线"，不是拖拽连线。**
界面必须按点选式连线设计，并用更大的 handle 热区。这条要进 `DESIGN.md`。

---

## 7. Feature 切分（七个，逐个介绍）

按 AGENTS.md 约定：每功能一个子包，功能间禁止互相 import，只经 `kbp/contracts/` 契约。
**依赖方向自上而下，箭头表示数据流向，不表示 import 关系。**

```
ingest → extract → kit → rebuild → score → export
                      \     |      /
                       \    v     /
                        → kbp/contracts ←
                              ↑
                          ui-share
```

`kbp/contracts/` 与 `ui-share/` 是横向通道；上面五个 feature 之间**没有任何直接 import**。

---

### 7.1 `ingest` — 原文读取与格式判定

**做什么**
把「用户给的一个文件」变成「一段可信的纯文本」，并记录它是怎么变来的。

**输入**：一个文件路径或上传的文件（txt / epub / 扫描 PDF / 文字层 PDF）

**输出**：纯文本 + 来源元信息（哪条路径处理的、原文件是什么、文本是否含 OCR 成分）

**内部职责**
- 判定有没有文字层（PDF 逐页探测文本可提取性）
- 文字层 → 直接读；epub → 解析；扫描件 → 调 MinerU 云服务
- 统一成一种中间形态，抹平三种来源的差异
- 标记 OCR 来源，供下游知道"这段文本可能有识别错误"

**边界（不做什么）**
- 不做任何抽取、不判断概念
- 不做分句/分词
- 不与数据库交互（它是纯函数式的：文件进，文本出）

**为什么单独成 feature**
三种输入格式的处理差异**全部**收在这一层，下游 `extract` 永远只面对纯文本。
如果合并进 `extract`，UIE 的代码里会混进 PDF 解析与 HTTP 调云的分支——
这两件事的失败模式完全不同（一个是网络/配额，一个是模型效果）。
分开后，扫描件下载失败不会表现为"抽取质量差"。

**待决**
- 云解析失败时（网络断、配额用完）的行为：报错中止，还是降级为"无文本"？
- 是否缓存解析结果（同一份教材二次上传不重复付费）？**我建议缓存，且不进 git**

---

### 7.2 `extract` — UIE 抽取

**做什么**
从纯文本中抽出一组**候选三元组**，全部落在"概念 × 固定连接词表"之内。

**输入**：纯文本 + 概念候选（可选）+ 连接词表（必填）

**输出**：候选三元组集合 `(概念A, 连接词, 概念B)`，每条带置信度

**内部职责**
- 按 schema 调用 UIE（`{"概念": ["爱吃", "属于", ...]}`）
- 长文本按 UIE 的窗口切分，再合并结果
- 去重、按置信度排序
- **保证输出不含连接词表外的值**（这是 UIE 的结构性质，但仍应断言）

**边界（不做什么）**
- 不决定哪条三元组"正确"——那是人的事（D9）
- 不冻结目标图——那是 `kit` 的事
- 不做人工审核界面

**为什么单独成 feature**
它是全项目唯一依赖 ML 模型的地方。把模型依赖隔离在一个文件夹里，
将来换模型（UIE → PP-UIE → 别的小模型）只改这里，其他五个 feature 不受影响。
这条对"应用阶段要降档"（D8）尤其关键。

**待决**
- 长文本切分策略：按段落切，还是按固定 token 窗口切带重叠？
- 概念候选是否允许用户先给一批（提高召回）？

---

### 7.3 `kit` — 目标图冻结与拆 kit

**做什么**
把候选三元组变成**冻结的目标图**，再拆出学生可用的零件集。

**输入**：候选三元组（来自 `extract`）+ 人工裁定结果（来自 D9 的抽检）

**输出**：
- 目标图（冻结，含命题集）
- kit：概念集 + 连接词集（**去掉连接**，这正是 Kit-Build 的定义）

**内部职责**
- 记录哪些候选被采纳、哪些被驳回、谁在什么时候裁定的
- 冻结后不可静默修改（改需走显式版本）
- 拆 kit 时保证：每个 kit 里的连接词，至少有一条目标命题用到它

**边界（不做什么）**
- 不判断学生答案
- 不做 UI 渲染（只产出数据）

**为什么单独成 feature**
"冻结"是这个项目的**方法论红线**——评分分母来自它，学生看到的 kit 来自它。
冻结逻辑一旦散落，就会出现"图改了但分母没改"这类静默错误。
把它独立出来，是为了让"冻结"这件事只有一个实现。

**待决**
- 冻结后的目标图能否版本化（同一教材 v1/v2）？我建议能，但 v1 一旦有学生用过就不能改
- 驳回的候选要不要留档（用于评估 UIE 的精度）？**我建议留，这是免费的标注数据**

---

### 7.4 `rebuild` — 学生组装

**做什么**
学生看到 kit，把概念和连接词组合成自己的图，然后提交。

**输入**：kit（来自 `kit`）

**输出**：学生提交的图（一组 `(概念A, 连接词, 概念B)`）

**内部职责**
- 前端画布（React Flow）
- **触摸屏要按点选式连线设计**（见 6.3，ReactFlow 官方原文）
- 提交前的基本校验：只能用 kit 内的概念和连接词
- 保存草稿（学生可能断电/关页面）

**边界（不做什么）**
- **不做评分**，甚至不在前端做任何对错提示——那会让学生边做边试
- 不生成报告

**为什么单独成 feature**
这是唯一的**学生直接交互**面，也是前端代码量最大的地方。
它和评分必须物理隔离：如果评分逻辑能被前端调用，学生就能探测答案。

### 7.4.1 双模式（D14）——已定

用户定：**默认测验模式，同时允许切换到学习模式。**

**这不是我的发明，论文里两种场景都写了：**

**学习模式的循环**（`10.58459_rptel.2026.21021.txt` 行 405–420 原文）：

> "Once the learner feels satisfied with their map, they can click on the ‘DONE’ button...
> The activity completes when the two maps are identical. Otherwise, the learner is
> presented with a visualization of the differences... the learner may press the
> ‘Return’ button to return to map recomposition state."
>
> "the learner **iterates through a loop** between recomposing the map and visualizing
> the differences **until he/she successfully recomposes the expert map**"

**测验模式（形成性评价的测量截面）**（`10.1186_s41039-017-0060-x.txt` 行 676–679）：

> "The learner map score is the ratio of the number of correct propositions in
> learner map to the number of propositions in the goal map ... takes a value of 0 to 1."

**两模式的差异只有一处：提交后能否继续修改图。**

| | 测验模式 | 学习模式 |
|---|---|---|
| 提交后可否改图 | ❌ 锁定，一次定分 | ✅ 可 Return 回去改 |
| 差异可视化 | ✅ 给（作为诊断反馈） | ✅ 给（作为下一步指引） |
| 分数 | ✅ 有效，用于效度研究 | ⚠️ 无意义（最终都收敛到 1.0） |
| 循环终止 | 不循环 | 直到完全一致或学生退出 |
| 用途 | **论文效度实验** | **学生自查与学习** |

**关键设计约束（必须写进 DESIGN.md）：**
两模式的**差异可视化组件是同一个**，只有"能否返回画布"这个开关不同。
否则会出现两套渲染逻辑，长期必然分叉。

### 7.4.2 模式由学生自选（D17）——已定，且有理论依据

用户定："**让学生自己选。我们的系统是以人为中心的AI应用（HCAI），
同时学习原理也是有意义学习，可见我们项目的精神就是人本主义。因此，相信学生。**"

**这不是"没考虑到会被刷分"，而是主动的立场选择。** 记录其理论锚点：

- **HCAI（Human-Centered AI）**：人不是系统的例外处理对象，而是决策主体
- **有意义学习**（Ausubel / Novak 一脉）：概念图的**理论源头就是意义学习理论**，
  学生自己判断"我是在学还是在测"本身就是元认知行为
- **人本主义**：默认信任学生，而不是用机制防范

**必须先承认的风险（写进 WHY.md，不要回避）：**
学习模式分数会收敛到 1.0，若学生全选学习模式，则测验数据为空。
**但这个风险的处置是"记录"而不是"限制"** —— 因为限制学生选择，
就等于在方法论层面否定了 HCAI 的立场。

**工程上的对应做法**：
每次提交都记录模式（`mode` 字段），统计时可以据此分层。
这样即使自选导致样本偏斜，也**可被观测、可在论文中说明**，而不是被隐藏。

### 7.4.3 模式锁定（D21）——已定

用户定：**进画布前就选，选后锁定。**

**这一条同时解决了数据完整性问题**（原先的顾虑"改到全对再切测验"）：
因为模式是**进入时的属性，不可变**，所以：
- 一次提交只有一个 `mode` 值，不存在"中途变性"
- CSV 里按 `mode` 分层是**可靠**的，不需要额外记录"切换历史"

**实现上的含义（不是契约，只是约束）：**
`mode` 应当在**创建提交记录时**就写入，而不是评分时补写。
否则会出现"记录建了但模式还没定"的中间态。

---

### 7.5 `score` — 命题级查表评分

**做什么**
比对学生的图和目标图，算分，出报告。

**输入**：学生提交的图 + 冻结的目标图

**输出**：分数 + 报告（哪些命题对、哪些错、漏了什么、多了什么）

**内部职责**
- 逐条查表：`(A, r, B)` 是否在目标命题集内（**命题级精确匹配**）
- 分数 = 正确命题数 / 目标图命题总数（**已核对论文原文，见 7.5.1**）
- 报出三种错误链（**名称与定义均取自论文，见 7.5.2**）

### 7.5.1 评分口径：我已核对论文原文

上一轮我把评分口径列为"待决"，并担心"方向错是否给部分分"没有依据。
**重读论文后，答案很明确——不给部分分。**

`10.1186_s41039-017-0060-x.txt` 行 676–679 原文：

> "The learner map score is the ratio of the number of correct propositions in
> learner map to the number of propositions in the goal map. It presents the
> degree of accordance between the learner map and the goal map that takes a
> value of 0 to 1."

**分数就是比例，取值 0~1。没有部分分，没有方向对错的加权。**

同一篇 行 145 处还提到另一种口径（Novak）：

> "A correct proposition can get only one score, while for the specific
> propositions ... the score will be increased from one to ten."

但那是 **Novak 法**，不是 Kit-Build 法。Kit-Build 用的是精确匹配。

**关于"部分分"，论文的态度是明确的（行 371–378）**：

> "some systems assign an additional condition of scoring methodologies such as
> graph theory, pattern of propositions, ranging scoring, or synonym words ...
> The learners who construct the incorrect proposition can receive a partial
> score when two concepts have a relation or can be connected to each other,
> even though the linking word is incorrect."

这段话是在**描述别人的系统**（C-TOOLS、CMT 一类），语境是"这引入了灵活性"。
而 Kit-Build 在 Table 1 里的判据是 `E`（exact matching），
**并明确不含 `S`（synonym matching）**，而 C-TOOLS 和 CMT 都含 `S`。

**所以"部分分"是 Kit-Build 刻意不要的东西。**
想加的话可以加，但那就不再是 Kit-Build 口径了，需要单独论证。

### 7.5.2 三种错误链（论文原文定义）

`10.1186_s41039-017-0060-x.txt` 行 235–240：

> "The link that is used to connect two concepts in the learner map but at
> least one concept which is different from the goal map is called **excessive
> link**. The link that is not connected to any concept is **leaving links**.
> And the **lacking links** are used to call the link that is in the goal map
> but does not exist in the learner map."

| 论文术语 | 含义 | 我原先的误称 |
|---|---|---|
| **lacking link** | 目标图有、学生图没有 | 漏报 |
| **excessive link** | 学生图有连接，但至少一端概念与目标图不同 | （我漏了这条） |
| **leaving link** | 连接词放了，但没连到任何概念 | （我完全没想到） |

**"leaving link"是我上一轮漏掉的关键类型**，而论文对它有明确的教学解读
（行 264–266）：

> "This link indicates that the learners **do not understand the linking word**."

**这是一类独立的诊断信息**：学生把连接词卡片丢在画布上但不知往哪连，
和"连错"是完全不同的认知状态。

**注意**：三种错误都**不影响分数**（分数只看正确命题比例），
它们是**诊断报告**的内容，不是评分的加减项。这一点必须分清。

### 7.5.3 方向错：Pailai 没讨论，但**另有文献专门定义了它**

用户问：真的在论文里找不到方向错吗？

**答案分两半，必须说清楚：**

**① Pailai et al. (2017) 的三分类里——确实没有。**
该文对 excessive 的定义是"至少一端概念与目标图不同"，
方向错两头概念都在图里，套不进去。**这个缺口是真的。**

**② 但"方向错"在概念图评分文献里有独立名称：`reversed proposition`。**
我在 `docs/research/papers/10.1109_tlt.2021.3103331.txt`（Kroeze et al., 2021,
IEEE TLT）找到专门的判据定义，行 313–320 原文：

> "Mislabeled and reversed propositions are determined by comparing labels for
> student propositions with those for propositions in the reference map, and
> identifying student propositions that contain identical concepts to those in
> the reference map, but either have a **different label**, or **reverse the
> direction** of the proposition."

同一篇还把它列进了八类短板之一（行 301–305）：

> "typos, missing concepts, superfluous concepts, mislabeled propositions,
> **reversed propositions**, missing propositions, superfluous propositions,
> and shortcuts"

**并且它把"标签错"与"方向错"分成了两类**（`mislabeled` vs `reversed`）——
这正是你说的那种区分。

### 7.5.4 一个反面证据，必须记下来

Kroeze 那篇同时报告了 reversed 判据的**可靠性问题**，行 655–660：

> "The only exceptions were the reversed proposition and shortcut criteria.
> The low accuracy of the reversed proposition criterion can be explained by
> the fact that **with an appropriate change of label, any proposition in a
> concept map can be reversed**."

**这句话对我们极其重要**：它说明"方向错"在**开放词汇**的概念图里难以自动判定，
因为换个标签方向就通了（"苹果-长在-树上" vs "树-结出-苹果"）。

**但我们的场景恰好免疫这个问题**：D4 保证连接词来自**固定词表**，
不是学生自由输入的。所以"方向反了还用同一个词"是可判定的
（`(A, r, B)` 与 `(B, r, A)` 都能在候选集里枚举）。

**这是一条可以写进论文的论据：封闭连接词集不只是防同义词，还让方向错变得可判。**

### 7.5.5 四分类（D13 定案）

用户已定：**方向错独立成第四类。**

| 类型 | 英文（原文出处） | 界面名 | 定义 |
|---|---|---|---|
| 缺失连接 | lacking link（Pailai 2017） | 缺失连接 | 目标图有、学生图没有 |
| 多余连接 | excessive link（Pailai 2017） | 多余连接 | 学生有连接，但至少一端概念与目标图不同 |
| 游离连接 | leaving link（Pailai 2017） | 游离连接 | 连接词放了，但没连到任何概念 |
| **方向反转** | **reversed proposition（Kroeze 2021）** | **方向反转** | 两端概念都对，连接词选对了，但方向相反 |

**这个组合的优点（写论文时可直接用）：**
- 前三类可整块引用 Pailai et al. (2017)，不用自己论证
- 第四类可引用 Kroeze et al. (2021)，也不用自己论证
- **两个来源各自内部自洽，不产生定义冲突**（这正是归入 excessive 做不到的）

**必须同时写进 WHY.md 的一条（来自 7.5.4）：**
Kroeze 报告 reversed 判据在其场景下准确率偏低，原因是
"换个标签任何命题都能反向"。**而本项目用封闭连接词集消除了这个失效条件**——
这是 D4 的第二个收益（第一个是防同义词），值得单独作为贡献点陈述。

**四类都只影响诊断报告，不影响分数。**（见 7.5.1，分数只算正确命题比例）

**边界（不做什么）**
- 不做图匹配（不需要，见 6.2）
- 不修改目标图
- 不生成"建议"（除非将来有明确设计）

**为什么单独成 feature**
评分口径是**研究效度的核心**，必须高度内聚、可单测。
四类错误的区分本身就是研究产出——不同的错误类型分布才是有教学意义的东西。
如果和 `rebuild` 混在一起，容易出现"前端顺手算了一下"的越界。

**待决**
- 报告要不要给"部分分"（如方向错给一半）？**这涉及评分口径，需对照论文**
- 多报是否扣分？（论文口径只算正确命题比例，多报不扣，但值得在报告里体现）

---

### 7.6 `kbp/contracts` — 契约域

**做什么**
只定义契约：数据结构、字段语义、纯函数签名、Protocol。

**内容形态**（按 AGENTS.md）
- 一个契约域一个文件
- 字段注释含：含义 / 单位 / 可空 / 枚举
- 行为契约用 Protocol 或纯函数签名
- **只做契约→契约，不做业务转换**

**边界（绝对不做什么）**
- 不含任何业务逻辑
- 不含 IO（不读文件、不连库、不发 HTTP）
- 不在调用点包 converter（出边界的转换由提供方做）

**为什么必须有**
五个 feature 之间禁止 import 彼此，跨功能只能走 `kbp/contracts/`。
没有它就写不出任何跨 feature 的代码。

**待决（下一步要做的）**
- 契约域怎么切：按数据流切（`TextDoc` / `Triple` / `TargetMap` / `Kit` / `Submission` / `Report`），
  还是按 feature 边界切？
- **冻结规则**：契约被第二个 feature 消费即冻结，改动需先给旧→新、影响范围、迁移方式

---

### 7.7 `export` — 测验结果导出（D19）

用户新增需求：**可单个导出、多选或全选为 CSV。**

**为什么独立于 `score`？**
表面看像 `score`（它有数据），但导出是**跨记录批量操作**，
而 `score` 是"一次提交 → 一份报告"的单一职责。理由：

- 它需要知道"有哪些测验记录"——这是**存储查询**，不是评分
- 它要处理批量选择（单个/多选/全选）——**交互模式与单次评分完全不同**
- 将来可能导出别的格式（xlsx、json）——**扩展方向独立**

**但要注意 `export` 与 `score` 的依赖方向**：
`export` 读 `score` 产出的报告，**不重新算分**。
若 `export` 自己算分，那么"导出的分数"和"屏幕上显示的分数"可能不一致——
这是最隐蔽的一类 bug。

**CSV 字段（已按论文实际变量重设计，见 7.7.1）**

**编码（D22 已定）：UTF-8 带 BOM。**

理由具体：不带 BOM 时，Excel for Windows 会用本地 ANSI 猜测编码，
中文列名与中文概念名都会乱码。**带 BOM 是被 Excel 正确识别的必要条件。**
代价：部分程序（如某些 Linux 工具）会把 BOM 当内容的一部分，
需要在读取时容忍。**这是可以用一次麻烦换来的稳定性。**

### 7.7.1 CSV 字段设计（依据论文实际用的变量）

我翻了 4 篇论文，看它们**实际收什么变量**。结论是：原来那 7 个字段**不够**，
缺了好几项做严谨量化分析必需的。

#### 论文实际使用的设计变量（出处）

**[P2] Khudhur et al. (2026)** 用了三阶段测量（行 576–580 原文）：

> "three distinct phases: the **pre-concept map construction phase (pre-test)**,
> the **post-construction phase (post-test)**, and a subsequent **two-week
> delayed phase (delayed post-test)**"

以及 **normalized change**（行 564–570）：

> "Normalized change metric measures the proportion of improvement or declines
> in academic achievement relevant to the maximum of what can be improved or
> lost, **thus avoiding the pre-test score bias**"

还有 **time-on-task**（行 29）：

> "the time-on-task does not predict ..."

**[P5] Kroeze et al. (2021)** 的统计模型（行 486–492、521–534）：

> "**Class and domain were included as random effects** to account for
> interclass correlation effects. Students' **gender, age, and grade** for the
> domain were controlled for by including them as **fixed effects**."

**[P4] Prasetya et al. (2022)** 用了 TAM（行 505–515）：

> "PEOU, PU, and BI scales ... a **six-point Likert scale** ... consisted of
> **3 PEOU items, 3 PU items, and 1 BI**"

以及**前测同质性检验**（行 278–279）：

> "the pretest was conducted before determining the role of the group, and the
> results stated that both classes were **homogeneous (p = 0.445 > 0.05)**"

#### 据此重设计的字段（分四组）

**A. 标识与版本（可回溯）**

| 字段 | 依据 |
|---|---|
| 提交时间 | 排序 |
| 被试 ID（可匿名） | Kroeze 的分层需要 |
| 教材 ID / 目标图版本 | D14 版本化 |
| **连接词表 ID / 版本** | **新增，D26 后必须有**——词表换学科就变，不记录则跨批不可比 |
| 模式（测验/学习） | D17 |
| 某次抽取的批次 ID | 同一教材多次抽取时区分（D23 并存） |

**B. 评分结果（可重算）**

| 字段 | 依据 |
|---|---|
| 正确命题数 / 目标命题总数 | 分数可重算 |
| **分数（0~1）** | 存一份便于核对，但**以分子分母为准** |
| 四类错误计数（缺失/多余/游离/方向反转） | 四分类（D13） |
| 是否可能不准（布尔） | D18 |
| **触发的信号与值** | D18 补充——存值才能重算 |

**C. 学习效果相关（这是原设计缺的大块）**

| 字段 | 依据 |
|---|---|
| **前测得分** | Khudhur 的 pre-test |
| **后测得分** | Khudhur 的 post-test |
| **延迟后测得分**（如有） | Khudhur 的 delayed post-test |
| **normalized change** | **建议存分子分母，让分析时自己算**——因为公式有多个变体 |
| **time-on-task（秒）** | Khudhur 用了；且论文说它"不预测"成绩，这本身是结论 |
| **建图开始/结束时间戳** | 比存一个时长更灵活，可重算 |

**D. 协变量（做严谨分析必需）**

| 字段 | 依据 |
|---|---|
| 性别 | Kroeze 的 fixed effect |
| 年龄 | 同上 |
| 年级 / 学段 | 同上（Kroeze 的 "grade for the domain"） |
| **班级 / 群组** | Kroeze 的 **random effect**——不做多层模型就必须有它 |
| **专业 / 学科背景** | **新增**：理论心理学场景下，学生是否心理学专业影响很大 |

#### 三个必须说明的设计原则

**① 存原始量，不存派生量。**
normalized change、分数、时长都是**派生量**。
派生量存下来就固化了公式选择，将来想换公式只能重算不了。
**所以：存分子分母、存时间戳、存原始计数。**

**② 班级必须存，因为它是 random effect。**
不存班级就无法做多层模型，而 Kroeze 明确指出要处理
"interclass correlation effects"。**这是心理学量化分析的硬要求。**

**③ 前测/后测/question-level 数据可能不在这个 CSV 里。**
Khudhur 的 normalized change 是**按题**算的（Table 1 是每题的三阶段正确性）。
若要做到那个粒度，需要**第二张表**（question-level），
本 CSV 只放**被试级聚合**。**这条要提前想清楚，否则后期无法补。**

**字段详表已外置（用户要求）：**

| 文件 | 内容 | 权限 |
|---|---|---|
| `CSV_PLAN.md` | 字段名、允许值、可空、来历 | **用户写**，等用户逐项修改 |
| `STAT_PLAN.md` | 统计量、算法、作用、出处 | research |

本节只保留**设计原则**，具体字段以 `CSV_PLAN.md` 为准。

**已定：`record_id` 按顺序 1/2/3/4/5... 唯一编号。**

---

### 7.8 跨 feature 的三个待议点

1. **人工抽检（D9）落在哪？**
   抽检发生在 `extract` 之后、`kit` 冻结之前。
   两条路：(a) 作为 `kit` 内部的一步；(b) 独立成 `review` feature。
   **我倾向 (a)**——因为"冻结"和"裁定"是同一个动作的两面，
   拆开会产生"谁有权冻结"的模糊地带。

2. **云解析属不属于 `ingest`？**
   **属于。** 它是"从文件得到文本"的一部分，换了一种手段而已。
   单独成 `ocr` 会让 `ingest` 变成"半个 ingester"，反而更难理解。

3. **前端代码怎么分？**
   `rebuild` 和 `score` 都有前端。但按约定 feature 间不 import，
   共享的组件（按钮、布局）应该走 `ui-share/`（见 7.8），
   或者接受少量重复。**这条需要单独定规则，不要硬套后端约定。**

**以上 7.1–7.7 是介绍，7.8 是待议。契约仍然一个都还没写。**

---

### 7.9 前端组件共享（专门讨论）

#### 7.9.1 问题

后端约定"feature 间禁止 import 彼此，只经 share/"。
前端照搬会出事：`rebuild` 和 `score` 都要画概念图，
缩放平移逻辑、节点样式、连接线渲染是同一套代码。
按后端约定，就得在两个 feature 里各写一份，或者走 kbp/contracts 契约——
但**UI 组件不是契约**，它是实现。

#### 7.9.2 查到的三种主流做法

**做法一：抽成独立包（monorepo）**
适合跨**项目**复用。但 [一篇 monorepo 实践文](https://www.cnblogs.com/dennisj/p/14230178.html)
明确指出它的前提是"复用的是业务组件、且别的项目也用得上"。
本项目是单体应用，没有第二个项目要复用。**不适用。**

**做法二：Feature-Sliced Design 的 shared 层**
[官方文档](https://feature-sliced.design/docs/reference/layers) 给的规则原文：

> "A module (file) in a slice can only import other slices when they are located
> on layers strictly below."

层级自高到低是 App / Processes / Pages / Widgets / Features / Entities / Shared。
**Shared 层可以自由 import**，因为：

> "the layers App and Shared are exceptions ... Shared does not have business
> domains ... layers App and Shared are made up of segments, and segments can
> import each other freely."

并且明确：

> "Shared should contain no business logic at all, hence has no meaning for the product"

**这和后端 `kbp/contracts` 的语义完全一致**：无业务逻辑、谁都能用。

**做法三：shadcn/ui 的复制模式**
核心是"**组件即你的代码**"，用 CLI 把源码复制进项目，不做 npm 依赖。
好处是随便改、不被上游绑架；代价是重复。

#### 7.9.3 已定命名（D12）

用户已定，两个共享层用对称命名：

| 目录 | 共享什么 | 语义 |
|---|---|---|
| **`kbp/contracts/`** | 契约 | 类型、字段语义、纯函数签名、Protocol。**无实现、无 IO** |
| **`ui-share/`** | 实现 | 组件、样式、通用交互封装。**无业务逻辑** |

**为什么这个命名好：** `*-share/` 是一个后缀族，一眼看出"两个都是共享层，
只是共享的东西不同"——一个是**契约**，一个是**实现**。

✅ **改名已完成（两处都已生效）**：用户授权后，
`README_PLAN.md` 内全部替换，`AGENTS.md` 的四处引用也已改为 `contract-share/`。

**关于 `ui-share/` 的规则（用户已同意"可以"）：**

- 只放**纯展示组件**与**通用交互组件**（布局、按钮、缩放容器、节点外壳）
- **严禁**放业务逻辑：不能出现"这条命题对不对"、"这个连接词合不合法"
- **两个 feature 都能 import 它**，这是它存在的理由

**为什么不抽成 npm 包**：单体应用，没有复用对象，抽出包只增加构建复杂度，
反而让 AI 改代码时多一层心智负担（正好是 vibe coding 的技术债来源，
见 [arXiv:2512.11922](https://arxiv.org/abs/2512.11922) 关于
"architectural inconsistencies ... lack of explicit design rationale" 的讨论）。

**为什么不复制粘贴（shadcn 模式）**：shadcn 复制的是**外部库的源码**（一次性导入，
之后不再同步）。本项目要共享的是**自己正在迭代的组件**，复制会导致改一处忘一处。

#### 7.9.4 已定边界（本轮拍板，D12 补充）

用户对三条全部同意，第三条明确"**算 ui-share/**"。

| 问题 | 决定 |
|---|---|
| 概念图节点算不算业务 | **不算**，放 `ui-share/` |
| React Flow 封装放哪 | 放 `ui-share/canvas/`（**单个 canvas 子目录**，不散落） |
| 页面骨架能否共享 | **能**，放 `ui-share/` |

**判定规则（把三条收敛成一句可执行的话）：**

> `ui-share/` 放的是"**知道怎么画，但不知道对错**"的东西。
> 一旦某个组件需要知道"这条命题对不对"、"这个词在不在词表里"，
> 它就不属于 `ui-share/`，而属于对应 feature。

这条规则能直接判：概念图节点只画形状 → 属于；评分高亮"这条错了" → 不属于。

**由此产生的一个具体约束（前端结构定了）：**

`ui-share/` 里**不能引用 `kbp/contracts/` 的业务类型**。
比如节点组件只接受"文本 + 位置"，不接受"命题对象"。
否则 `ui-share/` 就和业务绑定了，横切能力消失。

**前端目录（建议，非契约）**

```
ui-share/
  canvas/        React Flow 封装：缩放、平移、连线、handle
  layout/        页面骨架（标题 + 左画布 + 右面板）
  atoms/         按钮、输入框、标签、警告框
  styles/         全局样式与主题变量
```

---

## 8. 标注计划（✅ 已拍板：用户本人提前标）

### 8.1 现状

- 用户原话："标注都要标"、"**无标注好的**"，随后明确："**标注是我提前标。我自己标。**"

即：没有现成标注数据，由用户本人（项目作者）先行标注。

### 8.2 已解决的矛盾（D10）

**没有老师，谁来标？** —— 答案是：**用户自己。**

这个解法消除了一处关键风险：**如果标注由 LLM 预标，那么"正确答案"和
"生成答案"来自同一个模型，评估就变成了自我循环。**

用户亲自标注意味着：
- 基准与人独立于模型，评估有效
- 方案 A（D9）的抽检者与标注者是同一人，**判断标准不会分裂**
- 代价是人力成本，但这部分成本落在项目作者身上，不落在产品用户身上

**这条不冲突于 0.1 的"系统没有老师"**：
标注发生在**离线准备阶段**，是研究行为；
产品运行时确实只有学生和 LLM。两者不在同一个时间尺度上。

### 8.3 标注什么（用户已答"都要标"）

- 概念：哪些词/短语算节点
- 连接词：每个命题用词表里的哪一个
- 命题结构：(A, r, B) 三元组
- 边界：哪些内容**不该**进图（负例，用于测精度而非召回）

### 8.4 冷启动顺序（✅ 已拍板：先搭再看，D11）

用户原话："**先看看搭出来之后我给的教材效果好不好再说**"

所以顺序是：

1. **先把系统搭出来**（不依赖标注数据的部分：ingest / kit / rebuild / score）
2. 用户提供教材，跑一遍 UIE 零样本抽取
3. **看效果再决定**：够用 → 不动；不够用 → 才谈 few-shot 微调
4. 微调后再评估是否降档

**这个顺序有个重要含义：微调不是当前任务，不在第一个里程碑里。**
UIE 用零样本先跑通，把"模型效果"这个变量留到有真实教材之后再引入。
好处是：如果效果不好，能立刻区分是"抽取不行"还是"流程设计不行"。

### 8.5 仍待确认

- **具体学科**（本科难度已定，学科未定）—— 影响 UIE 零样本表现，
  但按 D11 可以在拿到教材后再看
- 首批教材给几份、给哪几份

---

## 8A. 已定的其余结构决策（本轮）

| 问题 | 决定 |
|---|---|
| 人工校正落在哪 | **`kit` 内部**（不独立成 review feature） |
| MinerU 云解析缓存 | **缓存，不入 git** |
| 目标图版本化 | **可以 v1/v2，但 v1 一旦有学生用过就不能改** |
| 驳回的候选 | **留档**（作为 UIE 精度的免费标注数据） |
| 中途保存/续做 | **允许** |
| 限时 | **不限** |
| 提交后能否改 | **分模式**：测验模式锁定；学习模式可循环（D14，见 7.4.1） |

**关于"目标图 v1 用过就不能改"的一个技术后果：**
这意味着 `kit` 必须记录**每次提交引用的是哪个版本**，
否则无法回答"这份分数是按哪版目标图算的"。这是版本化的真正含义，
不只是给目标图打个版本号。

---

## 9. 风险清单

| 风险 | 影响 | 缓解 |
|---|---|---|
| LLM 生成的目标图有错 | 效度崩，学生答对被判错 | 第 4 节方案 A |
| UIE 零样本 F1 不足以用 | 整条离线链路失效 | 先小规模实测，再决定微调 |
| 本机内存不足（当前仅 3GB 可用） | 模型加载/推理失败 | 用户称内存低为暂时现象，已部署过 |
| MinerU 云服务不可用或政策变动 | 扫描件链路断 | 保留本地部署方案，记录 modelscope 变量 |
| 连接词表本身设计不合理 | 学生理解困难，甚至歧义 | 词表需小规模试用后迭代 |
| 触摸屏连线手感与鼠标差异大 | 学生挫败 | 按官方建议加大 handle，点选式连线 |

---

## 10. 未决问题汇总（按优先级）

### 已关闭（本轮）

- ~~目标图效度走哪条~~ → **A**（D9）
- ~~谁来做标注~~ → **用户本人提前标**（D10）
- ~~先标注还是先搭系统~~ → **先搭，看效果再说**（D11，微调暂不列入里程碑）

### 本轮关闭的（批量）

- ~~评分口径~~ → 无部分分（7.5.1）
- ~~错误链~~ → 用原文三分类 + 中文界面名（7.5.2）
- ~~方向错归哪类~~ → **已找到文献依据**（7.5.3），但**我给的是四分类建议**，
  用户原意是归入 excessive。**这一条需要用户再确认一次（见下方 1）**
- ~~提交后能否改~~ → 双模式（D14，7.4.1）
- ~~人工校正落在哪~~ → `kit` 内部
- ~~MinerU 缓存~~ → 缓存不入 git
- ~~目标图版本化~~ → 可版本化，用过即锁
- ~~驳回候选留档~~ → 留档
- ~~中途保存/续做/限时~~ → 允许 / 不限
- ~~前端共享命名~~ → `contract-share/` + `ui-share/`（D12）
- ~~抽崩检测找现成方法~~ → 已查，无成熟实现（第 12 节）
- ~~抽崩后怎么办~~ → 警告框 + 允许继续（D16）

### 本轮关闭的（再批量）

- ~~方向错归类~~ → **四分类，方向反转独立**（D13，7.5.5）
- ~~谁决定测验/学习模式~~ → **学生自选**（D17，7.4.2，HCAI 立场）
- ~~警告时是否禁止计分~~ → **照常计分 + 布尔标记**（D18，12.5）
- ~~抽崩检测用什么~~ → **S1–S4 必做，S5 只作否定证据**（D20，12A）
- ~~是否需要导出~~ → **新增 CSV 导出，单/多/全选**（D19，7.7）
- ~~`export` 是否独立 feature~~ → **独立，立为第七个**（7.7）
- ~~`ui-share/` 三条边界~~ → **全部同意，页面骨架算 ui-share**（7.9.4）
- ~~`share/` 改名~~ → **已授权并完成**（plan 与 AGENTS.md 均已替换）

### 仍然开放

0. **"标注模型"的歧义**（14.2.1）：我按"**标注数据集**"理解并写入。
   **若是"用标注微调出的小模型"，第 14 节要整体重写，请纠正。**

1. ~~模式切换时机~~ → **进画布前选定并锁定**（D21，7.4.3）
2. ~~UTF-8 BOM~~ → **带**（D22）
3. ~~重抽记录~~ → **并存**（D23）
4. ~~披露 MinerU~~ → **披露**（D24）
5. ~~具体学科~~ → **产品全学科（D25）；论文用理论心理学（D26，14.2.1）**
5a. ~~学科适配方案~~ → **甲+丙：不微调，靠词表**（D26）
6. ~~AGENTS.md 改名~~ → **已完成**
7. ~~`SPEC.md` 分工~~ → plan 给人读、spec 给 AI 读且精简，讨论结束后写入

### 仅剩的细节项

- **CSV 字段**：已外置到 `CSV_PLAN.md`（用户写权限，等用户改）
- **统计量与算法**：已外置到 `STAT_PLAN.md`（含出处与待确认 5 项）
- **第二张表（题级）**：已定**现在就做**，long 格式，延迟后测同表（CSV_PLAN H）
- **连接词表是否需要内置几套学科模板**（若走方案丙，这是产品设计项）
- **抽样与伦理**：若真收性别年龄，一般需要伦理审查与知情同意——
  这是研究设计问题，不是技术问题，但**必须在收数据前决定**

---

## 11. 变更记录

| 日期 | 变更 |
|---|---|
| 初稿 | 建立选型记录，排除 Jev/Laya/GLiNER，确定 UIE 路线 |
| 本轮 | 关闭效度问题（A）、确定标注主体（用户自标）、确定先搭再看（D11） |
| 上一轮 | 把第 7 节从"草稿清单"改写为六个 feature 逐个介绍；新增 7.7 跨 feature 待议 |
| 本轮 | **重读论文**：核实评分口径（0~1 比例、无部分分）与三种错误链定义（7.5.1 / 7.5.2） |
| 本轮 | 按用户澄清重写 4.2.1：人工全部前移到开发阶段，运行期零人工 |
| 上一轮 | 新增 7.8 前端组件共享（三种主流做法 + 建议 + 三条待定边界） |
| 本轮 | 命名定案（D12）、批量关闭结构问题（8A）、双模式（D14） |
| 本轮 | **发现 reversed proposition 有独立文献**（Kroeze 2021），7.5.3–7.5.5 |
| 上一轮 | 新增第 12 节：抽崩检测的文献调研与候选信号（D15 / D16） |
| 本轮 | 四分类定案（D13）；模式学生自选（D17，HCAI 立场） |
| 本轮 | 警告下照常计分 + 布尔标记（D18）；新增 CSV 导出（D19） |
| 本轮 | 抽崩检测给出具体方案（D20 / 12A），并记录了**一致性≠正确**的反证 |
| 上一轮 | 记录 AGENTS.md 新增 `SPEC.md` 与 `README_PLAN.md` 可能定位重叠 |
| 本轮 | 新增第 13 节**参考文献库**（8 条，含"用在哪"与三条引用硬约束） |
| 本轮 | `share/` → `contract-share/` 全文替换（已授权） |
| 本轮 | `export` 提为第七个 feature（7.7）；`ui-share/` 三条边界拍板（7.9.4） |
| 本轮 | D18 补充：不存布尔，存**触发信号 + 实际值 + 阈值** |
| 上一轮 | 记录 plan 与 SPEC 的分工：plan 承载"为什么"，SPEC 只承载"是什么" |
| 本轮 | D21–D25：模式锁定、BOM、重抽并存、披露 MinerU、全学科通用 |
| 本轮 | **新增第 14 节**：全学科要求推翻微调思路，记入灾难性遗忘证据 |
| 本轮 | 3.4 的微调建议**降级**（保留原文 + 标注失效条件），不删除 |
| 本轮 | D26：产品全学科 + 论文用理论心理学单一学科（14.2.1） |
| 上一轮 | 记录"标注模型"解读歧义；记录理论心理学文本特点带来的词表设计风险 |
| 本轮 | 确认"标注模型"= **标注数据集**（A），D26 定稿 |
| 本轮 | **重设计 CSV 字段**（7.7.1）：依 P2/P4/P5 的实际变量，扩为四组约 20 项 |
| 上一轮 | 记录三条设计原则：存原始量不存派生量 / 班级是 random effect 必存 / question-level 需第二张表 |
| 本轮 | 新建 `STAT_PLAN.md`（统计量/算法/作用/出处）与 `CSV_PLAN.md`（字段草案，用户写权限） |
| 上一轮 | 确认 `record_id` 顺序唯一编号 |
| 本轮 | B9/B10 改为**独立 0/1 列 + 中文列名**（SPSS 友好），用户已定枚举 |
| 本轮 | C 组按论文形式确定：**0–100 分**；不存 gain；撤回 pre_min/max |
| 本轮 | 采纳 `map_size` / `map_node_count`（仅描述统计，不进分数） |
| 本轮 | **第二张表（题级）现在就做**，long 格式，见 CSV_PLAN H 节 |
| 上一轮 | 发现 SMS 但**不做**（无老师划分子图），记入 STAT_PLAN 3A |
| 本轮 | C 组定稿：**百分制 0–100，不存题数，撤回 pre_min/max**（D27） |
| 本轮 | `major` 用云师大完整清单（D28） |
| 上一轮 | 题级表定稿：延迟后测**同表**，long 格式（D29） |
| 本轮 | 定：测验只用**客观单选**，前/后/延迟**同一套题**（D30） |
| 本轮 | 定：`题目类型`拆为 `题型` + `内容维度` 两列（D31） |
| 本轮 | STAT_PLAN 补：二值题用 **KR-20**；选择题与概念图相关 **0.30–0.40** 作外部效度参照 |
| 上一轮 | **写 SPEC.md**（197 行，给 AI 读，只留结论与约束） |
| 本轮 | **修正 3.12a**：r=0.30–0.40 是引用他文，原文自身是 .71–.77，不可预设 |
| 本轮 | **新增 3.12b**：四指标公式与分类（同卷的唯一理由） |
| 本轮 | **新增 3.12c**：前测敏感性，Solomon 四组是标准解法但我们用不了，局限措辞已备 |
| 本轮 | 新增 5A：Taricani 论文的三个不可援引之处 |

> 补记：D10 与 D9 是互锁的。用户自标注 + 用户自抽检 = 同一判断标准贯穿全程。
> 若将来标注外包给他人，A 的抽检也必须换成同一批人，否则标准会分裂。

---

## 12. 运行期抽崩检测（D15 / D16）

### 12.1 为什么需要它

4.2.1 的模型是"运行期零人工"。代价是：**抽错了没人拦。**
检测的目的不是修正，而是**在给出错误分数之前意识到自己可能错了**。

### 12.2 先找现成方法（D15 的要求）

我查了三类：

**① 概念图质量指标（最相关，论文里就有现成的）**

`10.1109_tlt.2021.3103331.txt`（Kroeze et al., 2021）给了五个判据，前三个
**不依赖领域知识**（行 292–296 原文）：

> "The first three criteria provide an overview of the complexity of concept maps
> **without depending on domain knowledge or semantic content**, while the final
> two give an estimate of the extent of overlap between student and reference maps."

- **Density of concepts**：学生图概念数 / 参考图概念数
- **Density of propositions**：见原文公式
- **Matching structure**：最长连续命题链长度之比

**但这些是评学生图的，不是评目标图的。** 用于抽崩检测需要换个对象——
把"目标图 vs 原文"当作一对来算。**这算借用，不是原样搬。**

**② 信息抽取质量监控**

搜到的都是通用异常检测/漂移检测（传感器数据、医学影像），
**没有针对"从文本抽结构"的质量检测现成方案**。`gaps` 也大量报 `weak_support`。

**③ LLMOps 的模型监控**

[Oracle 的 LLMOps 综述](https://www.oracle.com/middleeast/artificial-intelligence/llmops/)
提到 "Model monitoring and drift detection: Monitor performance metrics and detect
issues with data direction and quality"。**但这是概念层面的，没有可直接用的实现。**

### 12.3 结论：没有成熟方法，回到自研（12.3 起是候选）

按 D15，"先找现成的，没有才自研" —— 结论是**部分可借，整体需自研**：

**可借鉴的骨头（有文献支撑）**
- 概念密度、命题密度、最长链（Kroeze 的三项无领域指标）——**用于衡量"抽出来的图形状是否像概念图"**
- 分布偏移的统计检验（通用做法，Z-score / KS 检验）

**必须自研的肉（本场景特有）**
- 孤立概念、孤立连接词、概念过度复用
- 双次抽取一致性
- 开发期基线对照

### 12.4 检测到之后怎么办（D16 已定）

用户定：

> "抽崩了加一个警告框提示学生可以尝试重抽，但也允许学生继续学习。"

**这条设计有一个必须想清楚的点：**

警告框对**学生**说什么？学生不懂"抽取质量"。所以说人话：

- ❌ "抽取置信度低于阈值" —— 学生看不懂
- ✅ "这份材料的自动分析可能不够准确，你可以换个文件重试，或者继续练习"

**并且必须明确后果**：测验模式下若继续，分数可能不可靠。
**所以测验模式应该默认不允许在警告下计分**，学习模式则放行。

### 12.5 警告下的计分规则（D18）——已定

用户定：**照常计分，但加一个布尔字段表示可能不准确，统计时自己筛选。**

**这个决定的优点**（记录下来）：
它把"是否可信"的判断**交给了研究者**，而不是让系统替研究者决定。
这与 D17 的立场一致——系统不越权替人做判断。

**字段设计的最小要求**（不写契约，只记语义）：
- 布尔：`可能不准确`
- **同时存触发原因**（用户已同意，D18 补充）：
  - 触发了哪几条信号（S1 / S2 / S3 / S4，多选）
  - 每条信号的**实际值**与当时的阈值
  - 只存一个布尔等于丢掉了"为什么不准确"，事后无法复核

**为什么连实际值一起存**：阈值会随学科调整（12A.5）。
若只存"触发了 S2"，半年后无法反推当时是否误报。
**存值才能重算，存布尔只能相信。**

**重抽记录：并存（D23 已定）**

同一份教材被重抽后，两次记录都保留，不覆盖。

**理由（比"是交互数据"更实用的一条）：**
重抽是**唯一能直接检验检测器是否有效的证据**——
如果第一次报警、第二次不报警，说明信号抓到了真实的不稳定；
如果每次都报警，说明阈值定错了。
**覆盖掉就等于把验证材料销毁了。**

---

## 12A. 抽崩检测的具体建议（D20）

用户问"那抽崩检测你的建议是什么"。**先给结论，再给理由和反证。**

### 12A.1 结论：用三项自洽性 + 一项分布基线，**不用一致性当置信度**

| 信号 | 具体做法 | 成本 | 依据 |
|---|---|---|---|
| **S1 孤立概念** | 抽出但没有任何命题用到的概念占比 | 0 | 自研（无文献） |
| **S2 连接词覆盖** | 实际用到的连接词数 / 词表长度 | 0 | 自研 |
| **S3 概念过度集中** | 单概念出现频次 / 总命题数，超阈值报警 | 0 | 自研 |
| **S4 开发期基线对照** | 命题数/千字、概念长度分布的 Z-score | 0 | 通用统计，配合你的标注 |
| **S5 双次抽取一致性** | 只作为**辅助确认**，不作为置信度 | ×2 推理 | 见 12A.2 |

**优先级：S1–S4 必做（纯统计，零成本）；S5 可选做（贵，且不可单独信）。**

### 12A.2 🔥 重要反证：一致性**不能**当置信度

我原本想把"双次抽取一致性"当主力信号。**查证后必须收回这个想法。**

arXiv:2607.08065（Ding et al., 2026, *When LLMs Agree, Are They Right?*）摘要原文：

> "These systems share a key assumption: that consistency — agreement among
> judges, or among a model's own samples — indicates correctness.
> **We show this assumption is unreliable. Agreement is not accuracy**: a model
> can agree with itself ... out of shared bias, a memorized heuristic, or an
> option-position prior rather than truth."

数据：**265,000 个样本**，53 个 runner。

> "agreement is a positive but **weak** predictor (rho 0.20–0.59 ...)"
> "worst — over-confident yet no more accurate — for the most consistent
> frontier model (agreement >= 0.8 on 77% of GPQA case-result entries,
> **48% of those wrong**)."

**翻译成对我们的含义**：模型可以在**同一个错误上稳定地重复**。
两次抽取一致，可能只是"稳定地错"。

**所以 S5 的正确用法是：不一致 → 一定有问题；一致 → 不能证明没问题。**
它只能做**否定证据**，不能做**肯定证据**。这条要写进实现注释和 WHY.md。

### 12A.3 那 UIE 自带的 probability 能用吗？

**不能当主力，原因很具体：**

UIE 每条结果带 `probability`，但它是**训练时学到的置信度**，没有任何证据表明
它在"教材→概念图"这个分布外场景下是**校准过的**。
Kroeze 那篇的做法可以对照——它们不用模型置信度，而用**图结构指标**（见 12.2）。

**建议**：先把 probability 记下来（免费），但**不参与报警决策**。
等开发期有了标注数据，再实测它的校准性（画 reliability diagram）。
**这是 D11"先搭再看"的直接应用。**

### 12A.4 为什么 S1–S3 值得信

它们的共同点是：**不依赖模型判断，只依赖抽取结果自身的一致性。**

- S1 孤立概念：概念抽了、关系没抽到 → 概念图**形状**不对
- S2 连接词覆盖：词表给了 20 个只用 2 个 → 要么文本单一，要么没抽全
- S3 概念过度集中：一个词占 80% 命题 → 典型"万金油"退化

**这三条都不需要知道正确答案，只需要知道"抽出来的东西像不像概念图"。**
这正是 Kroeze 三项指标的精神（"without depending on domain knowledge"）。

### 12A.5 建议的阈值来源

**不要拍脑袋定阈值。** 做法：

1. 开发期用你的标注教材跑一遍，记录 S1–S4 的**实际分布**
2. 取分布的分位数作为阈值（如 P5/P95 为异常）
3. **阈值写进配置，不硬编码**——因为换学科后分布会变

**这条也与 D11 一致：先有数据，再定阈值。**

---

## 12B. 无人值守的局限（必须承认）

即使做了上述检测，仍有一类错误**检测不到**：
**抽得齐全、结构也合理，但命题内容是错的**（比如把"导致"抽成"包含"）。

这类错误在**只有抽取结果、没有原文对照**的情况下不可发现。
S1–S4 都看不到它，因为它不影响图的形状。

**这意味着 D9（开发期校正）是唯一能覆盖它的手段。**
所以：**检测的价值是"兜底"，不是"替代标注"。**

---

## 13. 参考文献库（供论文写作引用）

> 说明：本节只登记**本项目实际引用过的论点及其出处**，
> 不做完整文献综述。每条注明"用在哪"，写论文时可直接取用。
> 著录信息取自 `docs/research/papers/` 下各 PDF 的原文首页与 DOI。

### 13.1 方法论来源（Kit-Build 与评分口径）

**[P1] Pailai, J., Wunnasri, W., Yoshida, K., Hayashi, Y., & Hirashima, T. (2017).**
The practical use of Kit-Build concept map on formative assessment.
*Research and Practice in Technology Enhanced Learning*, 12:20.
DOI: 10.1186/s41039-017-0060-x
本地：`docs/research/papers/10.1186_s41039-017-0060-x.txt`

**提供本项目的核心口径：**
- 命题级精确匹配（proposition level exact matching）的定义
- **三种错误链**：lacking / excessive / leaving link（行 235–240）
- **评分公式**：正确命题数 / 目标命题数，取值 0~1（行 676–679）
- **"部分分"是别人系统的做法**，Kit-Build 刻意不含 synonym matching（行 371–378 + Table 1）
- leaving link 的教学解读："learners do not understand the linking word"（行 264–266）

---

**[P2] Khudhur, N., Furtado, P. G. F., Hayashi, Y., & Hirashima, T. (2026).**
From learner-built to expert concept maps: An evaluation of the effects of
closed concept map recomposition on learning.
*Research and Practice in Technology Enhanced Learning*, 21:21.
本地：`docs/research/papers/10.58459_rptel.2026.21021.txt`

**提供：**
- Kit-Build 三步流程原文（行 265–269）：专家建图 → 拆成零件 → 学生重组
- **学习模式的迭代循环**：DONE → 差异可视化 → Return → 重做，
  "until he/she successfully recomposes the expert map"（行 405–420）
- 界面交互细节：连接词用 gizmo 拖拽连线（行 375–380）

---

**[P3] Wunnasri, W., Pailai, J., Hayashi, Y., & Hirashima, T. (2018).**
Validity of Kit-Build Method for Assessment of Learner-Build Map
by Comparing with Manual Methods.
*IEICE Transactions on Information and Systems*, E101-D(4), 1141–1150.
本地：`docs/research/papers/10.1587_transinf.2017edp7177.txt`

**提供：**
- **自动评分的效度论证**：KB 分数与两种人工评分法（Novak 结构法、
  McClure 关系法）"had a very strong correlation"，可视为效度证据
- 明确说自动评分的优势：实时评估/反馈、减少评分者负担（行 108–110）

**⚠️ 对本项目的特殊意义**：这篇证明的是**KB 自动评分与人工评分一致**。
但本项目的人工基准被 LLM 替代，所以**这篇的效度链条在我们这里断了一环**——
必须在 WHY.md 里正面处理。

---

**[P4] Prasetya, D. D., Pinandito, A., Hayashi, Y., & Hirashima, T. (2022).**
Analysis of quality of knowledge structure and students' perceptions in
extension concept mapping.
*Research and Practice in Technology Enhanced Learning*, 17:14.
DOI: 10.1186/s41039-022-00189-9
本地：`docs/research/papers/10.1186_s41039-022-00189-9.txt`

**提供：**
- 命题级评分口径的复述（行 286："evaluated through the propositional level"）
- 分数 = 正确命题数 / 目标图命题总数（行 676）
- **Vanides et al. (2005) 的四级 rubric**（行 496–499）：
  `0 = incorrect; 1 = partially incorrect; 2 = correct with thin scientific
  understanding; 3 = scientifically correct`
  —— **本项目不采用**，因为它是人工评分 rubric，不是精确匹配
- EKB vs ESB 对照（开放式 vs 封闭式），支撑 D3 的方法论论证

---

### 13.2 错误分类与质量指标来源

**[P5] Kroeze, K. A., van den Berg, S. M., Veldkamp, B. P., & de Jong, T. (2021).**
Automated Assessment of and Feedback on Concept Maps During Inquiry Learning.
*IEEE Transactions on Learning Technologies*, 14(4), 460–473.
（页码已核对：PDF 首行 460，末页 473）
DOI: 10.1109/TLT.2021.3103331
本地：`docs/research/papers/10.1109_tlt.2021.3103331.txt`

**提供本项目的第四类错误：**
- **`reversed proposition` 判据定义**（行 313–320）：
  "identifying student propositions that contain identical concepts to those in
  the reference map, but either have a different label, or reverse the direction"
- 八类短板清单（行 301–305），其中 mislabeled 与 reversed 是**分开的两类**
- **三个不依赖领域知识的指标**（行 292–296）：Density of concepts、
  Density of propositions、Matching structure
  → 本项目把它们借用为**抽崩检测**的候选信号（12A）
- **反面证据**（行 655–660）：reversed 判据准确率低，因为"换个标签任何命题都能反向"
  → 本项目因**封闭连接词集**而免疫，这是 D4 的第二个收益

---

**[P6] Cline, B. E., Brewster, C. C., & Fell, R. D. (2010).**
A rule-based system for automatically evaluating student concept maps.
*Expert Systems with Applications*, 37(3), 2282–2291.
DOI: 10.1016/j.eswa.2009.07.044
本地：`docs/research/papers/10.1016_j.eswa.2009.07.044.txt`

**提供对照（本项目**不**采用其口径）：**
- CMT 的命题准确率规则（行 310–320）：如果"关系箭头反了但用了正确的逆关系"，
  仍然给**满分**
  > "if the concepts match, the relation arrow is reversed, and the appropriate
  > inverse relation is used"
- 这与本项目的四分类**相反**：我们把方向反转单列为错误类型。

**写论文时这是一个有用的对照点**：说明"方向错算不算对"在文献里本就有分歧，
本项目的选择有明确依据（封闭词表使方向可判定，故不必用逆关系兜底）。

---

### 13.3 其他工具性来源（不属于核心论证）

**[P7] Hirashima, T. et al. (2015).** 信息与系统教育，14(1)，13–27。
本地：`docs/research/papers/10.12937_ejsise.14.13.txt`
—— KB 方法的早期论述，用于背景。

**[P8] Ding, K. et al. (2026).** When LLMs Agree, Are They Right?
Auditing Self-Consistency and Cross-Model Agreement as Confidence Signals.
arXiv:2607.08065
—— **只用于否定"一致性可当置信度"**（12A.2）。265,000 样本，
一致性与正确性 rho 仅 0.20–0.59，高一致样本中 48% 是错的。

---

### 13.4 ⚠️ 引用时需要注意的三个硬约束

**① Wunnasri (P3) 的效度链条在本项目断了一环。**
它证明"KB 自动评分 ≈ 人工评分"，前提是**目标图由专家建**。
本项目目标图由 LLM 建，所以不能直接引用它的效度结论。
必须补充论证（D9 的开发期校正 + D10 的用户本人标注）。

**② Vanides 的四级 rubric（P4 引用）不能用。**
它是**人工评分**的 rubric（0/1/2/3 级），而本项目是**精确匹配**（二值）。
把两者混用会让评分口径无法自证。

**③ Cline 的"逆关系给满分"（P6）与本项目口径冲突。**
若论文里既引用 CMT 又说方向反转是错误，必须解释清楚为什么两者不同，
否则会被认为口径不一致。

---

## 14. 学科通用性：本轮新增的硬约束（D25）

用户定："**要适应所有学科**，开发和论文阶段的教材我自己找。"

这条看似只是"选什么教材"，实际上**推翻了第 3 节的一个隐含假设**，
必须单独讨论。

### 14.1 它推翻了什么

3.4 我建议"实验阶段用 `uie-base`，效果不够就 few-shot 微调"。
**那个建议隐含假设：只有一个（或少数几个）学科。**

**若目标是全学科通用，微调就是有害的**，理由有实证：

`arXiv:2401.05605`（Kalajdzievski, 2024, *Scaling Laws for Forgetting When
Fine-Tuning Large Language Models*）摘要原文：

> "PEFT strategies, such as Low-Rank Adapters (LoRA), **still suffer from
> catastrophic forgetting**. In particular, we identify a **strong inverse
> linear relationship** between the fine-tuning performance and the amount of
> forgetting ... **forgetting cannot be avoided through early stopping or by
> varying the number of parameters fine-tuned.**"

**含义：在学科 A 上微调得越好，在学科 B 上就可能越差。**
而且"早停"和"减少调参量"都救不回来。

**对一个要覆盖所有学科的系统，这几乎是致命的。**
微调优化的是"我见过的学科"，代价是"我没见过的学科"。

### 14.2 三种可能的应对，需用户选（或组合）

**方案甲：不微调，只靠零样本 + 连接词表**

- 优点：**没有任何领域偏向**，对新学科公平
- 缺点：零样本 F1 有限（3.1 那张表是 37~78，且来源是二手）
- 关键：**这个项目的容错本来就高**——目标图要人（用户）确认后才冻结。
  所以"抽得不全"可以由人工补，而不是必须靠模型准确率。

**方案乙：按学科分别微调，运行时按学科选模型**

- 优点：每个学科都能达到高 F1
- 缺点：需要**每个学科都标注**，与"用户自己找教材"的成本叠加；
  且学科边界模糊（"生物化学"算生物还是化学？）
- **实际上不可行**：用户没有能力标注所有学科

**方案丙：不微调，但把"连接词表"变成学科适配的主要手段**

- 核心洞察：**连接词表本身就是领域知识**
  （物理多"正比于/导致"，历史多"发生于/继任于"）
- 做法：每个学科**只换连接词表**，不换模型
- 优点：零训练成本，可解释，用户自己能配
- 缺点：连接词表的设计质量决定上限

**我的建议：甲 + 丙。** 即：**不微调，学科适配靠词表。**
理由：

1. 与 D7（不付费）、D11（先搭再看）都一致
2. 与你"标注都要标"不冲突——但**标注的用途变了**：
   从"训练数据"变成"评估数据"和"词表设计依据"
3. **这是可以写进论文的立场**：不微调 = 模型对学科中立，
   学科适配显式化在词表里，**可审计、可复现**。

### 14.2.1 已定：甲 + 丙，且论文用单一学科（D26）

用户定：**"同意你的方法，但单独做一个理论心理学的标注模型用于论文写作。"**

**这解决了 14.3 提出的效度难题，而且是优雅地解决：**

- **产品层**：保持全学科通用（D25），不微调，靠词表适配
- **论文层**：只用**理论心理学**一个学科做效度研究

**这样"跨学科分数不可比"就不再是问题**——
因为论文**根本不主张跨学科可比**，它只主张"在本学科内有效"。
**限制从"缺陷"变成了"研究范围的自然边界"。**

**⚠️ "标注模型"一词有歧义，我按下面理解，若不对请纠正：**

| 解读 | 含义 | 与本方案的关系 |
|---|---|---|
| **A. 标注数据集**（我采用） | 用户手工标注一批理论心理学教材，作为**评估基准** | ✅ 与"不微调"一致 |
| B. 用标注微调出的模型 | 训练一个小模型专用于心理学 | ❌ 与 D25 冲突（遗忘） |

**我按 A 理解并写入。** 若是 B，则第 14 节需要整体重写——
**这处必须先确认，它会改变整章结论。**

**若为 A，那么这批标注同时产出三样东西（一鱼三吃）：**

1. **效度评估的基准**：UIE 零样本在理论心理学上的真实 F1
2. **该学科的连接词表设计依据**：从标注里归纳出实际用到的关系类型
3. **抽崩检测的基线分布**（S4 的数据来源，见 12A.5）

**这三样都是论文需要的，不重复劳动。**

### 14.2.2 理论心理学作为研究场景的一个具体风险

理论心理学的文本特点是**高度抽象、以论证和概念辨析为主**，
与 Kit-Build 论文里常见的自然科学材料（光合作用、沉积作用）差别较大：

- 概念往往是**构念**而非实体（"自我效能""认知失调"）
- 关系往往是**理论关系**而非物理因果（"源于""修正""对立于"）
- **命题的"正确性"依赖理论立场**，不同流派可能给出不同连接词

**这不影响方案成立，但影响词表设计难度**——词表可能更难收敛。
**建议：先标一小批，看词表实际能收敛到多少个词，再决定标注规模。**
这与 D11（先搭再看）一致。

**这条要写进 WHY.md**：选择理论心理学作为场景，既是便利（作者熟悉），
也是挑战（抽象度高）。**承认挑战比掩盖更有说服力。**

### 14.3 但它带来一个新的效度问题（必须记）

若词表因学科而异，则**跨学科的分数不可直接比较**。
因为分母（目标图命题数）与词表强相关。

**所以论文里只能做"同学科内"的效度研究，不能声称"跨学科可比"。**
这条限制必须写进 WHY.md，否则会被质疑。

### 14.4 与 3.4 的冲突处理

3.4 写的"不够就微调"**不删除**，但**降级为"仅当确定单学科场景时的选项"**。
D25 下它不适用。

**记录理由**：保留旧判断及其失效条件，比直接删掉更有价值——
将来若项目收缩到单学科，这条立刻可用。

---

## 附：本次查证使用的资料来源

- `https://docs.typesafe.ai/models`
- `https://docs.typesafe.ai/concepts/state.md`
- `https://github.com/NandhaKishorM/laya`（README）
- `https://github.com/NandhaKishorM/laya/tree/main/research/benchmarks/feishu_zh`
- `https://hf-mirror.com/knowledgator/gliner-relex-large-v1.0`（gliner_config.json）
- `https://github.com/urchade/GLiNER`（docs/usage.md）
- `https://paddlenlp.readthedocs.io/zh/latest/model_zoo/taskflow.html`
- PaddleNLP PP-UIE 文档：
  `https://github.com/PaddlePaddle/PaddleNLP`
  → `llm/application/information_extraction/README.md`
- `https://github.com/opendatalab/MinerU/blob/master/docs/zh/index.md`
- `https://github.com/opendatalab/MinerU/blob/master/docs/zh/usage/quick_usage.md`
- `https://reactflow.dev/examples/interaction/touch-device`
- NetworkX graph_edit_distance 文档：
  `https://networkx.org/documentation/stable/reference/algorithms/`
  → `similarity.graph_edit_distance.html`
- 本地论文：`docs/research/papers/10.58459_rptel.2026.21021.txt`
- 本地论文：`docs/research/papers/10.1186_s41039-022-00189-9.txt`
- 本地论文：`docs/research/papers/10.1109_tlt.2021.3103331.txt`
  （Kroeze et al., 2021：reversed proposition 判据 + 三个无领域指标）
- 本地论文：`docs/research/papers/10.1016_j.eswa.2009.07.044.txt`
  （CMT：方向反转 + 逆关系时给满分，与 Kit-Build 口径不同，供对照）
- 自洽性反证：`https://arxiv.org/abs/2607.08065`
  （Ding et al., 2026：一致性不是正确性，48% 高一致性样本是错的）
- 语义熵相关（了解即可，本方案不采用）：
  `https://arxiv.org/abs/2405.20003`、`https://arxiv.org/abs/2607.16868`
- 灾难性遗忘：`https://arxiv.org/abs/2401.05605`
  （Kalajdzievski, 2024：LoRA 仍会遗忘，且早停/减参都救不回来）
  → 用于论证 D25 下**不微调**，
  见第 14 节

> 可靠性说明：UIE 的 F1 对比表来自二手技术文章整理，
> 官方 UIE README 在本机 404，未能取到一手数据，已在正文中标注。
> `hf-mirror.com` 可达（200），`huggingface.co` 不可达（000），
> 故所有 HF 相关证据均经镜像取得。

<!-- /@zone research -->
