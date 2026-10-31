<!-- @zone research -->
# README_PLAN 决策草稿与讨论记录
本文件记为什么这样定、方案怎么被否定、还剩什么没定。一行一条，不修饰，不写导读，不引别处。本文件不做文献综述，只登记本项目实际引用过的论点与出处，论文按 DOI 标在 docs/research/文献清单.md。
## 0 定位
Kit-Build 的三步流程是专家建目标图、把目标图拆成零件、学生用零件重组（10.58459_rptel.2026.21021.txt 行 265–268）。
本项目把第一步的专家换成 LLM，产品运行时只有两个角色：学生与 LLM。没有老师，也没有专家在场。
由此产生的核心张力：LLM 同时是出题人（目标图的来源）与阅卷标准的来源。评分口径、效度论证、抽崩检测全部围绕这条张力展开。
## 1 决策表
D1 技术栈 FastAPI 加 SQLite 加 React 加 TS 加 Vite 加 ReactFlow。理由：单人可维护，SQLite 省掉部署数据库。
D2 只判结构不判语义。理由：结构可枚举可复算，语义判断无稳定基准。
D3 学生只从 kit 重组，不自由建图。理由：这是 Kit-Build 的定义，也是分母可固定的前提。
D4 连接词固定词表。理由：防同义词漏判，并让方向反转可判定。
D5 输入包含扫描 PDF。理由：教材常见形态。
D6 文档解析走 MinerU 云服务，已定；披露要求已定为传什么、传给谁、为什么必须传三项。仍悬置：本地部署的前提条件。
D7 不订阅第三方 LLM 服务，用用户自己的 API key 调用并自付调用费（BYOK）。理由：不绑订阅、成本可控，一章约 0.08 元。
D8 编号空置，未使用。
D9 目标图效度用方案 A：开发期人工校正，运行期放行。理由：运行期零人工是产品前提。
D10 标注不用 LLM 预标，由两名编码者独立标注、互不可见，分歧由第三人裁定。理由：基准必须独立于模型，否则评估自我循环。
D11 先把系统搭出来再看抽取效果。理由：把模型效果这一变量留到有真实教材之后。
D12 两个共享层对称命名，契约层与实现层分开。
D13 不给部分分；错误分四类，方向反转独立成第四类。
D14 双模式：测验模式与学习模式。
D15 抽崩检测先找现成方法，没有再自研。
D16 抽崩只警告不阻断，允许学生继续。
D17 模式由学生自选，不由系统指定。
D18 警告下照常计分，另存触发信号与实际值。
D19 新增 CSV 导出，支持单个、多选、全选。
D20 抽崩检测 S1 到 S4 必做，S5 只作否定证据。
D21 模式在进画布前选定并锁定。
D22 导出 CSV 用 UTF-8 带 BOM。
D23 同一教材重抽的记录并存不覆盖。
D24 使用云解析时必须披露传输内容、接收方与原因，并允许不用云。
D25 产品面向全学科。
D26 不微调，学科适配靠连接词表；论文的效度研究只用理论心理学一个学科。
D27 学习效果分数用百分制 0 到 100，不存题数，撤回 pre_min 与 pre_max。
D28 专业字段用云师大完整专业清单。
D29 题级表用 long 格式，延迟后测与前后测同表，用 time_point 区分。
D30 测验只用客观单选，前测后测延迟测同一套题。
D31 题目类型拆成题型与内容维度两列。
## 1.1 固定连接词集
kit 的定义本身就是封闭零件集：概念卡与连接词卡都是有限的。既然学生只能从给定零件里挑，分母即目标图命题总数就是常量，分数才可跨人可比。
分数口径为满图匹配分，即学生图中正确命题数除以目标图命题总数，原文取值 0 到 1，本项目按百分制 0 到 100 存储与报告，比例只在公式内部使用。定义句原文：The learner map score is the ratio of the number of correct propositions in learner map to the number of propositions in the goal map（10.1186_s41039-017-0060-x.txt 行 676–677）。
注意此处常被误标到另一篇同前缀 DOI 的文件。10.1186_s41039-022-00189-9.txt 行 676 讲的是原图的第二次实验，与分数定义无关。
封闭词表另有两个收益：一是同义词不会漏判，二是方向反转变成可枚举判定。
另有 EKB 与 ESB 的对照实验（扩展式与封闭式概念图），支撑 D3 的方法论论证（10.1186_s41039-022-00189-9.txt 行 496–499 前后的实验设计）。
## 2 排除决策模型路线
Jev（docs.typesafe.ai）：只处理文本，上下文 64k 与 32k 两档，报价 42 美元每十亿 token，CJK 精度低；原语是 Choice、Score、Noul，属闭集判断而非开放三元组生成。
Laya（github.com/NandhaKishorM/laya）：自称 multilingual non-autoregressive decision engine，34037 stars，仓库 2026-09-18 创建；其自测中文成绩 20/64 与 64/64 两说，且仓库自承利益冲突。
GLiNER 与 RelEx：gliner-relex-large-v1.0 的 encoder 是 microsoft/deberta-v3-large，英文编码器，中文不适用；下载量 1253。
共同排除理由：这些模型解决的是闭集判断，本项目要的是从教材抽开放三元组，任务不同。
## 3 抽取引擎选型
PaddleNLP UIE 共有五个档位：base 为 12 层 768 隐层，medium 为 6 层 768，mini 为 6 层 384，micro 为 4 层 384，nano 为 4 层 312。
二手技术文章给出的零样本 F1：base 在金融 46.43、医疗 71.83、互联网 78.33。这些数字来自二手整理，官方 README 在本机 404，未取到一手数据，引用时必须标注这一点。
PP-UIE 有 0.5B、1.5B、7B、14B 四个尺寸，官方宣传口径是相对 UIE-Base 提升 66%。
本机实测：CPU 为 Ryzen 7 7735U、16 逻辑核、无 GPU、内存 15290 MB（当时可用约 3GB）、swap 4G 加 zram 14.9G。
早期建议实验期用 uie-base，需要更高精度时升级 PP-UIE 0.5B 并加白名单校验，算力不足时降档 base 到 mini；该建议已被云端 DeepSeek 的 deepseek-flash 取代，此处只作存档。
第 3 段早期曾建议效果不够就做 few-shot 微调。该建议已被 D25 降级：全学科目标下微调有害，实证是 arXiv:2401.05605 的结论 forgetting cannot be avoided through early stopping or by varying the number of parameters fine-tuned。原建议保留并标注失效条件，不删除。
## 4 目标图效度
三条路线。方案 A：开发期人工校正，运行期放行，已采用。方案 B：多模型互证，未采用，理由是成本翻倍且互证不能替代独立基准。方案 C：把封闭性作为结构性补救，作为 A 的补充而非替代。
4.2.1 用户原话：没有老师，标注由我自己提前标。D10 已把标注主体改为两名独立编码者加第三人裁定，原话只保留问题动机。于是运行期零人工，所有人工判断前移到开发阶段。
4.5 抽取引擎迁云端。本机 ONNX 版 UIE 有三处实测缺陷：情绪影响记忆只覆盖关系一侧；主语侧 pmax 仅 0.397，等于哑火；记忆包括感觉、短时、长时这句出现三个 span，两两成对抽出六条，其中三条方向相反。
少样本试验：0 例、1 例、3 例时 start pmax 分别为 0.000、0.995、0.990，说明给例子只解决哑火，不解决精度。
据此选定 DeepSeek 的 deepseek-flash 加 BYOK。成本：一章 1.2 万字约 0.08 元，命中缓存后约 0.03 元，2000 章约 60 元。
四条风险：接口无 seed 参数，结果不可复现；模型版本会变；空 content 需重试两次；抽崩时无人拦。
## 5 文档解析边界
MinerU 官方说明：纯文本不进解析流程；EPUB 走原生解析，本地 epub 用 DocVortex 的 Flash 档原生解析；服务分 Flash、Basic、Standard、Advanced 四档，扫描件至少要用 Basic。
本地部署需 torch 全家桶加 ONNX；Hugging Face 不可达时需设置环境变量 export MINERU_MODEL_SOURCE=modelscope。
D24 要求披露三件事：传什么、传给谁、为什么必须传；并明确可以不用云，改用本地部署或纯文本输入。
## 6 流程
离线段：txt 与 epub 直接读文本层，扫描件经 MinerU 云服务解析；抽取一律调云端大模型（OpenAI 兼容接口，当前 DeepSeek），早期本地 UIE 与 ONNX 方案已停用；得到候选三元组后人工抽检，冻结为目标图，再拆 kit。
在线段：学生拖拽重组并提交，逐条查表，分数等于正确命题数除以目标图命题总数，再出报告。
6.2 为什么查表不做图匹配：图编辑距离是 NP-hard，且本项目要的不是最近似匹配而是逐条命题是否精确存在，查表即得。
6.3 触摸屏：ReactFlow 官方触摸设备示例给了三条做法，点两个 handle 完成连线、把 handle 加大到易点、用 connectOnClick 把连线改成点选式。本项目取点选式连线，即打开 connectOnClick 并把 handle 加大，触摸屏下点选比拖拽可靠。
## 7 feature 切分
主 feature 依次是 ingest、extract、kit、rebuild、score、export，另有两个横向层：契约层与前端共享层。
7.1 ingest 职责：从文件得到文本。边界：不做抽取、不判对错。解析结果缓存在此处，且不进 git，已定。悬置一项：云解析失败时的行为，报错还是落回本地。
7.2 extract 职责：从文本得到候选三元组。边界：不做人工裁定、不冻结。待决两项：长文切分策略；是否允许先把概念候选给学生。
7.3 kit 职责：冻结目标图并拆成零件。冻结规则：冻结后不可静默修改，改动须走显式版本；目标图可 v1、v2，但 v1 一旦有学生用过就不能改，因此每次提交必须记录引用的是哪个版本。驳回的候选要留档，它是 UIE 精度的免费标注数据。
7.4 rebuild 职责：学生拖拽重组的画布与提交。边界：不评分、不在前端给任何对错提示。隔离理由：前端一旦知道对错，就等于把评分口径复制到两处，日后必然不一致。
7.4.1 双模式。学习模式允许提交后看差异并反复重做，原句为 the learner iterates through a loop between recomposing the map and visualizing the differences until he/she successfully recomposes the expert map（10.58459_rptel.2026.21021.txt 行 417–420）。测验模式提交即锁定，分数有效，差异可视化照给。每文本上限 35 到 40 分钟，超时自动提交，两组同。两模式都显示差异可视化，差别只在提交后能否返回改图。
两模式的差别只有一处：提交后能否返回改图。分数是否有效与是否循环到一致都由这一条派生：测验模式不返回，故不循环、分数有效；学习模式可返回，故循环到一致、分数无意义。差异可视化组件两模式共用，两模式都显示。
7.4.2 模式由学生自选，三条理论锚点为人机协同、有意义学习、人本主义立场。风险记在功能说明里，处置方式是记录 mode 字段，不是替学生限制。
7.4.3 模式在建记录时写入，即进画布前锁定、不可中途切换，避免切换导致分数口径混乱。
7.5 score 职责：逐条查表算分并给诊断报告。分数只算正确命题比例，四类错误只进诊断报告，不参与加减分。
7.5.1 不给部分分。原文口径是精确匹配，同义词不算对，Kit-Build 在对比表中用 E（exact matching）而不用 S（synonym matching）。别的系统可给部分分（行 371–378 专门讨论这种做法），本项目不走这条。
7.5.2 三类错误链出自 Pailai 等 2017，第四类方向反转出自 Kroeze 等 2021，合起来是本项目的四分类。
lacking link：目标图有、学生图没有，中文界面名缺失连接。
excessive link：学生图有连接，但至少一端概念与目标图不同，中文界面名多余连接。
leaving link：连接词放了但没连到任何概念，中文界面名游离连接。
三者的定义在 10.1186_s41039-017-0060-x.txt 行 235–239。
leaving link 的教学解读原文是 This link indicates that the learners do not understand the linking word，位置在该文件行 249。常被误标成行 264–266，那一段讲的是 tagged number 与虚线权重。
游离连接是独立诊断信息：学生把连接词卡丢在画布上却不知往哪连，与连错是两种认知状态。
7.5.3 方向反转的文献依据。Pailai 的三分类里确实没有它，因为 excessive 的定义要求至少一端概念不同，而方向反转时两端概念都在图里。
但概念图评分文献里有独立名称 reversed proposition，判据原文见 10.1109_tlt.2021.3103331.txt 行 313–320：identifying student propositions that contain identical concepts to those in the reference map, but either have a different label, or reverse the direction of the proposition。
该文的八类短板清单在行 298–303，把 mislabeled 与 reversed 分作两类：typos, missing concepts, superfluous concepts, mislabeled propositions, reversed propositions, missing propositions, superfluous propositions, and shortcuts。
7.5.4 一条反面证据。同一文献行 654–658 报告 reversed 判据准确率偏低，原文为 The only exceptions were the reversed proposition and shortcut criteria. The low accuracy of the reversed proposition criterion can be explained by the fact that with an appropriate change of label, any proposition in a concept map can be reversed。
含义：开放词汇下方向难以自动判定，换个标签方向就通了。本项目场景免疫，因为 D4 保证连接词来自固定词表，学生不能自由输入，(A 关系 B) 与 (B 关系 A) 都能在候选集里枚举。
这是可写进论文的论据：封闭连接词集不只防同义词，还让方向反转变得可判定。这是 D4 的第二个收益，值得单独作为贡献点。
7.5.5 四分类定案。缺失连接、多余连接、游离连接三类整块引 Pailai 等 2017；方向反转引 Kroeze 等 2021。两个来源各自内部自洽，不产生定义冲突，这正是把方向反转塞进 excessive 做不到的。
四类都只影响诊断报告，不影响分数。
7.6 契约层职责：只定义数据结构、字段语义、纯函数签名、Protocol。边界：不含业务逻辑、不含 IO、不做契约到契约以外的转换。
契约被第二个 feature 消费即冻结，改动需先给旧到新的对照、影响范围、迁移方式。
契约域怎么切仍悬置：按数据流切成文本、三元组、目标图、零件包、提交、报告，还是按 feature 边界切。
7.7 export 职责：把测验结果按单个、多选、全选导出 CSV。独立于 score 的理由：它需要跨记录批量查询与批量交互，扩展方向（xlsx、json）也独立。
依赖方向必须单向：export 读 score 已产出的报告，不重算分数。若自己算分，导出的分数与界面显示的分数可能不一致，这是最隐蔽的一类 bug。
编码用 UTF-8 带 BOM（D22）。不带 BOM 时 Excel for Windows 会按本地 ANSI 猜编码，中文列名与中文概念名都乱码。代价是部分 Linux 工具会把 BOM 当内容的一部分，读取时需容忍。
7.7.1 字段设计依据四篇论文实际收的变量，原设计只有七个字段，不够做严谨量化分析。
标识与版本组：提交时间、被试标识（可匿名）、教材标识与目标图版本、连接词表标识与版本、模式、抽取批次标识。连接词表必须记版本，因为词表换学科就变，不记录则跨批不可比。
评分结果组：正确命题数与目标命题总数、分数 0 到 100、四类错误计数、触发的信号及其实际值与当时阈值。
学习效果组：前测得分、后测得分、延迟后测得分三个原始分；normalized change 及其分子分母都由这三个原始分现算，不落库；time-on-task 秒数由建图起止两个时间戳算得，也不单独存字段；导出时把算好的值写进 CSV。time-on-task 的依据是 Khudhur 等 2026 行 29 讨论 time-on-task 不预测成绩，这本身是结论。
协变量组：性别、年龄、年级或学段、班级或群组、专业或学科背景。前四项的依据是 Kroeze 等 2021 的固定效应设定（行 521–523），班级的依据是同一文献的随机效应设定（行 486–487）。
三条设计原则。一是存原始量不存派生量：normalized change、分数、时长都是派生量，存下来就固化公式选择，所以数据库只存分子分母、时间戳、原始计数；导出 CSV 时才把派生值写进 score 列，只作核对，不参与分析。二是班级必须存，它是随机效应，不存就做不了多层模型。三是题级数据不在被试级表里，要另做一张题级表，否则后期补不上。
record_id 按顺序 1、2、3 唯一编号。
7.8 跨 feature 待议点。人工抽检的落点已定：放进 kit 内部，因为冻结与裁定是同一动作的两面，拆开会出现谁有权冻结的模糊地带。云解析属不属于 ingest：属于，它只是换了一种从文件得到文本的手段。前端代码怎么分：重构与评分都有前端，共享组件走前端共享层，这条不要硬套后端契约约定。
7.9 前端组件共享。后端约定 feature 间禁止互相 import，照搬到前端会出事，因为 rebuild 与 score 都要画概念图，缩放平移、节点样式、连线渲染是同一套代码，而 UI 组件不是契约。
三种主流做法。一是抽成独立包，适合跨项目复用，本项目是单体应用，没有第二个项目要用，不适用。二是 Feature-Sliced Design 的 shared 层，规则是 slice 只能引用严格更下层的 slice，且 App 与 Shared 两层的 segment 可以自由互相引用，Shared 不含业务逻辑；这与契约层语义一致。三是 shadcn/ui 的复制模式，适用于复制外部库源码，一次性导入后不同步，本项目共享的是自己正在迭代的组件，复制会导致改一处忘一处。
7.9.3 命名与边界。契约层放契约，无实现无 IO；前端共享层放组件、样式、通用交互封装，无业务逻辑。
前端共享层的判定规则一句话：放的是知道怎么画但不知道对错的东西。一旦某个组件需要知道这条命题对不对、这个词在不在词表里，它就不属于共享层。
由此得一条硬约束：前端共享层不能引用契约层的业务类型，节点组件只接受文本与位置，不接受命题对象。
前端目录建议：canvas 放 React Flow 封装，layout 放页面骨架，atoms 放按钮输入框标签警告框，styles 放全局样式与主题变量。页面骨架可以共享，概念图节点不算业务，React Flow 封装集中在 canvas 一个子目录。
## 8 标注计划
现状：没有现成标注数据，由两名编码者独立标注（D10）。
谁标的矛盾由此解决：没有老师，标注者不是模型，是两名独立编码者。若标注由 LLM 预标，正确答案与生成答案同源，评估变成自我循环。
双人独立标注加第三人裁定的三个后果：基准独立于模型，评估有效；分歧由第三人裁决，判断标准收敛成一条；人力成本落在研究侧，不落在产品用户身上。
这不冲突于系统没有老师：标注发生在离线准备阶段，是研究行为；产品运行时确实只有学生与 LLM。
标注内容四类：哪些词算节点；每个命题用词表里的哪个连接词；三元组结构；哪些内容不该进图，作为负例用来测精度而非召回。
冷启动顺序（D11）：先搭系统（ingest、kit、rebuild、score 都不依赖标注），用户提供教材跑一遍零样本抽取，看效果再评估是否降档。含义是抽取效果不好时能立刻区分是抽取不行还是流程设计不行。
已定：本科难度；论文场景只做理论心理学单学科；产品覆盖全学科。已定：实验对照用两份材料（文本 1 与文本 2）。仍悬置：产品侧首批录入的教材给几份，以及将来扩展到其他学科的顺序。
## 8A 其余结构决策
人工校正放在 kit 内部，不独立成 review feature。
MinerU 云解析结果要缓存，且缓存不进 git。
目标图可以 v1、v2，但 v1 一旦有学生用过就不能改。
驳回的候选留档，作为 UIE 精度的免费标注数据。
中途保存与续做允许；每文本上限 35 到 40 分钟，超时自动提交，两组同。
提交后能否改按模式分：测验模式锁定，学习模式可循环。
目标图 v1 用过就不能改的技术后果：kit 必须记录每次提交引用的版本，否则无法回答这份分数按哪版目标图算。
## 9 风险
LLM 生成的目标图有错，效度崩、学生答对被判错，缓解是方案 A 的开发期校正。
零样本抽取 F1 不足，整条离线链路失效，缓解是先小规模实测再决定。
本机内存不足（当时仅 3GB 可用），模型加载或推理失败，缓解是用户称内存低为暂时现象，且已部署过。
MinerU 云服务不可用或政策变动，扫描件链路断，缓解是保留本地部署方案并记录 modelscope 变量。
连接词表设计不合理，学生理解困难甚至歧义，缓解是词表需小规模试用后迭代。
触摸屏连线手感与鼠标差异大，学生挫败，缓解是按官方建议加大 handle 并改用点选式连线。
## 10 未决问题
已关闭（写结论不再讨论）：目标图效度走 A；标注由两名编码者独立标；先搭系统再看效果；评分不给部分分；错误链用原文三类加中文界面名；方向反转归四分类；双模式；人工校正落在 kit 内；解析缓存不进 git；目标图用过即锁；驳回候选留档；中途保存允许、每文本 35 到 40 分钟上限加超时自动提交；前端共享层命名与三条边界；抽崩检测无成熟实现故自研；抽崩后警告并允许继续；警告下照常计分加信号标记；S1 到 S4 必做 S5 只作否定证据；新增 CSV 导出并独立成 export 这个 feature；模式进画布前锁定；BOM；重抽并存；披露 MinerU；产品全学科而论文用理论心理学；学科适配不微调靠词表。
标注一词在本文件按标注数据集理解，不用微调出的小模型，故无歧义、不开放。
细节项：CSV 字段详表；连接词表是否需要内置学科模板。抽样已定：便利样本加个体随机与区组随机。仍悬置：伦理审查与知情同意，若真收性别年龄一般需要，必须在收数据前决定。
## 11 变更记录
初稿：建立选型记录，排除 Jev、Laya、GLiNER，确定 UIE 路线。
后续各轮依次完成：关闭效度路线与标注主体；把 feature 章节从清单改写为逐个介绍；重读论文核实评分口径与三种错误链；重写运行期零人工的说明；命名定案与双模式；发现 reversed proposition 有独立文献；新增抽崩检测调研；四分类定案与模式学生自选；给出抽崩检测具体方案并记录一致性不等于正确；share 改名为两个对称层；export 提为独立 feature；警告不存布尔而存信号加实际值；D21 至 D25；新增第 14 节记灾难性遗忘证据并降级微调建议；D26；重设计 CSV 字段为四组约二十项；新建统计与字段两份计划文件；B9 与 B10 改为独立 0/1 列加中文列名；学习效果改 0 到 100 分不存 gain；采纳 map_size 与 map_node_count 仅作描述统计；题级表现在就做；D27 至 D31；STAT_PLAN 补 KR-20 与外部效度参照并修正引用归属；写出机器读的规范文件；新增四指标公式与前测敏感性两节；新增三个不可援引之处。
一处补记：标注与抽检互锁。两名编码者独立标注、第三人裁定分歧，抽检由同一批人做，等于同一判断标准贯穿全程；若将来标注外包，抽检也必须换成同一批人，否则标准分裂。
## 12 运行期抽崩检测
需要它的理由：运行期零人工的代价是抽错没人拦。检测的目的不是修正，而是在给出错误分数之前意识到自己可能错了。
找现成方法的三条线。一是概念图质量指标，Kroeze 等 2021 给了五个判据，前三个不依赖领域知识，原文在行 292–296：The first three criteria provide an overview of the complexity of concept maps without depending on domain knowledge or semantic content, while the final two give an estimate of the extent of overlap between student and reference maps。三项分别是概念密度（学生图概念数除参考图概念数）、命题密度（见原文公式）、匹配结构（最长连续命题链长度之比）。但这些是评学生图的，用于抽崩检测需把对象换成目标图与原文这一对，属借用而非原样搬。
二是信息抽取质量监控，搜到的都是通用异常检测与漂移检测，针对从文本抽结构的质量检测没有现成方案。
三是 LLMOps 的模型监控，只有概念层面的 model monitoring and drift detection，没有可直接用的实现。
结论：部分可借，整体需自研。可借的是三个无领域指标与分布偏移的统计检验（Z-score、KS）；必须自研的四项是孤立概念、连接词覆盖、概念集中度、开发期基线对照；第五项双次抽取一致性只作辅助确认与否证证据，不列入四指标。
检测到之后：只警告不阻断（D16）。给学生的话要人话，不能说抽取置信度低于阈值，要说这份材料的自动分析可能不够准确，可以换个文件重试或继续练习。后果要写明：测验模式下继续则分数可能不可靠。
D18 计分规则：照常计分并另存可能的不可靠标记。这个决定的优点是是否可信的判断交给研究者，而不是系统替人决定。
字段设计最小要求：不设单一布尔报警列，只存触发了哪几条信号、每条信号的实际值与当时阈值。只存一个布尔等于丢掉为什么不准确，事后无法复核；阈值会随学科调整，只存触发过哪条，半年后无法反推当时是否误报。存值才能重算，存布尔只能相信。
重抽记录并存（D23）。它是唯一能直接检验检测器是否有效的证据：第一次报警第二次不报警说明信号抓到了真实的不稳定，每次都报警说明阈值定错。覆盖掉等于销毁验证材料。
## 12A 具体建议
S1 孤立概念：抽出但没有任何命题用到的概念占比。零成本，自研。
S2 连接词覆盖：实际用到的连接词数除以词表长度。零成本，自研。
S3 概念过度集中：单概念出现频次除以总命题数，超阈值报警。零成本，自研。
S4 开发期基线对照：命题数每千字、概念长度分布的 Z 分数。零成本，通用统计配合标注。
S5 双次抽取一致性：只作辅助确认，不作置信度，成本是两倍推理。
优先级：S1 到 S4 必做，S5 可选且不可单独信。
12A.2 重要反证：一致性不能当置信度。arXiv:2607.08065（Ding, K., 2026, When LLMs Agree, Are They Right?）摘要原文说 these systems share a key assumption, that consistency indicates correctness, and we show this assumption is unreliable, agreement is not accuracy。数据规模 265,000 个样本、53 个 runner；一致性与正确性是正相关但弱的预测（rho 0.20 到 0.59）；最一致的前沿模型在 GPQA 的 77% 条目上一致度不低于 0.8，其中 48% 是错的。
含义：模型可以在同一个错误上稳定重复，两次一致可能只是稳定地错。所以 S5 的正确用法是不一致就一定有问题，一致不能证明没问题，只作否定证据。这条要写进实现注释与功能说明。
12A.3 UIE 自带 probability 不能用吗。不能当主力，因为它是训练时学到的置信度，没有任何证据表明它在教材到概念图这个分布外场景下是校准过的。Kroeze 等的做法是不用模型置信度而用图结构指标。建议先把 probability 记下来（免费），不参与报警决策，等有标注数据后画可靠性图实测校准性。
12A.4 为什么 S1 到 S3 值得信：它们不依赖模型判断，只依赖抽取结果自身的形状。概念抽了关系没抽到，图形状不对；词表给了二十个只用两个，要么文本单一要么没抽全；一个词占八成命题，是典型的万金油退化。这三条不需要知道正确答案，只需要知道抽出来的东西像不像概念图。
12A.5 阈值来源：不要拍脑袋。开发期用标注教材跑一遍，记录 S1 到 S4 的实际分布，取分位数作阈值（如 P5 与 P95），阈值写进配置不硬编码，因为换学科分布会变。
## 12B 无人值守的局限
仍有一类错误检测不到：抽得齐全、结构也合理，但命题内容是错的，例如把导致抽成包含。这类错误在只有抽取结果没有原文对照时不可发现，S1 到 S4 都看不到它，因为它不影响图的形状。
这意味着开发期校正（D9）是唯一能覆盖它的手段。检测的价值是兜底，不是替代标注。
## 13 参考文献
说明：本节只登记本项目实际引用过的论点及其出处，著录信息取自各论文首页与 DOI，行号指向本地纯文本。
P1 Pailai, J., Wunnasri, W., Yoshida, K., Hayashi, Y., & Hirashima, T. (2017). The practical use of Kit-Build concept map on formative assessment. Research and Practice in Technology Enhanced Learning, 12:20. DOI 10.1186/s41039-017-0060-x。本地文件 10.1186_s41039-017-0060-x.txt。
P1 提供本项目的核心口径：命题级精确匹配的定义；三种错误链在行 235–239；评分公式定义句在行 676–677、取值 0 到 1 的句子在 681–682（679–680 为页眉与空行），原文取值 0 到 1，本项目按百分制；部分分是别的系统做法，Kit-Build 刻意不含同义词匹配，见行 371–378 与对比表；leaving link 的教学解读在行 249。
P2 Khudhur, N., Furtado, P. G. F., Hayashi, Y., & Hirashima, T. (2026). From learner-built to expert concept maps: An evaluation of the effects of closed concept map recomposition on learning. Research and Practice in Technology Enhanced Learning, 21:21。本地文件 10.58459_rptel.2026.21021.txt。
P2 提供：三步流程原文在行 265–268；学习模式的迭代循环在行 417–420；连接词用 gizmo 拖拽连线的交互细节在行 375–380；三阶段测量在行 576–579；normalized change 在行 564–568；time-on-task 的讨论在行 29。
P3 Wunnasri, W., Pailai, J., Hayashi, Y., & Hirashima, T. (2018). Validity of Kit-Build Method for Assessment of Learner-Build Map by Comparing with Manual Methods. IEICE Transactions on Information and Systems, E101-D(4), 1141–1150。本地文件 10.1587_transinf.2017edp7177.txt。
P3 提供自动评分的效度论证：KB 分数与两种人工评分法（Novak 结构法、McClure 关系法）高度相关，两种人工法的出处原文在该文件行 127–129；自动评分的优势是实时评估与反馈、减少评分者负担，在行 108–110。
P3 对本项目的特殊意义：它证明的是 KB 自动评分与人工评分一致，前提是目标图由专家建。本项目目标图由 LLM 建，所以这条效度链断了一环，必须在功能说明里正面处理。
P4 Prasetya, D. D., Pinandito, A., Hayashi, Y., & Hirashima, T. (2022). Analysis of quality of knowledge structure and students' perceptions in extension concept mapping. Research and Practice in Technology Enhanced Learning, 17:14. DOI 10.1186/s41039-022-00189-9。本地文件 10.1186_s41039-022-00189-9.txt。
P4 提供：扩展概念图的两种模式对照，支撑 D3 的方法论论证；Vanides 等 2005 的四级 rubric 在行 496–499，取值为 0 不正确、1 部分不正确、2 正确但理解单薄、3 科学上正确，本项目不采用，因为它是人工评分 rubric 而非精确匹配；TAM 的量表设计在行 505–520，六点 Likert，含 3 个 PEOU 条目、3 个 PU 条目、1 个 BI 条目；前测同质性检验在行 278–279，p 等于 0.445；Shapiro-Wilk 正态性检验在行 530–531；Cronbach's alpha 判据 0.7 在行 780–785。
命题级评分的说法原文 the learner maps will be evaluated through the propositional level 在 10.1186_s41039-017-0060-x.txt 行 286，不在此篇。此处易误标，引用前先核文件名。
P5 Kroeze, K. A., van den Berg, S. M., Veldkamp, B. P., & de Jong, T. (2021). Automated Assessment of and Feedback on Concept Maps During Inquiry Learning. IEEE Transactions on Learning Technologies, 14(4), 460–473. DOI 10.1109/TLT.2021.3103331。本地文件 10.1109_tlt.2021.3103331.txt。
P5 提供：reversed proposition 的判据定义在行 313–320；八类短板清单在行 298–303，其中 mislabeled 与 reversed 是两类；三个不依赖领域知识的指标在行 292–296，分别指概念密度、命题密度、匹配结构，本项目借为抽崩检测的候选信号；反面证据在行 654–658，reversed 判据准确率低，原因是换个标签任何命题都能反向，本项目因封闭词表而免疫；统计模型的固定效应与随机效应设定在行 486–487 与 521–523；评分者一致性在行 530–531，一致率 89% 而 Cohen's kappa 只有 0.47，同文行 539–540 另有两组 93% 对应 0.88、74% 对应 0.56 的结果，引用时别混。
P6 Cline, B. E., Brewster, C. C., & Fell, R. D. (2010). A rule-based system for automatically evaluating student concept maps. Expert Systems with Applications, 37(3), 2282–2291. DOI 10.1016/j.eswa.2009.07.044。本地文件 10.1016_j.eswa.2009.07.044.txt。
P6 提供对照，本项目不采用其口径：CMT 的命题准确率规则在行 310–320，若关系箭头反了但用了正确的逆关系，仍给满分，原文为 if the concepts match, the relation arrow is reversed, and the appropriate inverse relation is used。这与本项目四分类相反，本项目把方向反转单列为错误类型。
写论文时这是有用的对照点：方向错算不算对在文献里本就有分歧，本项目的选择有明确依据，即封闭词表使方向可判定，不必用逆关系兜底。
P7 Alkhateeb, M., Hayashi, Y., Rajab, T., & Hirashima, T. (2015). Comparison between Kit-Build and Scratch-Build Concept Mapping Methods in Supporting EFL Reading Comprehension. Information and Systems in Education, 14(1), 13–27. DOI 10.12937/ejsise.14.13。本地文件 10.12937_ejsise.14.13.txt。
P7 的用途是背景与对照：它比较的是 Kit-Build 与 Scratch-Build 两种建图法在英语阅读理解上的效果，不是 Kit-Build 的方法学论述。一作是 Alkhateeb，不是 Hirashima，引用时不要写成 Hirashima 等。
P8 Ding, K. (2026). When LLMs Agree, Are They Right? Auditing Self-Consistency and Cross-Model Agreement as Confidence Signals. arXiv:2607.08065。
P8 只用于否定一致性可当置信度：265,000 个样本，一致性与正确性的相关系数只有 0.20 到 0.59，高一致样本中 48% 是错的。该文为独著，引用时不要写成 Ding 等。
13.4 引用时的三个硬约束。
一是 P3 的效度链条在本项目断了一环：它证明 KB 自动评分与人工评分一致，前提是目标图由专家建，本项目目标图由 LLM 建，不能直接引它的效度结论，必须补开发期校正与作者本人标注。
二是 P4 转引的 Vanides 四级 rubric 不能用：它是人工评分 rubric，本项目是精确匹配的二值判定，混用会让评分口径无法自证。
三是 P6 的逆关系给满分与本项目口径冲突：若论文里既引 CMT 又说方向反转是错误，必须解释两者为何不同，否则会被认为口径不一致。
## 14 学科通用性
用户定：要适应所有学科，开发与论文阶段的教材由作者自己找。这条推翻了原先只考虑单一学科的隐含假设。
早期建议实验期用 uie-base、效果不够就微调，隐含假设是只有一个或少数几个学科。若目标是全学科通用，微调是有害的，理由有实证。
arXiv:2401.05605（Kalajdzievski, D., 2024, Scaling Laws for Forgetting When Fine-Tuning Large Language Models）摘要原文：PEFT strategies, such as Low-Rank Adapters (LoRA), still suffer from catastrophic forgetting; we identify a strong inverse linear relationship between the fine-tuning performance and the amount of forgetting; forgetting cannot be avoided through early stopping or by varying the number of parameters fine-tuned。
含义：在学科 A 上微调得越好，在学科 B 上可能越差，且早停与减参都救不回来。对一个要覆盖所有学科的系统，这几乎是致命的。
三种应对。方案甲：不微调，只靠零样本加连接词表，优点是无领域偏向，缺点是零样本 F1 有限且现有数字来自二手。方案乙：按学科分别微调并运行时选模型，实际不可行，因为需要每个学科都标注，作者没有这个能力。方案丙：不微调，把连接词表变成学科适配的主要手段，核心洞察是词表本身就是领域知识，物理多正比于与导致，历史多发生于与继任于，每个学科只换词表不换模型。
建议甲加丙，理由三条：与不付费、先搭再看两条决策一致；与标注都要标不冲突，但标注的用途从训练数据变成评估数据与词表设计依据；这是可写进论文的立场，不微调等于模型对学科中立，学科适配显式化在词表里，可审计可复现。
14.2.1 已定。产品层保持全学科通用不微调靠词表适配；论文层只用理论心理学一个学科做效度研究。这样跨学科分数不可比就不再是问题，因为论文根本不主张跨学科可比，只主张在本学科内有效，限制从缺陷变成研究范围的自然边界。
标注模型一词有歧义，本文件按标注数据集理解，即作者手工标注一批理论心理学教材作为评估基准；若指用标注微调出的小模型，则与全学科目标冲突，第 14 节要整体重写。
若为标注数据集，这批标注同时产出三样东西：效度评估的基准，即零样本在理论心理学上的真实 F1；该学科连接词表的设计依据；抽崩检测 S4 的基线分布。
14.2.2 理论心理学作为场景的具体风险：文本高度抽象、以论证与概念辨析为主，与 Kit-Build 论文常见的自然科学材料差别较大。概念往往是构念而非实体，关系往往是理论关系而非物理因果，命题的正确性依赖理论立场，不同流派可能给出不同连接词。这不影响方案成立，但影响词表收敛难度。建议先标一小批，看词表实际能收敛到多少个词再定规模。这条要写进功能说明：选理论心理学既是便利也是挑战，承认挑战比掩盖更有说服力。
14.3 它带来的效度问题：若词表因学科而异，跨学科分数不可直接比较，因为分母与词表强相关。所以论文只能做同学科内的效度研究，不能声称跨学科可比。
14.4 与该建议的冲突处理：不够就微调这条不删除，降级为仅当确定单学科场景时的选项，全学科目标下不适用，微调只作单学科后备，不作为计划。保留旧判断及其失效条件比直接删掉更有价值。
## 附 资料与可复核性
选型查证来源：docs.typesafe.ai 的 models 与 concepts/state 两页；github.com/NandhaKishorM/laya 的 README 与其 research/benchmarks/feishu_zh 目录；hf-mirror.com 的 knowledgator/gliner-relex-large-v1.0 配置文件；github.com/urchade/GLiNER 的 usage 文档；paddlenlp 的 model_zoo/taskflow 文档与 PaddleNLP 仓库的 llm/application/information_extraction 说明；opendatalab/mineru 的中文 index 与 quick_usage 文档；reactflow.dev 的 touch-device 示例；networkx 的 graph_edit_distance 文档；arxiv.org 上 2607.08065、2512.11922、2401.05605 三个摘要页；本地论文四篇加两篇补充阅读。
可靠性说明：UIE 的 F1 对比表来自二手技术文章整理，官方 README 在本机 404，未取到一手数据，正文已标注。hf-mirror.com 可达，huggingface.co 在本机不可达，故所有 Hugging Face 相关证据均经镜像取得。
<!-- /@zone research -->
