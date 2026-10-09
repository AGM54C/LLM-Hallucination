# 30 篇核心文献

围绕当前的“证据读取、比较与决策”问题筛选。每篇目录只有原文 PDF 和中文想法；想法依据已有全文阅读记录整理，不代表独立复现。

建议先读：**InterPact → 生化序贯决策 → Computes-From → Test-then-Route → Elicitation-Matters**。这五篇最直接约束当前方案的贡献与验证方式。

## 科学发现

| 文章 | 为什么保留 |
|---|---|
| [01 · CoScientist](01-%E7%A7%91%E5%AD%A6%E5%8F%91%E7%8E%B0/01-CoScientist/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 科研假设的生成、批评、排序和修订已经形成闭环系统。 |
| [02 · SciMON](01-%E7%A7%91%E5%AD%A6%E5%8F%91%E7%8E%B0/02-SciMON/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 检索灵感、生成科研想法和新颖性修订已有参数训练方案。 |
| [03 · SciDisco](01-%E7%A7%91%E5%AD%A6%E5%8F%91%E7%8E%B0/03-SciDisco/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 可执行的科学分析环境与过程奖励已经用于训练 Qwen3-14B。 |
| [04 · 生化序贯决策](01-%E7%A7%91%E5%AD%A6%E5%8F%91%E7%8E%B0/04-%E7%94%9F%E5%8C%96%E5%BA%8F%E8%B4%AF%E5%86%B3%E7%AD%96/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 生化有限实验库中的匿名化、证据获取和决策评价已有直接先例。 |
| [05 · ether0](01-%E7%A7%91%E5%AD%A6%E5%8F%91%E7%8E%B0/05-ether0/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 化学推理已有大规模强化学习及难度、奖励变化驱动的选样。 |

## 证据与决策

| 文章 | 为什么保留 |
|---|---|
| [06 · InterPact](02-%E8%AF%81%E6%8D%AE%E4%B8%8E%E5%86%B3%E7%AD%96/06-InterPact/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 读出中间条件和让最终决策依赖条件是两件事，已有匹配训练消融。 |
| [07 · Context-Memory](02-%E8%AF%81%E6%8D%AE%E4%B8%8E%E5%86%B3%E7%AD%96/07-Context-Memory/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 模型在上下文与参数记忆冲突时，信息可读出不保证被用于回答。 |
| [08 · 观察-信念-行动](02-%E8%AF%81%E6%8D%AE%E4%B8%8E%E5%86%B3%E7%AD%96/08-%E8%A7%82%E5%AF%9F-%E4%BF%A1%E5%BF%B5-%E8%A1%8C%E5%8A%A8/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 观察形成信念和信念影响行动可能在不同环节失效。 |
| [09 · Molecular-Blinding](02-%E8%AF%81%E6%8D%AE%E4%B8%8E%E5%86%B3%E7%AD%96/09-Molecular-Blinding/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 分子身份、数值变换与上下文学习需要分开评价。 |
| [10 · Elicitation-Matters](02-%E8%AF%81%E6%8D%AE%E4%B8%8E%E5%86%B3%E7%AD%96/10-Elicitation-Matters/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 相同观测在不同提示和查询协议下，可能产生不同数值预测与决策。 |

## 上下文检索与绑定

| 文章 | 为什么保留 |
|---|---|
| [11 · Entity-Binding](03-%E4%B8%8A%E4%B8%8B%E6%96%87%E6%A3%80%E7%B4%A2%E4%B8%8E%E7%BB%91%E5%AE%9A/11-Entity-Binding/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 模型如何把实体和属性绑定已有明确的内部干预研究。 |
| [12 · Lookbacks](03-%E4%B8%8A%E4%B8%8B%E6%96%87%E6%A3%80%E7%B4%A2%E4%B8%8E%E7%BB%91%E5%AE%9A/12-Lookbacks/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 信念追踪可能通过回看上下文位置及其内容完成。 |
| [13 · Mixing-Mechanisms](03-%E4%B8%8A%E4%B8%8B%E6%96%87%E6%A3%80%E7%B4%A2%E4%B8%8E%E7%BB%91%E5%AE%9A/13-Mixing-Mechanisms/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 上下文实体检索可能由多种机制共同完成。 |
| [14 · Test-then-Route](03-%E4%B8%8A%E4%B8%8B%E6%96%87%E6%A3%80%E7%B4%A2%E4%B8%8E%E7%BB%91%E5%AE%9A/14-Test-then-Route/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 条件真假判断与答案路由可以通过不同 donor 设计分开检验。 |
| [15 · Lost-in-the-Middle](03-%E4%B8%8A%E4%B8%8B%E6%96%87%E6%A3%80%E7%B4%A2%E4%B8%8E%E7%BB%91%E5%AE%9A/15-Lost-in-the-Middle/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 相关信息在上下文中的位置会明显影响模型表现。 |

## 机制验证与干预

| 文章 | 为什么保留 |
|---|---|
| [16 · Activation-Patching](04-%E6%9C%BA%E5%88%B6%E9%AA%8C%E8%AF%81%E4%B8%8E%E5%B9%B2%E9%A2%84/16-Activation-Patching/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 激活修补的结论会受损坏方式、度量和干预窗口影响。 |
| [17 · Halt-Vector](04-%E6%9C%BA%E5%88%B6%E9%AA%8C%E8%AF%81%E4%B8%8E%E5%B9%B2%E9%A2%84/17-Halt-Vector/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 将因果 steering 干预内化到参数，并在推理时去除 hook，已有直接先例。 |
| [18 · Computes-From](04-%E6%9C%BA%E5%88%B6%E9%AA%8C%E8%AF%81%E4%B8%8E%E5%B9%B2%E9%A2%84/18-Computes-From/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 能改变答案的 steering，不一定写入了会被后续计算使用的语义状态。 |
| [19 · Interpretability-Actionability](04-%E6%9C%BA%E5%88%B6%E9%AA%8C%E8%AF%81%E4%B8%8E%E5%B9%B2%E9%A2%84/19-Interpretability-Actionability/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 内部表示近乎可完全读出，也不保证能够纠正最终错误。 |
| [20 · Fine-Tuning-Mechanisms](04-%E6%9C%BA%E5%88%B6%E9%AA%8C%E8%AF%81%E4%B8%8E%E5%B9%B2%E9%A2%84/20-Fine-Tuning-Mechanisms/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 微调后的能力提升可能增强已有机制，而非产生全新机制。 |

## 学习与泛化

| 文章 | 为什么保留 |
|---|---|
| [21 · RLVR-Capacity](05-%E5%AD%A6%E4%B9%A0%E4%B8%8E%E6%B3%9B%E5%8C%96/21-RLVR-Capacity/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 训练后单次表现改善与可解问题集合扩大是不同的能力主张。 |
| [22 · State-Tracking](05-%E5%AD%A6%E4%B9%A0%E4%B8%8E%E6%B3%9B%E5%8C%96/22-State-Tracking/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 不同内部算法可能完成相同训练任务，并表现出不同长度泛化。 |
| [23 · Artificial-Needles](05-%E5%AD%A6%E4%B9%A0%E4%B8%8E%E6%B3%9B%E5%8C%96/23-Artificial-Needles/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 简单合成检索训练已经能够迁移到自然文档问答。 |
| [24 · Faithfulness-Flow](05-%E5%AD%A6%E4%B9%A0%E4%B8%8E%E6%B3%9B%E5%8C%96/24-Faithfulness-Flow/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 训练时约束信息通路，已有用于改善推理过程忠实性的研究。 |
| [25 · SCoRe](05-%E5%AD%A6%E4%B9%A0%E4%B8%8E%E6%B3%9B%E5%8C%96/25-SCoRe/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 让模型真正学会自我纠错，不能只靠重复询问或模仿修订文本。 |

## 科学评价与证据管理

| 文章 | 为什么保留 |
|---|---|
| [26 · AskChem](06-%E7%A7%91%E5%AD%A6%E8%AF%84%E4%BB%B7%E4%B8%8E%E8%AF%81%E6%8D%AE%E7%AE%A1%E7%90%86/26-AskChem/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 化学主张的条件、量值、来源和冲突，已有专门的证据基础设施。 |
| [27 · SciRigor](06-%E7%A7%91%E5%AD%A6%E8%AF%84%E4%BB%B7%E4%B8%8E%E8%AF%81%E6%8D%AE%E7%AE%A1%E7%90%86/27-SciRigor/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 科学分析的评价需要追踪数据、变换、结果与结论之间的支持关系。 |
| [28 · Stored-Is-Not-Supported](06-%E7%A7%91%E5%AD%A6%E8%AF%84%E4%BB%B7%E4%B8%8E%E8%AF%81%E6%8D%AE%E7%AE%A1%E7%90%86/28-Stored-Is-Not-Supported/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 信息被存进记忆，并不意味着它仍然支持当前主张。 |
| [29 · DiscoveryBench](06-%E7%A7%91%E5%AD%A6%E8%AF%84%E4%BB%B7%E4%B8%8E%E8%AF%81%E6%8D%AE%E7%AE%A1%E7%90%86/29-DiscoveryBench/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 数据驱动的科学发现需要比普通问答更明确的任务和评价边界。 |
| [30 · CruxBench](06-%E7%A7%91%E5%AD%A6%E8%AF%84%E4%BB%B7%E4%B8%8E%E8%AF%81%E6%8D%AE%E7%AE%A1%E7%90%86/30-CruxBench/%E6%88%91%E7%9A%84%E6%83%B3%E6%B3%95.md) | 主动寻找关键未知信息本身已有专门的评价任务。 |
