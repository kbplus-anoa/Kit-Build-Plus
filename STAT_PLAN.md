<!-- @zone research -->
# STAT_PLAN — 统计量、算法与作用

> 目的：在做导出字段之前，先确认**要算什么、怎么算、为什么算**。
> 依据来自 `docs/research/papers/` 下论文的实际做法，逐条标注出处行号。
> 本文件只讨论统计，不定义字段（字段见 `CSV_PLAN.md`）。

---

## 0. 一条前置结论

**统计量的选择决定了字段的粒度。**
所以顺序是：先定统计量 → 再定字段 → 最后才决定要不要第二张表。
本轮先做前两步。

---

## 1. 论文实际用过的统计量（证据）

| 统计量 | 用在哪 | 出处 |
|---|---|---|
| Normalized gain (Hake 1998) | 学习增益 | `10.58459_rptel.2024.19021.txt` 行 415–425 |
| Normalized change (Marx & Cummings 2007) | 学习增益（可处理下降） | `...rptel.2026.21021.txt` 行 564–568 |
| Shapiro–Wilk | 正态性检验 | `10.1186_s41039-022-00189-9.txt` 行 530–531 |
| Kolmogorov–Smirnov | 正态性检验（另一篇） | `10.14569_ijacsa.2020.0110420.txt` 行 286 |
| 前测同质性检验 | 分组前确认无差异 | `10.1186_s41039-022-00189-9.txt` 行 278–279 |
| Mann–Whitney U | 组间比较 | `10.58459_rptel.2026.21021.txt` 行 647、692 |
| Wilcoxon signed-rank | 组内前后测 | `10.14569_ijacsa.2020.0110420.txt` 行 290–294 |
| Kruskal–Wallis + Dunn | 三组以上 + 事后 | `10.1587_transinf.2021edp7069.txt` 行 432–436 |
| 双因素 ANOVA | 两因素交互 | `10.12937_ejsise.14.13.txt` 行 447–455 |
| 多层/混合模型 | 处理班级聚类 | `10.1109_tlt.2021.3103331.txt` 行 486–492、521–534 |
| Pearson's r（作 ES） | 非参检验的效应量 | `10.1186_s41039-022-00189-9.txt` 行 537–540 |
| Cohen's kappa | 评分者间一致性 | `10.1109_tlt.2021.3103331.txt` 行 538–541 |
| Fleiss' kappa | 多评分者一致性 | `10.1587_transinf.2022edp7203.txt` 行 218 |
| Cronbach's alpha | 量表内部一致性 | `10.1186_s41039-022-00189-9.txt` 行 780–785 |
| g-coefficient | 概化理论信度 | `10.1587_transinf.2017edp7177.txt` 行 129、351 |
| 相关性（Pearson/Spearman） | 效度检验 | `10.1109_tlt.2021.3103331.txt` 行 519–524 |
| 卡方 | 分布差异 | `10.1587_transinf.2021edp7069.txt` 行 452 |
| 逻辑回归 | 二分类结果 | `10.58459_rptel.2026.21021.txt` 行 814–834 |

---

## 2. 我们到底需要哪些：按分析目标反推

### 目标 G1：KB 分数的**效度**
"自动评分能否代表理解程度"

- **必需**：Pearson / Spearman 相关（KB 分数 vs 外部测量）
- **外部测量**：前测、后测、延迟后测、标准化测验
- 出处：Kroeze 用它证明"质量分与专家评分强相关（r=0.78）"

### 目标 G2：**学习效果**
"用这个系统能不能学到东西"

- **必需**：Normalized change（不是 gain，理由见 3.1）
- **必需**：前测 → 后测 → 延迟后测的**配对比较**（Wilcoxon 或配对 t）
- **必需**：延迟保持（retention）
- 出处：Khudhur 的三阶段设计

### 目标 G3：**组间差异**（若做实验/对照）
- **必需**：先做**前测同质性检验**（否则组间差异无意义）
- **组间比较**：Mann–Whitney（非参）或 t 检验（参数）
- **多组**：Kruskal–Wallis + Dunn
- **有班级聚类**：**多层模型**，班级作 random effect

### 目标 G4：**错误类型分布**
"学生错在哪一类"

- **必需**：四类错误的**频次与占比**（描述统计）
- **可选**：卡方（检验不同组/不同模式的分布差异）

### 目标 G5：**LLM 目标图的效度**（本项目独有，最重要）
"LLM 抽的目标图，和人工标注一致吗"

- **必需**：**评分者间一致性**（Cohen's kappa 或 ICC）
  对象是"人工标注的三元组集" vs "LLM 抽的三元组集"
- **必需**：**precision / recall / F1**（因为这是集合比对，不是分类）
- **注意**：kappa 适用于**逐项判定**，而我们是**集合**，
  所以更合适的是 **F1 + Jaccard**，kappa 只在"逐条命题判定"时用
- **这条是论文的核心效度证据**，比 G1 更关键

### 目标 G6：**抽崩检测器本身的效度**
我们做了 S1–S4 报警，它准吗

- **必需**：**ROC / AUC**（报警 vs 实际是否崩）
- **必需**：precision / recall / F1（在选定阈值下）
- **前提**：需要"实际是否崩"的标签 —— 来自用户标注
- **这条容易被忽略，但没有它，检测器就是没有依据的**

### 目标 G7：**模式差异**（测验 vs 学习）
- **必需**：描述统计 + 组间比较
- **注意**：学习模式分数会收敛到 1.0（天花板效应），
  **必须报告天花板效应**，否则均值比较无意义
  出处：Khudhur 提到 "ceiling effect"（`10.1186_s41039-017-0060-x.txt` 行 700–710）

---

## 3. 每个统计量的算法与作用（核心章节）

### 3.1 Normalized change（**不是** normalized gain）

**为什么必须区分这两者**（这是本轮最重要的发现）：

**Normalized gain**（Hake 1998），`10.58459_rptel.2024.19021.txt` 行 425 原文：

```
NLG = (PostScore − PreScore) / (100 − PreScore)
```

**问题**：分子为负时（成绩下降），分母仍是 `100 − Pre`，
算出来的"增益"**不能反映下降幅度**，且当 `Pre → 100` 时分母趋零。

**Normalized change**（Marx & Cummings 2007），`10.58459_rptel.2026.21021.txt`
行 564–568 原文说它"avoids the pre-test score bias"：

```
若 Post > Pre:  c = (Post − Pre) / (Max − Pre)
若 Post < Pre:  c = (Post − Pre) / (Pre − Min)
若 Post = Pre:  c = 0
```

**区别的本质**：下降时用 `Pre − Min` 作分母，
即"还有多少可以掉"，与"还有多少可以涨"对称。

**结论：本项目用 normalized change，不用 normalized gain。**
因为我们允许学生答错、成绩可能下降，用 gain 会系统性低估退步。

**作用**：把不同基线的人拉到同一尺度，使"提升幅度"可比。
**这正是我们需要的**——学生的前测分数差异会很大。

**⚠️ 实现要求**：存**前测、后测、Min、Max**，不存算好的 c。
原因见 `README_PLAN.md` 7.7.1 的原则①（存原始量，不存派生量）。

---

### 3.2 正态性检验：Shapiro–Wilk

**算法**：检验样本是否来自正态分布（W 统计量，越小越偏离正态）。

**作用**：**决定后面用参数还是非参检验。** 这是流程上的分叉点，不是结论本身。

**论文的做法**：Prasetya 用 Shapiro–Wilk（`10.1186_s41039-022-00189-9.txt` 行 530）；
另一篇用 Kolmogorov–Smirnov（`10.14569_ijacsa.2020.0110420.txt` 行 286）。

**选择建议**：**用 Shapiro–Wilk**。样本量小（课堂规模）时它比 K–S 更有检验力；
**但样本 > 5000 时它会过度敏感**，此时看 Q-Q 图更实际。

**⚠️ 一个必须记录的现实**：Kroeze 的研究里，
前测正态（p=0.2705）但后测不正态（p=6.774e-06）。
**这很常见**——后测有天花板效应。
**所以不能"一次检验定终身"，要分变量、分时点检验。**

---

### 3.3 前测同质性检验

**算法**：组间比较前测分数（t 检验或 Mann–Whitney），确认 p > 0.05。

**作用**：**这是所有组间比较的前提。** 若前测就有差异，
后面的"组间差异"可能是基线差异的延续，不是处理效应。

**论文原文**（`10.1186_s41039-022-00189-9.txt` 行 278–279）：

> "the pretest was conducted before determining the role of the group, and
> the results stated that both classes were homogeneous (p = 0.445 > 0.05)"

**注意**：不显著 ≠ 等价。样本小时检验力低，容易"通过"。
**建议同时报告效应量**，不要只看 p。

---

### 3.4 Wilcoxon signed-rank（组内前后测）

**算法**：对配对差值取绝对值排序，用符号和检验。
是**配对 t 检验的非参替代**。

**作用**：同一批学生"前测 vs 后测"是否有显著变化。
**这是我们 G2 的主力**，因为课堂样本小、且后测常不正态。

**论文用法**：`10.14569_ijacsa.2020.0110420.txt` 行 290–294

> "A Wilcoxon signed-rank test was used to determine ... The Wilcoxon
> signed-rank is a non-parametric analog of the parametric paired t-test."

---

### 3.5 Mann–Whitney U（组间）

**算法**：两组秩和比较。配对 Wilcoxon 的非配对版本。

**作用**：两组学生（如实验/对照、测验/学习）之间的差异。

**论文用法**：Khudhur 用它比较两组的 normalized change（行 647、692）。

---

### 3.6 Kruskal–Wallis + Dunn（三组以上）

**算法**：K–W 是 Mann–Whitney 的多组扩展（基于秩的方差分析）；
显著后做 **Dunn's test** 两两比较，**必须做多重比较校正**。

**作用**：三组及以上（如多个班级、多种模式）。

**论文用法**：`10.1587_transinf.2021edp7069.txt` 行 432–436

> "a Kruskal-Wallis test with normalized change as the dependent variable ...
> Post-hoc comparisons using **Dunn's test** revealed that ..."

**⚠️ 常见错误**：K–W 显著就直接两两做 Mann–Whitney，不校正 → 假阳性膨胀。
**必须用 Dunn + 校正（Bonferroni 或 Holm）。**

---

### 3.7 效应量：Pearson's r（用作非参 ES）

**算法**（**这是关键，容易算错**）：

```
r = Z / √N
```

其中 Z 是 Mann–Whitney / Wilcoxon 的**标准化统计量**，N 是总样本数。

**不是** Pearson 相关系数！只是**借用了 r 的尺度**。

**判读标准**（Schober et al. 2018，`10.58459_rptel.2024.19021.txt` 行 436–440 引用）：

| \|r\| | 解释 |
|---|---|
| < 0.39 | 弱 |
| 0.40 – 0.69 | 中 |
| ≥ 0.70 | 强 |

**作用**：p 值只说"有没有差异"，效应量说"差异有多大"。
**论文必须同时报告**，否则小样本的显著性没有说服力。

**为什么不用 Cohen's d**：d 假设正态。
我们大部分是非参检验，对应的是 r。**两者不可混用。**

**⚠️ Cohen's d 与 r 不可直接换算比较**，但 `d ≈ 2r/√(1−r²)` 可作参考。

---

### 3.8 Cohen's kappa（评分者间一致性）

**算法**：

```
κ = (Po − Pe) / (1 − Pe)
```

Po = 实际一致率，Pe = 随机期望一致率。

**作用**：**两个评分者（人工 vs LLM）在"逐项判定"上是否一致。**
用于 G5 —— 但**注意适用条件**，见 3.9。

**论文用法**：Kroeze 报告 "89% agreement, with a Cohen's κ of 0.47"（行 538–541）。
**注意 89% 的一致率只对应 κ=0.47（中等）** —— 这正是为什么要报 kappa 而不是只报一致率。

---

### 3.9 ⚠️ G5 的正确做法：F1，不是 kappa

**这是本项目最容易做错的一处。**

我们的比对对象是**三元组集合**：
人工标注的目标图 = 一组命题；LLM 抽取 = 另一组命题。

**kappa 要求"逐项判定"，但集合比对没有天然的"项"。**
若强行把"所有可能的三元组"当项，绝大多数是"两边都没有"，
会把 Pe 抬得很高，**kappa 虚高**。

**正确的做法**：

```
precision = |LLM ∩ Human| / |LLM|
recall    = |LLM ∩ Human| / |Human|
F1        = 2PR / (P + R)
Jaccard   = |LLM ∩ Human| / |LLM ∪ Human|
```

**作用**：
- **precision** 低 → LLM 抽了人工没标的（幻觉）
- **recall** 低 → 人工标了 LLM 没抽到的（漏抽）
- **这两个错误后果不同**：漏抽可由人补（D9 允许），幻觉会污染 kit（更严重）

**结论：G5 用 F1 + 分项 P/R，不用 kappa。**
kappa 只在"每条已抽取的命题，人工判对/错"时才有意义（那是二分类判定）。

---

### 3.10a ⚠️ 二值题用 KR-20，不是 Cronbach's alpha

**用户已定：测验只用客观单选（每题对/错）。**
那么信度指标要换。

| 题型 | 信度指标 |
|---|---|
| **二值题（对/错）** | **KR-20**（Kuder–Richardson 20） |
| 多级量表（Likert） | Cronbach's alpha |

**两者数学等价**：KR-20 就是 alpha 在二值数据上的特例。
但**期刊惯例不同**——二值题报 alpha 会被问"为什么不用 KR-20"。

**论文用例**：`10.1007_s11423-006-6497-z.txt` 行 334：

> "The **KR-20 reliability** for the posttest was 0.83."

**我们的应用**：
- 测验题（单选）→ 报 **KR-20**
- TAM 量表（六点）→ 报 **Cronbach's alpha**
- **两者都要报，因为它们是两个不同工具的信度**

---

### 3.10 Cronbach's alpha（内部一致性）

**算法**：

```
α = (k / (k−1)) × (1 − Σσ²ᵢ / σ²_total)
```

k = 题目数，σ²ᵢ = 第 i 题方差，σ²_total = 总分方差。

**作用**：**量表**（TAM 的 PEOU/PU/BI）的题项是否测同一个构念。

**论文用法**：Prasetya 行 780–785，判据 "Cronbach's alpha greater than 0.7"。

**⚠️ 它需要 item-level 数据**（每道题的得分）。
**这是决定"要不要第二张表"的关键约束之一** —— 见第 4 节。

---

### 3.11 多层/混合模型（班级聚类）

**算法**：`y = Xβ + Zu + ε`，u 为随机效应（班级），X 为固定效应（性别、年龄、年级）。

**作用**：**处理同一班级内学生的相关性**（ICC > 0 时，普通回归会低估标准误）。

**论文原文**（Kroeze 行 486–492）：

> "**Class and domain were included as random effects** to account for
> interclass correlation effects. Students' **gender, age, and grade** ...
> were controlled for by including them as **fixed effects**."

**变体**（Kroeze 行 520–534）：binomial（二分类）、ordinal（有序）、multinomial（多分类）。

**对本项目的含义**：**必须存班级**，否则做不了这个模型。
这也是 `README_PLAN.md` 7.7.1 原则②的由来。

**⚠️ 现实约束**：多层模型需要**足够的组数**（一般 ≥ 10 个班）。
若只有 2–3 个班，随机效应估计不稳，**退化成分层描述更诚实**。

---

### 3.12 ROC / AUC（抽崩检测器效度，G6）

**算法**：扫描所有阈值，画 TPR–FPR 曲线，算曲线下面积。

**作用**：**检测器的整体判别能力**，与阈值无关（阈值的选择是另一件事）。

**判读**：0.5 = 随机，0.7–0.8 可接受，> 0.8 好。

**为什么需要**：我们设计的 S1–S4 阈值是**拍出来的**（12A.5 说要"用分布定"）。
**AUC 是唯一能证明这套阈值不是瞎猜的证据。**

**前提**：需要"实际是否崩"的标签——来自用户标注。
**这意味着标注要包含"这份抽取是否可用"的判定**，不只是三元组。

---

### 3.12a 外部效度参照：相关范围很宽，**不要预设**

**⚠️ 本节已修正。** 我原先写"相关只有 0.30–0.40"，那是**断章取义**。

`10.1007_s11423-006-6497-z.txt` 行 556–565 的完整语境：

> "Scores based on network map **link data** ... were more related to terminology,
> with **Pearson's r = .77** ... while scores based on network map **distance data**
> were more related to comprehension, with **r = .71**"

> "the **correlation between multiple-choice posttest scores and concept map
> scores** can be at least ... thus **Pearson's r values in the 0.30 to 0.40**"

**区分清楚这两组数字的归属：**

| 数字 | 是谁的 |
|---|---|
| **r = .30–.40** | **该文引用的前人研究**（不是它自己的结果） |
| **r = .71–.77** | **该文自己的实测结果** |

**这个修正改变了结论的可辩护性：**

- 若概念图分数与选择题相关只有 .30，两者测不同东西 → **"增量信息"论证成立**
- 若相关达 .71，两者相当接近 → **"增量信息"论证不成立**，
  反而要回答"为什么还需要概念图"

**结论：这个值必须自己算，不能预设。**
在实测前，任何"预期落在 0.3–0.4"的说法都是没有依据的。

**报告方式（不变）**：
- 主结果：概念图分数（FMS）
- 外部参照：单选测验分数
- **报实测相关值，与上述两个文献参照点作比较**
- **无论落在哪一端，都要解释它意味着什么**

---

### 3.12b 四指标：区分"复习"与"新学"（**必须做**）

**这是同卷设计的唯一理由。** 只有前/后/延迟用同一套题，才能逐题判分类。

出处 `10.58459_rptel.2026.21021.txt` Table 2 原文：

| 指标 | 公式 |
|---|---|
| Normalized Review | `Review / Pre` |
| Normalized New | `New / (1 − Pre)` |
| Normalized Review Retention | `ReviewOnDelay / Review` |
| Normalized New Retention | `NewOnDelay / New` |

**表下说明原文：**

> "**Pre refers to pre-test scores. Review, New, ReviewOnDelay, and NewOnDelay
> refer to the number of questions belonging to each classification for that
> particular learner.**"

**分类依据（Khudhur Table 1）**

| 分类 | 前测 | 后测 | 延迟后测 |
|---|---|---|---|
| **Review** | 对 | 对 | — |
| **New** | 错 | 对 | — |
| **ReviewOnDelay** | 对 | 对 | 对 |
| **NewOnDelay** | 错 | 对 | 对 |

**四个指标各自回答什么**

| 指标 | 回答的问题 |
|---|---|
| Normalized Review | 前测就会的那部分，有多少在后测仍保持 |
| **Normalized New** | **真正新学会了多少**（分母是"原本不会的"） |
| Normalized Review Retention | 复习过的知识，两周后还剩多少 |
| Normalized New Retention | 新学的知识，两周后还剩多少 |

**为什么它不可替代：**

FMS 只回答"最终对了几条命题"。
**这四个回答"学到的到底是新的，还是本来就会的"。**

论文原话（`10.58459_rptel.2026.21021.txt` 行 146）：

> "Learning gains are also separated into **reviewed knowledge and newly
> attained** knowledge"

**没有这四个指标，就无法排除"学生本来就知道"这个替代解释。**

**注意 Normalized New 的分母**：`1 − Pre`，与 normalized change 的
`Max − Pre` 同源，都是"还有多少可以提升"。

---

### 3.12c 设计威胁：前测敏感性（**已承认，未解决**）

**问题**：前测与后测用同一套题，学生会记得题目，
后测分数**部分来自记忆而非理解**，会高估学习增益。

**学界的标准解法存在**——**Solomon 四组设计**（Solomon, 1949）。
[Utwente 的统计文献](https://research.utwente.nl/en/publications/)摘要原文：

> "The Solomon four-group design (R. Solomon, 1949) is a very useful
> experimental design to investigate **the main effect of a pretest and the
> interaction of pretest and treatment**."

四组 = 前测+处理 / 前测+无处理 / 无前测+处理 / 无前测+无处理。
靠四组对比把"前测本身的影响"与"前测×处理的交互"分离出来。

**为什么我们不用**

| 原因 | 说明 |
|---|---|
| 需随机分到**四个独立组** | 需要至少 4 个班、足够样本 |
| 样本规模不支持 | 教材与班级由用户自定，规模未定但不会大 |
| **前测敏感性无法用统计修正** | 只能靠设计，不能靠事后校正 |

**Khudhur 也没处理。**
他的方法部分只写了 "shared identical questions"，
**通篇没有提及记忆效应或前测敏感性**（`...rptel.2026.21021.txt` 行 531–534）。

**所以我们既不能援引先例说"论文这么做的所以没问题"，
也不能声称我们解决了。**

**建议写进论文"局限"一节（措辞已备好）：**

> 本研究前测与后测使用同一套题。该设计存在前测敏感性风险：
> 后测增益可能部分来自题目记忆。标准解法为 Solomon 四组设计，
> 但需随机分配至四个独立组，本研究样本规模不支持。
> 该风险以两周延迟后测部分对冲——延迟后仍答对者，
> 记忆解释的说服力较弱。

**为什么这个措辞是站得住的**：
它**承认了标准解法存在**，说明为何未采用，并给出了部分对冲。
**比沉默或硬说没问题都更负责。**

---

**定义**：当分数接近满分时，方差压缩，均值差异不可检出。

**论文证据**（`10.1186_s41039-017-0060-x.txt` 行 700–710）：

> "The average of the third map score in group B is 0.967 (SD = 0.117).
> The summation between the average score and the standard deviation is
> higher than the maximum value ... which is statistically confirmed by the
> **ceiling effect**."

**对本项目的影响**：**学习模式的分数必然天花板**（可循环到全对）。
所以：
- 学习模式的均值比较**无意义**
- 测验模式若题目简单也可能天花板
- **必须在报告里显式检查**：`mean + SD > max` 即为天花板征兆

---

## 3A. 一个重要的发现：FMS 之外还有 SMS（**但我们不做**）

### 3A.1 发现

`10.58459_rptel.2024.19021.txt`（Rismanto et al., 2024）摘要原文：

> "KB employs an automatic assessment method called **'Full Map Scoring (FMS)'**,
> which evaluates the learner's understanding based on the recomposed concept map.
> **However, FMS only evaluates the final product of the recomposition activity,
> neglecting the process itself.** This is a potential limitation because
> **different processes leading to the same result could reflect different levels
> of understanding** among learners."
>
> "A multiple linear regression analysis confirmed that **the SMS score was a more
> precise predictor of learning gain than the FMS score**."

**SMS（Sub-Map Scoring）**评的是**重组顺序的连续性**：
若学生理解了某个子图的含义，他会把这个子图的命题**连续地**连起来。

原文的例子（行 345–356）：

```
Learner A 重组序列: {P1, P2, P3, P5, P4, P14, P12}
子图 SM1={P1,P2}, SM2={P3,P4,P5}, SM3={P12,P14}
→ SM1: 2/2, SM2: 3/3, SM3: 2/2  → SMS = 100
Learner B: 同一批命题但顺序散乱 → SMS = 33
```

**也就是说：同样的最终答案，过程不同，SMS 不同，而 SMS 更准。**

### 3A.2 为什么我们不做（用户已定）

**决定性理由（原文行 265–266）：**

> "As a preparation of SMS, **a teacher is required to define several sub-maps
> in the teacher's map**."

**划分子图必须由老师做。而本项目没有老师**（README_PLAN 第 0 节）。

**其他理由：**
- SMS 需要记录**完整的重组顺序**（第三张表／操作序列），成本远超收益
- 划分子图是领域判断，LLM 划的子图没有依据，等于又引入一个效度漏洞
- 我们当前的核心问题（LLM 目标图是否可信）都还没解决，
  加 SMS 会分散验证资源

**但这件事要记进 WHY.md**：
> 我们知道存在比 FMS 更准的 SMS，且知道它更准的证据。
> **不采用的理由是"无老师划分子图"，不是"不知道"** —— 这是主动取舍。

### 3A.3 一个几乎零成本的折中（建议，待你定）

**记录每次连线的时间戳与顺序，但不实现 SMS 算法。**

- 成本：几乎为零（前端本来就要处理连线事件）
- 收益：将来若有了自动划分子图的办法（比如让 LLM 提议 + 你审核），
  **数据还在，可以直接算**
- 风险：多一张表要维护

**我倾向：不做这张表**，因为你说"不做 SMS"。
若将来真要做，前端加日志即可，不必现在就建表。

---

## 4. 要不要第二张（question-level）表？—— 现在的答案

**先看哪些统计量必须有 item-level 数据：**

| 统计量 | 需要 item-level？ | 说明 |
|---|---|---|
| Normalized change | ❌ 不需要 | 用总分即可 |
| Wilcoxon 前后测 | ❌ 不需要 | 用总分 |
| Mann–Whitney 组间 | ❌ 不需要 | 用总分 |
| Kruskal–Wallis | ❌ 不需要 | 用总分 |
| **Cronbach's alpha** | ✅ **必须** | 需要每题得分 |
| **Khudhur 的 Review/New 分解** | ✅ **必须** | 要按题看三段正确性 |
| 相关（G1） | ❌ 不需要 | 总分相关即可 |
| F1（G5） | ❌ 不需要 | 命题集合，不是题 |
| ROC/AUC（G6） | ❌ 不需要 | 抽取级标签 |

**结论（已由用户拍板）：做第二张表，现在就做。**

**若只做 G1–G4 和 G5/G6，不需要第二张表。**
**但要做 Cronbach's alpha 或 Khudhur 的 Review/New 四指标，则必须。**

**用户已定：现在就做。** 字段设计见 `CSV_PLAN.md` H 节。

**我原先建议"后置"，理由与现在的决定并不冲突**：
我担心的是一次性建太多表、第一里程碑被拖慢。
但既然题级表只依赖**第一张表已有的四个键**，
现在一起建反而省事（将来补不上才是真麻烦）。
理由：

1. **Cronbach's alpha 是 TAM 量表的必需信度证据**，没有它，
   主观量表部分无法自证（Prasetya 明确用 0.7 作判据）
2. **Review/New 分解是 Kit-Build 研究的标志性指标**
   （区分"复习了"还是"新学会了"），
   若不做，就丢掉了一个很有力的论点
3. **但这两者都不是第一个里程碑的事**（D11：先搭再看）

**所以：第一张表（被试级）现在设计；第二张表（题级）留接口，暂不实现。**
**关键是不能把第一张表设计成"无法关联到题"** ——
即：题级表的关联键必须是**已有字段**（被试 ID + 教材 ID + 版本），
否则将来补不上。

---

## 5. 已确认与仍待确认

### 已确认

| 问题 | 结论 |
|---|---|
| 前/后测形式 | **逐题**，且**前/后/延迟用同一套题**（对齐 Khudhur） |
| 题型 | **只用客观单选**（每题对/错），不设主观题 |
| 延迟后测 | **做**，同表存放（`time_point` 区分） |
| 题级表 | **现在就做**（long 格式） |

**前/后测同卷的代价（见 3.12c，措辞已备好）**：
存在**前测敏感性**风险，标准解法是 Solomon 四组设计，但样本规模不支持。
Khudhur 亦未处理。**在局限一节必须承认，不能援引先例当作已解决。**

**同卷的唯一正当理由**：3.12b 的四个指标**必须**逐题比对三阶段，
平行卷会使 Review/New 分类无从判定。**这是有意识的取舍，不是疏忽。**

### 已确认（本轮拍板）

| 问题 | 结论 |
|---|---|
| 做实验/对照分组 | **做**，效能试验，不做机制分解 |
| TAM | **用**，中文量表由用户提供 |
| 样本规模 | **n = 120**，便利样本、个体区组随机 |
| 前/后/延迟 | **同卷**，任课教师同意，风险入局限 |

**n=120 的检验力（双侧 α=.05, power=.80，两组各 60）：**

| 口径 | 最小可检出效应 |
|---|---|
| 单教材 | d = 0.51 |
| **两教材（k=2, r≈.5）** | **d ≈ 0.44** |

- 两教材修正因子 `sqrt((1+(k-1)r)/k)`；r 取 .5 是保守假设，实际更高则更有利
- **没有班级层级**（个体招募）⇒ 多层模型不做，区组进固定效应
- Shapiro–Wilk 在 n=120 仍可用（远未到 5000 的过度敏感区）

### 仍待确认

1. `内容维度` 的具体取值（第一次测验后再收敛成枚举）
2. TAM 中文量表条目（等用户提供）

### 已补充的一处实测（本轮）

- **§7 全节为实测**：R 4.5.2 跑通全流程；
  发现 Normalized 指标的**单位混用**会把指标算出 >1（§7.3），
  且随机效应会**奇异**（§7.4）。两者均已给处理规则。

### 已补充的两处修正（本轮）

- **3.12a 已修正**：原文 r=0.30–0.40 是**该文引用的前人研究**，
  它自己的结果是 .71–.77。**不要预设相关值，必须自己算。**
- **3.12c 新增**：Solomon 四组是标准解法，我们用不了；**措辞已备好**。

---

## 5A. 本轮新增的外部引用（供论文写作）

| 文献 | 用途 |
|---|---|
| Solomon, R. L. (1949). An extension of control group design. | **前测敏感性**的标准解法（四组设计） |
| Utwente 统计文献（`research.utwente.nl`） | Solomon 四组的数据分析方法 |
| Taricani & Clariana（`10.1007_s11423-006-6497-z.txt`） | 概念图分数 vs 选择题的相关 |
| ↑ 该文需注意三点 | 无前测 / 开放式图 / PFNet 评分，均不可照搬 |

**⚠️ Taricani 那篇的三个不可援引之处（写论文时别引错）：**

1. **它没有前测** —— 所以不能用它论证"同卷是可接受的"
2. **它是开放式概念图** —— 与封闭 kit 是相反设计
3. **它用 PFNet 邻近矩阵评分**，不是命题级查表

**它唯一可援引的是**：概念图分数与选择题分数的相关值（且需分清哪组数字是谁的）。

---

## 6. 一张图总结

```
                    ┌── 正态性 (Shapiro-Wilk)
                    │        ↓
前测同质性 ─────────┤   参数？非参？
                    │        ↓
                    │   非参 → Wilcoxon(组内) / Mann-Whitney(组间)
                    │        Kruskal-Wallis + Dunn(多组)
                    │        ↓
                    └── 效应量 r = Z/√N  （必报）

学习效果 → Normalized change（不是 gain）
         → 天花板效应检查（mean+SD > max ?）

效度 G1  → Pearson/Spearman 相关
效度 G5  → F1 + P/R（**不用 kappa**）
检测 G6  → ROC/AUC
量表     → Cronbach's alpha（**需题级数据**）
聚类     → 多层模型（**需班级字段**）
```

## 7. 用 R，不用 Python（已定）

**理由不是偏好，是可复现性**：本领域审稿人与复核者默认在 R 生态，
用 Python 复算要把整个 pipeline 重写一遍，而 R 脚本可直接交出去。

### 7.1 环境（已在本机跑通）

```
R version 4.5.2 (2025-10-31)
lme4 1.1-37   lmerTest 3.1-3   rstatix 0.7.2
pROC 1.18.5   psych 2.4.3      emmeans / car / effsize 均在
```

- `FSA`、`irr` **未装**：Dunn 用 `rstatix::dunn_test()` 替代，不需要 FSA；
  人-人一致性用 **F1/Jaccard**（见 3.9），不需要 irr 的 kappa
- **不为此装新依赖**（AGENTS.md 边界）

### 7.2 每个统计量对应的 R 函数

| 统计量 | R |
|---|---|
| 前测同质性（非参） | `rstatix::wilcox_test(pre ~ group)` |
| 组间主模型 | `lmerTest::lmer(post ~ group*pre + txt + ord + (1\|subj))` |
| 组内前后测 | `wilcox_test(post ~ pre, paired = TRUE)` |
| 非参效应量 r | `abs(qnorm(p/2)) / sqrt(N)`（不是 `effsize`，见 3.7） |
| K–W + Dunn | `kruskal_test()` → `dunn_test(p.adjust.method="holm")` |
| 正态性 | `shapiro.test()` 或 `rstatix::shapiro_test()` |
| Normalized change | 见 7.3 |
| Cronbach's alpha | `psych::alpha()`，报 `raw_alpha` |
| ROC / AUC | `pROC::roc()` → `auc()`；阈值用 `coords(..., "best")` |
| 多层/区组 | `lmer(... + (1|subj))` |

### 7.3 Normalized 指标的**单位陷阱**（已实测）

Khudhur 的公式写作 `New / (1 − Pre)`，其中 **Pre 是比例**。
但 `New` 若取"条数"而 `Pre` 取"比例"，两者单位不一致，结果会离谱。

实测（k=10 题，200 人模拟）：

| Pre 的单位 | Normalized New 最大值 | >1 的比例 |
|---|---|---|
| 比例（错） | **10.0** | 94.5% |
| 条数/总数（对） | **1.000** | 0% |

**规则**：全部用条数除以`(k − Pre条数)`，或全部用比例；**混用必错**。
同理，Review 侧要 `n_review / n_pre`，**不是** `n_review / k`——
分母是"这个人前测就会的条数"，不是总题数。

### 7.4 随机效应可能奇异（会真实发生）

模拟中 `lmer(post ~ group*pre + txt + ord + (1|subj))` 曾报：

```
boundary (singular) fit: see help('isSingular')
随机截距方差 = 0.0003
```

**原因**：每人只有 2 个教材 × 3 时点，被试内相关本就弱，随机截距方差趋零。
**处理顺序**（不要一上来就去掉随机项）：

1. 先看 `isSingular(m)` 与 `VarCorr(m)`；
2. 方差≈0 时，**试随机斜率** `(1 + txt | subj)`；
3. 仍奇异则退 `lm()`，并在论文写明"被试内相关可忽略，故用 OLS"；
4. **不得**因为奇异就删数据。

**这是本设计的已知弱点**：每教材只有 1 次观测，被试内重复太薄。
若最终 n 偏小且奇异频发，改用**宽表 + 配对检验 / rmANOVA** 更诚实。

### 7.5 脚本与产物的存放

- 分析脚本进 `docs/research/`（**不新建文档目录**，遵循 AGENTS.md）
- 随机种子、包版本、R 版本必须写进脚本头部，否则不可复现
- **不把算好的派生量写回数据库**（SPEC §关键技术点：存原始量）

<!-- /@zone research -->
