# Agent 自演化与受限科学验证器：定向证据汇总

日期：2026-10-14。范围：一篇广泛的新综述，加一篇直接研究自写验证失效的原始研究。它们回答“什么在改进、谁提供验收信号”，不回答主分工中的 RLVR 能力边界。

## 已完成的阅读

| 论文 | 日期/版本 | 本轮阅读 | 证据类型 |
|---|---|---|---|
| [Self-Improvements in Modern Agentic Systems: A Survey](https://arxiv.org/abs/2607.13104v1), Ren et al. | 2026-07-14, v1 | PDF 1—97 全部：正文 1—57；参考文献 57—95；Notation 96—97；复杂图表核查 | 文献整理、形式化与设计建议；无本轮复现 |
| [Self-Authored Verification Is Unreliable in Heuristic Self-Improving Agents](https://arxiv.org/abs/2607.24300v1), Guo et al. | 2026-07-27, v1 | 公开 PDF 1—9 全部；关键图表核查；另检查 source archive | Atari 程序策略与测试共演化的原始实验；作者提到的 supplement 未附在公开版本，未读到；无本轮复现 |

逐节笔记分别见 `reading-notes-survey.md` 与 `reading-notes-SEAL.md`；PDF、版本页面、哈希、页码全文、源包与检索日志均在本目录。

## 1. 近期文献的“self-improvement”通常比强 RSI 更宽

Ren et al. 把 agent 写为 `A_t=(θ_t,Σ_t)`，其中 `Σ_t=(prompt,memory,tools,control logic)`（p.12）。普通执行历史是临时状态；自改进通过 U 提交跨任务持久变化（p.13）。由此至少要区分：

| 层次 | 改变对象 | 仍需追问的外部依赖 | 是否单凭此事就达到递归改进器 |
|---|---|---|---|
| 权重自训练 | θ | 数据过滤、奖励、环境、更新器 | 否；更新器可以固定 |
| scaffold 自演化 | prompt、memory、tools、controller | 执行器、测试、配置准入 | 否；也可由固定优化循环完成 |
| 改进器递归自修改 | 产生下一轮更新的 I 本身 | 目标、验收标准、运行环境、资源 | 更接近强 RSI，但仍不证明无限或加速改进 |

综述 p.15 将“meta-level skill 自身也得到改进”单列为 improver 与被改进系统共同演化；p.40 的式 (23) 明确 `Σ_(t+1)=I_(Σ_t)(Σ_t;S_t)`。p.41 仍把现有系统描述为 bounded, verifiable loops，目标和安全协议由人设计。

因此，对当前科学验证器，**持久化经验证规则/技能**是一种可研究的 self-evolution；只有当“提出和评估下一次规则更新的方法”本身也参与学习时，才需要进一步声称更强递归层次。

## 2. 自生成任务与独立验收不矛盾

综述 p.25 的原句：“The agent may choose what to try, while the environment determines whether the attempt succeeds.” 它把自主提出任务、自己编写候选解与由环境执行判断成功区分开。相反，p.23 指出 self-consistency 只是 correctness 的 proxy；p.20 提醒任务分解可能丢失原问题约束。

对科学推理的启发是：模型可以探索新假设、构造反例、建议新中间步骤；**这些提议必须保持为候选，不能因被 agent 写入记忆、在多次采样中一致出现、或被自己的 critic 赞同，就升级为可用事实前提。** 这一句是本轮根据两篇文献作的设计外推，不是它们已经做过的科学推导实验。

## 3. 新原始研究把“自写检查不够”定位到控制权结构

Guo et al. 的 agent 同时修改 policy 与 tests。35 个无保护 model–game 格中，自测分数全 ≥0.70，但 15 个最终策略低于 random reference（p.5 Table 4）。问题可在无显式作弊时出现：tests 与 policy 共享错误假设，或 tests 不代表部署分布。

只准加强测试、或只要求超过 trivial baseline，都不能稳定修复该差距（p.6）。这一发现为综述 p.55 的“critic 只允许单调增强”建议补上边界：**单调性限制修改方向，不保证测试分布、前提或语义有效。** 这不是对“单调约束 + 独立审计”的整体反证。

SEAL 保留自写 tests 作改进线索，另外由 agent 无权编写或查看的 task-native audit 比较 candidate 与 incumbent，回传 accept/reject，并在拒绝时回滚 policy–test 全状态（p.3—4）。audit 与最终 hidden deployment evaluation 分离。p.5 Table 5 在 6 模型、3 seeds 的 Breakout 消融中，SEAL 的 final mean 均高于 none；p.7 的跨游戏比较是 9 改善、2 持平、1 变差，不是无例外优势。

最重要的负面证据来自它自己：audit 从 12.7 升到 14.2 的一次接受更新，真实部署 return 反而从 17.6 降到 13.8（p.7）。因此这只是减少明显回退的有限样本门控，并不保证科学真实性或真实目标单调增加。

## 4. 哪些主张不能从这些证据推出

- 不能推出 LLM 自纠错普遍不可能。SEAL p.3 的 TV 下界取决于正负情形的可见证据不可区分；它不是无条件必要性定理，也没证明 SEAL 唯一或最小。
- 不能推出隐藏 audit 绝不被适应。accept/reject 本身仍携带 audit 信息，文中没有长期自适应泛化保证。
- 不能把 Table 5 的 mean ± half-range 写成标准误或置信区间；三 seeds 的区间宽。
- 不能把 Table 6 的 proposal-count matching 写成总审计计算匹配；平均 endo-gate 13.9 对 SEAL 15.4 也表明仅回滚已贡献不少，单格可由 endo-gate 更好。
- 不能把 Atari 多游戏外推成跨科学领域验证成功。它没有测试 hidden scientific assumptions、量纲、守恒、因果前提或实验来源。
- 不能说“只要前提不增加，结论就科学可靠”。已登记前提可能不真实、过时、范围失配或仅是近似；形式推导有效性和实证前提支持程度是两个不同问题。
- 不能把读综述中的 CoEvoSkills、DGM、STELLA、MetaTextGrad、VASO 等介绍称为已全文读过这些原始研究。

## 5. 对当前方案的具体、可反驳启发

### 5.1 把前提准入和推导检查写成不同职责

可以先研究一个受控系统：候选生成器提出结论及显式前提依赖；受保护的证据登记仅保存已获得外部支持的前提；逐步 checker 验证在这些前提和合法规则下，结论是否成立。科学陈述的证据登记还应保存来源与版本、适用条件、不确定性、近似/理想化条件。用户提供、文献报告、实验观测、数值模拟和假设不得无标记互换。

“禁止自行增加未经验证前提”最好实现为**不能擅自把假设批准为事实**。系统仍可提出假设并输出“若 H 成立，则 C”的条件性结论，或提出需要实验验证的 proof obligation；否则会把科学假设探索也误杀。这个区分是本轮分析，不是文献已有方案的复现。

### 5.2 可演化的部分与受保护的部分分开

可演化：候选步骤生成、证据检索策略、反例提议、工具选择、证明搜索、经批准的技能复用。受保护：前提类型与证据准入语义、推理规则的 checker、最终 audit 数据、状态批准接口。受保护并不表示永不修订，而表示修订不能由被评估 agent 单方面自批准。

若撤销一个前提，需要沿依赖图使后代结论与技能失效，重新验证后再入库。它把 SEAL 的 whole-state rollback（p.4）与综述 memory lifecycle（p.31—37）的启发转化为科学工作流的依赖管理问题。

### 5.3 最小实验可隔离四种机制

在同一基础模型、同一任务分布、同一候选预算下，比对：（a）自由反思；（b）显式列出前提但自行批准；（c）只追加检查/规则；（d）独立前提准入 + 步骤检查 + 依赖回滚。分别记录 proposer、checker 与 audit 的计算预算，保持 final holdout 隔离。应额外对“只回滚”“只做最终答案验收”做机制对照，避免把收益全部误归因于前提类型系统。

任务需要含真实可检查的错误来源，例如悄悄加入独立性、边界条件、封闭系统、平衡态、线性近似或分布假设；不能只在文本里删一句显式条件就算覆盖科学推理风险。应同时包括有效但复杂的推导，测试系统会不会过度拒绝。

可证伪的问题是：**在多轮自改进中，独立前提准入能否在保留已验证任务能力和相同总验证预算的条件下，降低未经支持的假设被持久化与跨任务复用的概率？** 若仅降低回答率、或只对明显缺前提有效，便不能支持强方案；若换一个相关 LLM judge 就失效，也说明没有实现可靠独立检查。

建议主要度量：unsupported-premise acceptance、valid-chain false rejection、推导步骤错误率、前提撤销后的后代失效覆盖、跨条件/OOD 假设迁移、逐轮 regression、总验证开销。最终答案准确率应保留，但不足以单独证明前提约束有效。

## 检索中更晚的线索（不计入全文精读）

本轮两轮检索还返回 Safety in Self-Evolving Agents（2610.00093）、Auditing Harness Tampering in Self-Improving Agents（2609.00069）、Counterfactual Self-Evolving Agents for Evidence-Grounded Reasoning（2609.32870）等。前两项已核对 arXiv 摘要页，第三项只到检索元数据/摘要。它们说明截止日期前还有更新线索；本轮不声称七月综述是绝对最新或已穷尽九月以后工作，也不从这些摘要推出技术结论。
