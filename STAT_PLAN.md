<!-- @zone research -->
# STAT_PLAN 统计量、算法与作用
先确认要算什么、怎么算、为什么算，再定导出字段。依据取自 docs/research/papers 下论文的实际做法，逐条标出处行号。字段定义不在本文件。
## 零 一条前置结论
统计量的选择决定字段粒度。顺序是先定统计量，再定字段，最后才决定要不要第二张表。
文献与本地文件对照，后文只写文件名：10.58459_rptel.2024.19021.txt 是 Rismanto 等 2024，RPTEL 19:21；10.58459_rptel.2026.21021.txt 是 Khudhur 等 2026，RPTEL 21:21；10.1186_s41039-022-00189-9.txt 是 Prasetya 等 2022，RPTEL 17:14；10.1186_s41039-017-0060-x.txt 是 Pailai 等 2017，RPTEL 12:20；10.1109_tlt.2021.3103331.txt 是 Kroeze 等 2021，IEEE TLT 14(4):460 到 473；10.1007_s11423-006-6497-z.txt 是 Taricani 与 Clariana 2006；10.1587_transinf.2017edp7177.txt 是 Wunnasri 等 2018，IEICE E101-D(4):1141 到 1150；10.1587_transinf.2021edp7069.txt 与 10.1587_transinf.2022edp7203.txt 均为 IEICE 论文；10.1016_j.eswa.2009.07.044.txt 是 Cline 等 2010，ESWA 37(3):2282 到 2291；10.14569_ijacsa.2020.0110420.txt 与 10.12937_ejsise.14.13.txt 分别属 IJACSA 与信息与系统教育。
## 一 本地文献用过的统计量
Normalized gain，Hake 1998，用于学习增益，10.58459_rptel.2024.19021.txt 行 415 到 425。
Normalized change，Marx & Cummings 2007，用于可处理下降的学习增益，10.58459_rptel.2026.21021.txt 行 564 到 568。
Shapiro-Wilk，正态性检验，10.1186_s41039-022-00189-9.txt 行 530 到 531；另见 10.58459_rptel.2024.19021.txt 行 431 到 434。
Kolmogorov-Smirnov，正态性检验的另一篇，10.14569_ijacsa.2020.0110420.txt 行 286。
前测同质性检验，分组前确认无差异，10.1186_s41039-022-00189-9.txt 行 278 到 279。
Mann-Whitney U，组间比较，10.58459_rptel.2026.21021.txt 行 647、692。
Wilcoxon signed-rank，组内前后测，10.14569_ijacsa.2020.0110420.txt 行 290 到 294。
Kruskal-Wallis 加 Dunn，三组以上与事后比较，10.1587_transinf.2021edp7069.txt 行 432 到 436。
双因素 ANOVA，两因素交互，10.12937_ejsise.14.13.txt 行 447 到 455。
多层与混合模型，处理班级聚类，10.1109_tlt.2021.3103331.txt 行 486 到 492、521 到 534。
Pearson's r 作非参检验的效应量，10.1186_s41039-022-00189-9.txt 行 537 到 540。
Cohen's kappa，评分者间一致性，10.1109_tlt.2021.3103331.txt 行 530 到 531。
Fleiss' kappa，多评分者一致性，10.1587_transinf.2022edp7203.txt 行 218。
Cronbach's alpha，量表内部一致性，10.1186_s41039-022-00189-9.txt 行 780 到 785。
g-coefficient，概化理论信度，10.1587_transinf.2017edp7177.txt 行 129、351。
Pearson 或 Spearman 相关，效度检验，10.1109_tlt.2021.3103331.txt 行 519 到 524。
卡方统计量，10.1587_transinf.2021edp7069.txt 行 452 到 453 写的是 chi squared = 9.95, p < 0.01，那个值是 Kruskal-Wallis 的检验统计量，不是独立的皮尔逊卡方检验，引用时别写成这篇做过卡方检验。
逻辑回归，二分类结果，10.58459_rptel.2026.21021.txt 行 814 到 834。
## 二 按分析目标反推需要什么
### G1 分数效度
问自动评分能否代表理解程度。需要 Pearson 或 Spearman 相关，一端是满图匹配分，另一端是外部测量：前测、后测、延迟测、标准化测验。满图匹配分与外部测量的相关由本项目自己算。
### G2 学习效果
问用这个系统能不能学到东西。需要 normalized change，不用 normalized gain，因为 gain 在分数下降时系统性低估退步、前测接近满分时分母趋零；需要前测到后测到延迟测的配对比较，用 Wilcoxon 或配对 t；需要延迟保持量。设计参照 Khudhur 的三阶段。
### G3 组间差异
先做前测同质性检验，否则组间差异无从解释。两组用 Mann-Whitney 或 t，多组用 Kruskal-Wallis 加 Dunn。本设计没有班级层级，多层模型不做，区组进固定效应。
### G4 错误类型分布
四类错误的频次与占比是描述统计。组间或模式间分布差异可用卡方。
### G5 目标图效度
问 LLM 抽的目标图与人工标注一致吗。比对对象是两组三元组集合，所以主指标是 precision、recall、F1 与 Jaccard，不是 kappa。kappa 要求逐项判定，集合比对没有天然的项，故不用。这一条是论文的核心效度证据，比 G1 更关键。
### G6 抽崩检测器效度
需要 ROC 与 AUC，加选定阈值下的 precision、recall、F1。前提是拿到实际是否崩的标签，来自标注时勾的抽取是否可用。没有这条，四个报警阈值就没有依据。
### G7 模式差异
测验模式与学习模式比较只作描述统计与敏感性分析，学习模式分数不作结果变量：它会收敛到满分，属天花板，报均值时必须同时报均值与标准差超满分的比例。天花板效应的判据是均值加标准差是否超过满分，文献实例在 Pailai 等 2017 行 692 到 695。
## 三 每个统计量的算法与作用
### 3.1 normalized change 而不是 normalized gain
normalized gain 出 Hake 1998，10.58459_rptel.2024.19021.txt 行 424 写作 NLG = (PostScore 减 PreScore) 除 (100 减 PreScore)。分子为负时分母仍是 100 减 Pre，算出的增益不反映下降幅度；Pre 趋近 100 时分母趋零。
normalized change 出 Marx & Cummings 2007，10.58459_rptel.2026.21021.txt 行 564 到 568 说它 avoids the pre-test score bias。三分支如下。
Post 大于 Pre 时 c = (Post 减 Pre) 除 (Max 减 Pre)。
Post 小于 Pre 时 c = (Post 减 Pre) 除 (Pre 减 Min)。
Post 等于 Pre 时 c = 0。
差别在于下降时用 Pre 减 Min 作分母，即还有多少可以掉，与还有多少可以涨对称。
本项目用 normalized change。学生成绩可能下降，用 gain 会系统性低估退步。
实现只存前测与后测原始分，满分与下限是常量 100 与 0，不必另存；不存算好的 c，派生量一旦落库就锁死公式选择，换公式只能重算全部数据。
### 3.2 正态性检验
Shapiro-Wilk 的 W 越小越偏离正态。它的作用是决定后续用参数还是非参检验，是流程分叉点，不是结论本身。
Prasetya 用 Shapiro-Wilk，10.1186_s41039-022-00189-9.txt 行 530 到 531。另一篇用 Kolmogorov-Smirnov，10.14569_ijacsa.2020.0110420.txt 行 286。
选择建议用 Shapiro-Wilk，课堂规模下它比 K-S 有检验力；样本超过 5000 时它过度敏感，改看 Q-Q 图。
必须分变量、分时点检验，不能一次定终身。实例见 10.58459_rptel.2024.19021.txt 行 431 到 434：前测 p 等于 0.2705 判为正态，后测 p 等于 6.774e-06、延迟测 p 等于 0.006 判为不正态，于是该文改用 Kruskal-Wallis。这类前后不一致很常见，后测常因天花板而不正态。
### 3.3 前测同质性检验
组间比较前测分数，t 或 Mann-Whitney，确认 p 大于 0.05。这是所有组间比较的前提，否则后面的组间差异可能只是基线延续。
原文 10.1186_s41039-022-00189-9.txt 行 278 到 279：the pretest was conducted before determining the role of the group, and the results stated that both classes were homogeneous (p = 0.445 > 0.05)。
注意不显著不等于等价，样本小时检验力低，容易通过。要同时报效应量。
### 3.4 Wilcoxon signed-rank
对配对差值取绝对值排序，做符号和检验，是配对 t 的非参替代。用于同一批学生的前测与后测比较，是 G2 的主力，因为课堂样本小且后测常不正态。
原文 10.14569_ijacsa.2020.0110420.txt 行 290 到 294：A Wilcoxon signed-rank test was used to determine … The Wilcoxon signed-rank is a non-parametric analog of the parametric paired t-test。
### 3.5 Mann-Whitney U
两组秩和比较，是配对 Wilcoxon 的非配对版本。用于实验与对照、测验与学习的组间差异。Khudhur 用它比两组的 normalized change，行 647、692。
### 3.6 Kruskal-Wallis 加 Dunn
K-W 是 Mann-Whitney 的多组扩展，基于秩的方差分析。显著后做 Dunn 两两比较，必须多重比较校正。
原文 10.1587_transinf.2021edp7069.txt 行 432 到 436：a Kruskal-Wallis test with normalized change as the dependent variable … Post-hoc comparisons using Dunn's test revealed that …；同处把 chi squared = 9.95, p < 0.01 报作 K-W 的检验统计量。
常见错误是 K-W 显著就直接两两做 Mann-Whitney 不校正，假阳性膨胀。要用 Dunn 加 Bonferroni 或 Holm。
### 3.7 效应量 r 等于 Z 除根号 N
算法：Z 取 Mann-Whitney 或 Wilcoxon 的标准化统计量，N 为总样本数。它不是 Pearson 相关系数，只是借用 r 的尺度。
因此不套 Pearson 的判读档。要判读就走效应量通识基准，绝对 0.1 小、0.3 中、0.5 大，并把通识与文献区分开写。
仅当真做 Pearson 相关时，才用相关系数的判读档。10.58459_rptel.2024.19021.txt 行 439 到 441 转述 Schober et al. 2018 为三档：小于 0.39 弱、0.40 到 0.69 中、0.70 以上强。该转述与原文的五档不同，原文为绝对 0.10 以下可忽略、0.10 到 0.39 弱、0.40 到 0.69 中、0.70 到 0.89 强、0.90 以上很强。写论文时引 Schober et al. 2018 原文，不引转述。
作用：p 值只说有没有差异，效应量说差异多大，两者必须同报。
不用 Cohen's d 的理由是 d 假设正态，本项目的检验多为非参。两者不可混用，d 约等于 2r 除根号下 1 减 r 方只作参考换算。
### 3.8 Cohen's kappa
算法：kappa 等于 Po 减 Pe 再除 1 减 Pe，Po 为实际一致率，Pe 为随机期望一致率。用于两个评分者在逐项判定上是否一致。
原文 10.1109_tlt.2021.3103331.txt 行 530 到 531：In total, 83% of feedback prompts were considered accurate by human coders, who reached 89% agreement, with a Cohen's k of 0.47。同一文献行 539 到 540 还有两组不同对象的结果，93% 对应 k 等于 0.88，74% 对应 k 等于 0.56，引用时别混。
89% 的一致率只对应 0.47 的中等 kappa，这正是要报 kappa 而不只报一致率的理由。
### 3.9 G5 用 F1 不用 kappa
比对对象是三元组集合：人工标注的目标图是一组命题，LLM 抽取是另一组命题。kappa 要求逐项判定，集合比对没有天然的项。若把全部可能三元组当项，绝大多数是两边都没有，Pe 被抬高，kappa 虚高。
正确做法：precision 等于交集除 LLM 集合大小，recall 等于交集除人工集合大小，F1 等于 2PR 除 P 加 R，Jaccard 等于交集除并集。
precision 低说明抽了人工没标的，是幻觉；recall 低说明漏抽。两者后果不同：漏抽可由人补，幻觉会污染零件包，更严重。
结论：G5 用 F1 加分项 P 与 R，不用 kappa。kappa 只在每条已抽取命题由人工判对错时才有意义，那是二分类判定。
### 3.10 二值题用 KR-20
测验只用客观单选，每题对错，信度指标要换成 KR-20，即 Kuder-Richardson 第 20 号公式。多级量表才用 Cronbach's alpha。
两者数学上等价，KR-20 就是 alpha 在二值数据上的特例，但期刊惯例不同，二值题报 alpha 会被问为什么不用 KR-20。
文献用例 10.1007_s11423-006-6497-z.txt 行 333：The KR-20 reliability for the posttest was 0.83。
方法出处为 Kuder, G. F., & Richardson, M. W. (1937). The theory of the estimation of test reliability. Psychometrika, 2(3), 151–160。
应用：单选测验题报 KR-20，TAM 六点量表报 Cronbach's alpha，两者都报，因为它们是两个不同工具的信度。三个时点各报一次；alpha 判据 0.70，KR-20 无通用阈值，按 0.70 同处理并在报告里写明这条是借用。
### 3.11 Cronbach's alpha
算法：alpha 等于 (k 除以 (k 减 1)) 乘 (1 减去 (各题方差之和 除以 总分方差))，k 为题数。括号不能省，省了有两种读法，数值不同。
用于量表各题是否测同一构念，即 TAM 的 PEOU、PU、BI。
原文 10.1186_s41039-022-00189-9.txt 行 780 到 785，判据为 Cronbach's alpha greater than 0.7。
它需要题级数据，即每道题的得分，这是决定要不要第二张表的关键约束。
### 3.12 多层与混合模型
算法 y 等于 X 贝塔加 Zu 加 epsilon，u 为随机效应即班级，X 为固定效应即性别、年龄、年级。
作用是处理同班学生的相关性。ICC 大于 0 时普通回归会低估标准误。
原文 10.1109_tlt.2021.3103331.txt 行 486 到 487：Class and domain were included as random effects；行 521 到 523：gender, age, and grade as fixed effects。同文行 520 到 534 给出 binomial、ordinal、multinomial 三个变体。
对本项目的含义：必须存班级，否则做不了这个模型；本项目个体招募无班级层级，主分析不做多层模型，lmer 只在将来多班数据上备用。本设计改走个体招募，无班级层级，多层模型不做，但班级字段照存，供后续多班研究。
现实约束：多层模型一般需要 10 个以上组，只有 2 到 3 个班时随机效应估计不稳，退化成分层描述更诚实。
### 3.13 天花板效应
定义：分数接近满分时方差压缩，均值差异不可检出。
文献实例 10.1186_s41039-017-0060-x.txt 行 692 到 695：group B 的相关系数低 because of ceiling effect of some learners，第三次图分数均值 0.967、标准差 0.117，均值加标准差高于满分，作者据此判为天花板。
对本项目的影响：学习模式可循环到全对，分数必然天花板，均值比较无意义；测验模式若题目简单也可能天花板。
报告时必须显式检查均值加标准差是否超过满分，并写清结论。
### 3.14 ROC 与 AUC
扫描所有阈值，画 TPR 与 FPR 曲线，算曲线下面积。它衡量检测器的整体判别力，与阈值选择无关。
判读：0.5 为随机，0.7 到 0.8 可接受，0.8 以上好。
为什么需要：四个报警阈值是拍出来的，AUC 是唯一能证明它们不是瞎猜的证据。
前提是拿到实际是否崩的标签，来自标注时勾的抽取是否可用，所以标注不只标三元组。
### 3.15 外部效度参照：不要预设相关值
10.1007_s11423-006-6497-z.txt 行 219 起复述 Clariana 与 Poindexter 2004 的后续研究，行 232 到 239 报出该校研究的相关：网络图连线数据与术语测验 r 等于 0.77（对比 0.69），距离数据与理解测验 r 等于 0.71（对比 0.53）。这组数字属前人研究，不是本文实测。
同文行 556 到 565 才是作者对自己结果的讨论：概念图分数与选择题分数不一定强相关，thus Pearson's r values in the 0.30 to 0.40。
所以两组数字的归属必须分清：0.30 到 0.40 属本文自己讨论的经验区间，0.71 与 0.77 属被引的前人研究。
这个区分决定论证能否成立。若概念图分数与选择题相关只有 0.30，两者测不同东西，增量信息论证成立；若相关到 0.71，两者相当接近，增量信息论证不成立，反而要回答为什么还需要概念图。
结论：本项目必须自己算这个相关，实测前不写预期值。
### 3.16 前测敏感性
问题：前测与后测用同一套题，学生记得题目，后测分数部分来自记忆，会高估增益。
学界标准解法是 Solomon 四组设计。Solomon, R. L. (1949). An extension of control group design. Psychological Bulletin, 46(2), 137–150，DOI 10.1037/h0062958。四组为前测加处理、前测无处理、无前测加处理、无前测无处理，靠四组对比分离前测本身的影响与前测乘处理的交互。写作时直引该文，不引第三方页面转述。
本项目不用，因为需随机分到四个独立组，样本规模不支持，且前测敏感性无法用统计修正，只能靠设计。
Khudhur 也没把这条列进局限：他的方法只写 shared identical questions，10.58459_rptel.2026.21021.txt 行 531 到 534 讲的是测试题构成；同文行 767 反而承认材料可能有 a memory-enhancing impact on the reviewed information。
所以既不能援引先例说论文这么做的所以没问题，也不能声称本项目解决了。
局限一节的措辞：本研究前测与后测使用同一套题，存在前测敏感性风险，后测增益可能部分来自题目记忆。标准解法为 Solomon 四组设计，但需随机分配至四个独立组，本研究样本规模不支持。该风险以两周延迟后测部分对冲，延迟后仍答对者，记忆解释的说服力较弱。
### 3.17 四指标：区分复习与新学
同卷设计的唯一正当理由是能逐题判分类。出处 10.58459_rptel.2026.21021.txt Table 2。
Normalized Review 等于 Review 除 Pre 的比例形式。
Normalized New 等于 New 除以 (1 减 Pre)。
Normalized Review Retention 等于 ReviewOnDelay 除 Review。
Normalized New Retention 等于 NewOnDelay 除 New。
表下说明：Pre refers to pre-test scores. Review, New, ReviewOnDelay, and NewOnDelay refer to the number of questions belonging to each classification for that particular learner。
分类依据 Khudhur Table 1：Review 为前测对且后测对；New 为前测错而后测对；ReviewOnDelay 为前测对、后测对、延迟测对；NewOnDelay 为前测错、后测对、延迟测对。
四个指标各答一问：前测就会的部分在后测仍保持多少；真正新学会了多少，分母是原本不会的；复习过的知识两周后剩多少；新学的知识两周后剩多少。
为什么不可替代：满图匹配分只回答最终对了几条命题，这四个回答学到的到底是新的还是本来就会的，没有它们就排除不了学生本来就知道这个替代解释。
注意 Normalized New 的分母 1 减 Pre 与 normalized change 的 Max 减 Pre 同源，都是还有多少可以提升。
## 四 外部文献的三个不可援引之处
Taricani 与 Clariana 那篇不能用来论证同卷可接受，因为它没有前测。
它是开放式概念图，与封闭零件包是相反设计。
它用 PFNet 邻近矩阵评分，不是命题级查表。
它唯一可援引的是概念图分数与选择题分数的相关值，且要分清哪组数字是谁的。
## 五 要不要题级表
按统计量看：normalized change、Wilcoxon、Mann-Whitney、Kruskal-Wallis、G1 相关、G5 的 F1、G6 的 ROC 都不需要题级数据，用总分或命题集合即可。
需要题级数据的有三处：Cronbach's alpha 要每题得分；Review 与 New 四指标要按题看三个时点的正确性；单题难度与区分度要每题得分。
结论：做第二张表，现在就做。理由有两条。Cronbach's alpha 是 TAM 量表的必需信度证据，没有它主观量表部分无法自证。Review 与 New 分解是 Kit-Build 研究的标志性指标，不做就丢掉一个有力论点。
前提是题级表的关联键必须来自被试级已有字段，即被试标识、教材标识、目标图指纹、时点、提交序号，否则将来补不上。
## 六 已确认与悬置
### 已确认
前测、后测、延迟测都逐题作答，且三个时点同一套题。
题型只用客观单选，每题对错，不设主观题。
延迟后测做，同表存放，用 time_point 区分。
题级表现在就做，用长格式。
做实验与对照分组，属效能试验，不做机制分解。
TAM 用，中文量表由用户提供。
样本规模 n 等于 120，便利样本，个体区组随机。检验力用 pwr 包按双侧 alpha 0.05、power 0.8 计算，脚本与随机种子须与结果一同保存，否则不可复现。
### n 等于 120 的检验力
双侧 alpha 等于 0.05，power 等于 0.80，两组各 60。单教材最小可检出效应 d 等于 0.51；两教材按 k 等于 2、r 约 0.5 修正后 d 约 0.44。修正因子为根号下 1 加 k 减 1 乘 r 再除 k，r 取 0.5 是保守假设，实际更高更有利。
没有班级层级，个体招募，多层模型不做，区组进固定效应。
Shapiro-Wilk 在 n 等于 120 仍可用，远未到 5000 的过度敏感区。
### 悬置
内容维度的具体取值，第一次测验后收敛成枚举。
此项已定，不在悬置内：TAM 中文措辞取自用户提供的问卷原文，14 题逐字一致，PU 4、PEOU 4、BI 3、ATT 3 可选，六点 Likert。仍悬置的只有一条：题面所指任务是回忆任务与回忆辅助系统，与概念图重建构念不符，改写题面后是否仍算逐字。
## 七 用 R 不用 Python
理由是可复现性，不是偏好。本领域审稿人与复核者默认在 R 生态，用 Python 复算要重写整条流水线，R 脚本可直接交出去。
### 7.1 环境
R 版本 4.5.2，发布日 2025-10-31，与 CRAN 记录一致；此后已有 4.5.3、4.6.0、4.6.1，若不锁定版本，复核者按新版本跑可能得到细微不同的结果，故脚本头必须写死版本。
已装 lme4 1.1-37、lmerTest 3.1-3、rstatix 0.7.2、pROC 1.18.5、psych 2.4.3，另有 emmeans、car、effsize。
FSA 与 irr 未装：Dunn 用 rstatix 的 dunn_test 替代，不需要 FSA；人人与机器对人工的一致性用 F1 与 Jaccard，不需要 irr 的 kappa。
不为此装新依赖。
### 7.2 每个统计量对应的函数
前测同质性用 rstatix 的 wilcox_test(pre ~ group)。
组间主模型用 lmerTest 的 lmer(post ~ group*pre + txt + ord + (1|subj))。
组内前后测用 wilcox_test(post ~ pre, paired = TRUE)。
非参效应量 r 用 abs(qnorm(p/2)) 除根号 N，不用 effsize。
K-W 用 kruskal_test，事后用 dunn_test(p.adjust.method 等于 holm)。
正态性用 shapiro.test 或 rstatix 的 shapiro_test。
normalized change 的分子分母必须同单位，混用会算出大于 1 的值。
Cronbach's alpha 用 psych 的 alpha，报 raw_alpha。
ROC 与 AUC 用 pROC 的 roc 与 auc，阈值用 coords 的 best。
多层与区组用 lmer 加 (1|subj)。
### 7.3 normalized 指标的单位陷阱
公式写作 New 除 1 减 Pre，其中 Pre 是比例。若 New 取条数而 Pre 取比例，单位不一致，结果离谱。
实测模拟 k 等于 10 题、200 人：Pre 用比例时 normalized New 最大值 10.0，超过 1 的占 94.5%；统一用条数除总数时最大值 1.000，超过 1 的占 0%。
规则：全部用条数或全部用比例，混用必错。Review 侧同理，分母是该人前测就会的条数，不是总题数。
### 7.4 随机效应可能奇异
模拟中 lmer(post ~ group*pre + txt + ord + (1|subj)) 曾报 boundary (singular) fit，随机截距方差 0.0003。原因是每人只有 2 个教材乘 3 个时点，被试内相关本就弱。
处理顺序：先看 isSingular 与 VarCorr；方差近零时试随机斜率 (1 + txt | subj)；仍奇异则退 lm，并在论文写明被试内相关可忽略故用 OLS；不得因为奇异就删数据。
这是本设计的已知弱点：每教材只有一次观测，被试内重复太薄。若最终 n 偏小且奇异频发，改用宽表加配对检验或 rmANOVA 更诚实。
### 7.5 脚本与产物
分析脚本放 docs/research 下。随机种子、包版本、R 版本写进脚本头，否则不可复现。算好的派生量不写回数据库，界面与统计一律从原始量算。
## 八 流程顺序
先做正态性检验，据结果分参数与非参。非参时组内用 Wilcoxon、组间用 Mann-Whitney、多组用 Kruskal-Wallis 加 Dunn，效应量一律报 r 等于 Z 除根号 N。
学习效果走 normalized change，不用 gain，随后查天花板，判据是均值加标准差是否超过满分。
G1 效度用 Pearson 或 Spearman 相关；G5 用 F1 加分项 P 与 R，不用 kappa；G6 用 ROC 与 AUC；量表信度用 KR-20 与 Cronbach's alpha，需题级数据；班级聚类用多层模型，需班级字段。
<!-- /@zone research -->
