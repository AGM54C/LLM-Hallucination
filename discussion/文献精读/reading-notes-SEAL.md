# 全文精读：Self-Authored Verification Is Unreliable in Heuristic Self-Improving Agents

阅读日期：2026-10-14。以下论文数字均为作者报告，本轮未复现、未训练。

## 版本、可用材料与读取边界

- 作者：Diandian Guo, Cong Cao, Fangfang Yuan, Yingqi Wang, Yueshan Wang, Dakui Wang；中国科学院信息工程研究所/中国科学院大学。
- [arXiv:2607.24300v1](https://arxiv.org/abs/2607.24300v1)，v1 = 2026-07-27；检索时只有 v1。PDF 标注 AAAI 2027 模板版权不构成录用证据，本文按预印本处理。
- PDF 全 9 页已完整读取：p.1—7 正文、p.8—9 参考文献。逐页文本与 PDF 保存在同目录。p.3 Fig.2、p.5 Tables 4/5、p.6 Figs.3/4、p.7 Table 6/7 和 Figs.5/6 已渲染核查；全部 9 页均有渲染文件。
- SHA-256：`0a1434ea1c9b533855c856bf49ff5271d1bcc70aa1cb3ac8f040250b5f46f372`。
- **补充材料限制**：p.3 说证明和限定条件在 supplemental materials；p.5 说额外分析在 supplementary materials。当前公开 PDF 没有这些附件。已下载 arXiv `src/2607.24300v1` 的源包并列出全部文件：仅 `main.tex`、样式、README 和 6 个图 PDF，未附 supplement；`main.tex` 无附录 input/include，arXiv 摘要页也无补充/代码项目链接。保留的[公开PDF](<../../综述选题-20261010/参考文献/Self-Authored Verification Is Unreliable in Heuristic Self-Improving Agents.pdf>)仍是本次阅读依据。因此可以说**公开 PDF 全文已读**，不能声称已读作者提及但未公开在该版本中的补充证明/实验。

## 1. 问题与已有工作的区别（p.1—2）

研究对象是程序式 heuristic policy 与 tests 的共同改写，基础 LLM 权重不更新。fixed-specification program synthesis 常有外部验收标准；heuristic learning 需要试错，agent 往往自行维护测试和 proxy metric。问题不要求 agent 故意作弊：只要 policy 与 tests 共享错误假设、测试分布变简单、阈值被改小，就可能自测分数很好而真实表现差。

作者称之为 verifier–deployment gap。与固定 reward hacking 的区别在于 evaluator 本身成为可修改状态。它不是一般意义上“LLM 永远不能自纠错”的证明，而是研究具有这种控制权结构的迭代系统。

## 2. 形式化与理论陈述（p.3）

状态 `x_t = (π_t, T_t)`，候选 `x'_t = (π'_t, T'_t)`。agent 看见当前代码、测试、此前反馈和 self-test 输出，形成 `H_t`。自测产生 `r_t = V_(T'_t)(π'_t)`。隐藏部署评估 `Y_D(π)` 只离线报告，不进入 agent context，不决定接受；这是与 gate audit 不同的第三条信号。

文中条件性下界：对非退步/退步两种情况可见证据分布 `P+ / P−`，任何仅用这份内源证据的 gate 满足 `α + β ≥ 1 − TV(P+, P−)`，因此若 TV ≤ δ，至少一种错误概率 ≥ (1−δ)/2。α 是错误拒绝，β 是错误接受。

**含义严格受条件限制**：如果两类世界从可见证据不可区分，gate 不可能同时把两类错误做小。这是标准可区分性下界；它没有证明内源信号总无信息，也没有证明 SEAL 是唯一/最小办法，更没有普遍证明所有自改进都需要外源信号。作者 p.3 本身明说这些限定。

独立代数核对（不是作者补充证明已读）：记接受事件为 B，则 `α+β=1−P+(B)+P−(B)≥1−TV(P+,P−)`。这只核对了显示公式的基本逻辑，不能补足未公开的补充材料和实验细节。

## 3. SEAL 机制（p.3—4，Fig.2、Algorithm 1、Table 2）

Sealed Exogenous Acceptance Loop 保留 agent 自写 tests 作调试；部署准入由受保护、task-native、可执行 audit 决定。它不是换一个 supervisor LLM。审计样本/seed 与 dynamics 不由 agent 编写、选择或查看，且与 training、自测、最终 deployment evaluation 分离。

对同一份隐藏 audit 运行 incumbent 与 candidate，得 `b_t=A(π_t)`、`c_t=A(π'_t)`。slack 为 `δ_t=max(δ_min, ρ|b_t|)`。当 `c_t ≥ b_t−δ_t` 时接受，否则保留**整个 policy–test 状态**，防止只回滚 policy 而让已漂移的 tests 成为下一轮状态。返回 agent 的 audit 反馈仅为 accept/reject，隐藏数值、seed、每例结果、slack。

该规则允许小于 slack 的退步，并且只防明显 audit regression，不要求每个接受更新提高真实目标。这一点与“自我改进每一轮都更好”不同。

Table 2 的四项为 exogenous audit、audit confidentiality、single-bit feedback、conservative update。它的“Agent cannot adapt to the audit”“Audit score does not become a new target”等表达应作工程目的理解。**accept/reject 仍携带依赖 audit 的信息**；公开全文未给长期自适应泛化保证、严格信息泄漏上界或无限轮次保护证明。隐藏数值可减少反馈信息，不等于零信息。

## 4. 实验设计（p.4—5，Tables 3—5）

环境为 Atari/ALE 程序策略，不是自然科学推导。每轮 agent 修改 `policy.py` 与 `tests.py`，从弱初始程序策略出发，一般 10 个 outer rounds。部署评估施加 agent 看不到的 dynamics shifts，例如 sticky actions / repeat-action probability。最终 truth 是最终 accepted policy 在 5 个隐藏部署 seeds、每个 seed 6 个完整 episode 的平均 raw return。

探索矩阵：7 个模型 × 5 个游戏（Breakout、Pong、SpaceInvaders、Seaquest、MsPacman）。7 个模型是 DeepSeek-V4-Flash、Gemini-3-Flash、MiniMax-M2.7、Doubao-Seed-2.0-Pro、Kimi-K2.5、Qwen3.6-Plus、GPT-5.5。主 Breakout 消融用其中 6 个模型（不含 Qwen），每条件 3 个 seeds；模型名称按论文报告，未独立核查底层服务快照。

条件：none（无保护）；monotone（只加强/追加自写测试）；discriminative（须超过 trivial baseline）；endo-gate（自写 tests 比 incumbent/candidate，带 accepted state retention）；SEAL；leaky-anchor（同 audit、拒绝后泄露数值）。文中有“five conditions”的简化措辞，Table 3/5 实际含泄漏对照共六列，报告时逐列说明更准确。

多 seed 结果是 **mean ± half-range**，不是标准误、标准差或置信区间。公开版本缺少完整 audit 参数、slack 数值、提示和实现细节，且指向未附补充材料，限制可复现性判断。

## 5. Finding 1：高自分数可能失去部署意义（p.5—6，Table 4、Fig.4）

35 个 model–game cell 的自测分数全 ≥0.70，但 15 个最终策略低于相应 random reference，6 个 Pong cell 在 −21 的底部。作者区分 failure to discover（从未发现好策略但自测满分）和 failure to retain（曾找到的策略被后续修改破坏，自测仍高）。

不能把不同 raw return 与 0—1 自分数直接相减作为统一误差。Fig.4 仅在 Breakout 中以所有模型最高 final mean 对 truth 归一化，属于图示性的 gap，而非跨任务有统一意义的概率校准指标。能力分层来自这些有限模型/任务轨迹观察，未受控地单独操纵“模型能力”。

## 6. Finding 2：内部约束不足；SEAL 改善保留（p.6—7，Tables 5/6、Figs.3/5）

Table 5 中，monotone 和 discriminative 都在 6 个核心模型中的 4 个低于 none。原因解释是：更严格的 tests 仍可取自不代表部署的分布；击败很弱的 baseline 也不意味着保持 incumbent 已有能力。SEAL 六个模型的 final mean 全高于 none。例：Gemini 7.9±0.8 → 30.0±9.7；Doubao 19.1±17.9 → 35.1±26.0；这些 ± 均为 half-range。Kimi 的 endo-gate 为 OOT，不能将该缺测格称为定量胜出。

leaky-anchor：SEAL 六格中五格更好，一格持平，Doubao 35.1 vs 12.7 差别较大。这支持在此设置减少 audit 数值暴露的实用价值，未证明所有任务下单比特总优于更丰富反馈。

Table 5 没有控制 proposal budgets。Table 6 是 **candidate-proposal-count matched pilot**，四模型平均 final truth 为 none 7.7、endo-gate 13.9、SEAL 15.4；平均 peak-to-final loss 为 6.9、0.5、0.4。不能把“proposal 数相同”称为总 token、审计运行次数、wall-clock 都匹配。回滚结构本身贡献很大；相对于 endo-gate 的剩余差为平均 1.5，且 DeepSeek 一格 endo-gate 16.4 高于 SEAL 16.2。不能把全部保留收益都归因外源性。

Fig.5 的较长 SEAL trace 接受早期两个状态后拒绝 19 个候选，说明保护已发现行为，也揭示可能停滞。作者主动报告反例：某次接受将 audit 12.7 提高到 14.2，而 deployment truth 从 17.6 下降到 13.8。因此 gate 仍依赖有限样本 proxy 的排序保真，**不是逐轮真实改进保证**。

## 7. Finding 3 与结论（p.7，Table 7、Fig.6）

Breakout 之外，4 模型 × 3 游戏 = 12 比较：SEAL 9 个更好、2 个持平、1 个更差。更差的是 DeepSeek SpaceInvaders：310±31 → 297±22；± 仍是 half-range。Pong 有两模型仍停留 −21。normalized peak-to-final loss 在 9 格改善、2 格不变。该结果不能写成全部任务都提升，也不能把多个 Atari 游戏当成多个科学/程序/现实领域的泛化证据。

结论把外部验收边界说得较强。本轮采用其条件化版本：**当 agent 同时能改 policy 和其自测依据、且内源证据不能可靠区分部署退步时，受保护的外源验收可在这些实验里减少大幅回退。** 不将其提升为无条件理论必要性。

## 8. 对受限科学验证器的可迁移启发

论文直接支持的是权限/信息流设计和迭代评价，未直接支持新的科学 soundness 定理。

1. **分离提议与批准**：科学 agent 可以提出证明步骤、候选前提、反例与测试，但不能自己决定这些项目获得“已验证”标记。受保护的 checker/证据登记管理批准权。
2. **回滚依赖全状态**：撤销错误结论时，应同时撤销或标记依赖它的推导、记忆和技能。只修最终答案，错误测试/前提仍可能在后续轮次复活。此项是由 SEAL whole-state rollback 向科学依赖图的设计外推，并非文中实验。
3. **单调规则不充分**：只允许新增检查条目，仍不保证检查覆盖适用条件、隐藏前提与 OOD 科学情形；需要独立反例/审计集和范围条件。
4. **接受信号与最终评价分离**：开发过程中可看的检验、决定更新的审计、最终 held-out 评价不能混作一个集合。
5. **推导正确与前提真实分离**：形式 checker 可证明在给定 axioms/assumptions 下的结论，不会自动证明经验前提符合自然世界；引用、模拟和独立 LLM 也不自动填补这个缺口。

建议研究量：未经支持前提被批准的比例、已证步骤的误拒绝率、依赖污染扩散与撤销成功率、多轮 regression、holdout task/assumption shift、审核成本。它们比只报告最终答案准确率更贴近用户目标。

## 可引用原文

| 页码 | 原文短句 | 使用限制 |
|---|---|---|
| 2 | “This does not require explicit cheating.” | 描述该控制权结构，不推断意图 |
| 3 | “This is a conditional information limit” | 不能升级为内源验证普遍不可能 |
| 3 | “It is an executable, task-native scoring procedure.” | SEAL audit 不是另一个 LLM judge |
| 4 | “It only blocks candidates that clearly regress under an external sealed audit.” | 不保证每次更新提升 |
| 6 | “strengthen tests on an unrepresentative distribution” | 解释为什么 monotone alone 不足 |
| 6 | “Table 5 does not control proposal budgets across conditions” | 对主消融的计算归因保留限制 |
| 7 | “The audit remains a finite-sample proxy.” | 最核心的外推边界 |

## 本轮证据等级

公开 PDF 全文及关键图表：已读；版本与题名作者：arXiv + OpenAlex 双核；源包是否附 supplement：已检查，无；作者补充证明与额外实验：未获取，不能称已读；代码训练/实验：未运行。本分支没有全文阅读 CoEvoSkills 等被引研究；Red Queen Gödel Machine 已由另一分支完成全文，见[独立笔记](rqgm-2606.26294v3-reading-notes.md)，不把它混作本篇 SEAL 的实验依据。
