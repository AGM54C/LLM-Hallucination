# 全文精读：Self-Improvements in Modern Agentic Systems: A Survey

阅读日期：2026-10-14。本文为定向深读笔记，不是对综述全部引文的原始研究复核。

## 版本与阅读范围

- 作者：Zhe Ren, Yimeng Chen, Dandan Guo, Guowei Rong, Tonghui Li, R. B. Xiong, Qingfeng Lan, Wenyi Wang, Li Nanbo, Yibo Yang, Mingchen Zhuge, Jürgen Schmidhuber。
- 原文：[arXiv:2607.13104v1](https://arxiv.org/abs/2607.13104v1)，v1 = 2026-07-14；检索时 arXiv 页面仅列 v1。预印本，未据模板或作者身份推断同行评审状态。
- PDF 97 页；完整读取 p.1—97：p.1—4 封面、摘要、目录，p.5—57 正文，p.57—95 参考文献，p.96—97 未进入目录的 Notation 表。没有遗漏末尾符号表。
- PDF SHA-256：`896642aa98dc5a283147aa4245ef96e92891bbc72f31f727c1d36c761cfd70b8`。
- 页码与正文按[固定版本PDF](<../../综述选题-20261010/参考文献/Self-Improvements in Modern Agentic Systems： A Survey.pdf>)核对，提取文本已清理。
- 阅读分批：1—6、7—14（10 页另重读以补初次工具截断）、15—20、21—27、28—34、35—41、42—48、49—55、56—58、59—65、66—73、74—81、82—88、89—93、94—97。初始 `sort=True` 的截断输出不作为阅读完成证据。
- 复杂图表视觉核查：p.1 Fig.1、p.8 Fig.3、p.32 Fig.8/Table 3、p.34 Table 4、p.53 Fig.12；另渲染其他图表页，见 `rendered/2607.13104v1/`。Table 3 的方块是作者定性归纳，不是标准化实验得分；Table 4 的彩色圆点区分 primary / secondary / absent，文本抽取会丢失该差别。Fig.12 是使用关系矩阵，不是性能排行榜。

## 各节精读

### 1. Introduction（p.5—7）

文章把现代 agent 写为基础模型与 operational scaffold 的耦合。scaffold 包括 prompt、memory、tool interface、control logic，也称 harness。它的分类问题不是“是否自我反思”，而是“实际持久改变什么，以及改进信号从哪里来”。它把参数更新视为较慢的积累，把 scaffold 修改视为较快、较可回滚的适应。

此处的“self-improvement”定义相当宽，涵盖模型自己产生训练数据后由外部优化器更新权重。不能因为一个系统落在此综述内，就宣称它的改进器已被递归改进。引言中的 intelligence explosion 是历史动机，不是这篇综述的实验证明。

### 2. Historical Context and Theoretical Foundations（p.7—12）

2.1 从最小二乘、控制论、Turing child machine、早期学习程序追溯反馈适应，强调学习与显式自修改不等同。2.2 讨论 AM/EURISKO 将 heuristics 作为可修改对象；p.10 提醒 EURISKO 的成功依赖人类解释输出、剪除无效启发式等外部评价信号。2.3 讨论可学习学习规则、fast weights、自指权重矩阵与元学习；2.4 讨论 Gödel machine、反射、不完备资源下的安全自修改和 NAS；2.5 回到基础模型的快 context/scaffold 循环与慢权重更新循环。

对当前项目最有用的是历史上一直存在的“谁来判定自修改真的有效”问题。Gödel machine 的理想化证明条件涉及环境、效用与计算可表达性，不等于现代自然语言 agent 已有该保证。这部分主要是作者的历史叙述，本轮没有逐一复核历史原始文献；引用倾向集中于自指学习谱系，不能把该选择当作中立完备的科学史。

### 3. Definitions（p.12—17）

形式化为 `A_t = (θ_t, Σ_t)`，`Σ_t = (p_t, m_t, T_t, g_t)`。`X_t` 是临时执行状态，`U` 是提交持久修改的 update operator；普通会话历史增长与永久改变配置应区别。自参考有两种模式：自己的行为改变训练数据分布，从而间接改变 θ；通过行动直接改变自身的 Σ。

p.15 将 skill 定义为可序列化、可复用的配置更新，跨越 prompt、tool、memory、weights、control logic 等载体。object-level skill 作用于任务世界；meta-level skill 作用于 agent 配置。当 meta-level skill 自身也被改进，才出现“improver evolves together with the system it improves”的递归层次。这对原任务中 RSI 的术语边界很关键。

与 RL、online learning、active learning 的关系：更新 θ 接近固定框架内的策略优化；更新 Σ 可改变表示、可行动作及运行语义，通常用离散搜索或程序修改。scaffold 外显有助调试，但 p.16 明说并不消除遗忘，还可能引入 memory poisoning、工具语义漂移、模板脆弱性。p.17 的简化语句“without the risks of catastrophic forgetting”不能孤立引用为无遗忘保证。

### 4. Taxonomy（p.17—18）

第一轴是更新对象 θ / Σ；第二轴是信号形态。θ 更新分 intrinsic generative demonstrations、intrinsic evaluative feedback、extrinsic exploratory experience；Σ 更新按 prompt、memory、tool、full scaffolding 划分。类别可组合，作者按 dominant signal 分类，不能机械理解为互斥算法全集。

### 5. Foundation Model Improvement（p.18—26）

5.1（p.19—21）：生成任务、指令、推导轨迹、API 调用与执行记录，然后筛选和训练。p.20 指出自一致过滤会在“自信地反复犯同样错误”时失败；分解任务也可能不再保存原任务约束。p.21 讨论错误自训练、分布收缩、model collapse，以及真实/既有数据保留、外部 checker、theorem prover、diversity 和人工审计。这里的“内源生成”不保证标签也无需外部验证。

5.2（p.21—24）：评分准则、consistency/confidence、自然语言纠错是三种不同信号。p.22—23 明确“一致”只是正确性的弱代理；critic 也可能产出貌似合理的错误解释。作者建议分离 generator/evaluator 的 checkpoint 或模型族、保留外部锚点、把不一致当不确定性、定期复核评分。模型异质性是减小相关错误的工程策略，不是独立真值保证。

5.3（p.24—26）：外源信号包括执行环境与 learned proxy environment。程序测试、SQL、theorem proving、可检查 postcondition 提供较清楚的反馈；LLM reward model 仍是估计。p.25 特别区分：agent 可以自己提出任务，但执行器/环境决定成功与否，因此“任务自生成”不等于“正确性自我授权”。learned world model 可以降低探索成本，却可能伪造看似合理的转移；训练会利用这些模拟错误。对科学验证器，物理模拟器和语言模型都不能因处于 tool 层而自动获得真值地位。

### 6. Scaffolding Improvement（p.26—41）

6.1 Prompt（p.27—31）：scalar feedback、qualitative critique、population evolution、textual gradient 四类。p.29 表指出 critique 噪声、validator 依赖和 drift；p.30 的 Promptbreeder 还演化 mutation prompt，MetaTextGrad 还优化 optimizer prompt，属于比固定改进器更强的自指线索。textual gradient 是类比和结构化文字指导，不具备通常数值梯度的保证。上述具体原始研究本轮均未全文精读。

6.2 Memory（p.31—37）：分 memory object、structure、processing。对象包括 processed interaction trails、curated raw content、integrated external knowledge、latent representation；后两者中的“外部知识”与“latent memory”不能混为一个信任等级。p.32—33 对原始证据的精确保存和审计尤为相关：summary/heuristic 有概括偏差，raw artifacts 有细节保真但占空间，外部知识可能过时或接地失败，latent 记忆难以纠错。结构分 flat、hierarchical、graph、vector；graph 适合依赖追踪但有边更新和冲突维护成本。CRUD 不仅仅是添加记忆：无效合并可擦除关键前提，错误删除可失去旧能力，检索相似不等于对当前决策有用。

6.3 Tool（p.37—39）：动态路由、迭代修复、自动创建。执行成功不能只看 tool 是否运行；调用前提、参数、顺序、接口语义都可能错。p.38—39 强调工具修复同时是进入长期 skill repository 的准入控制。若错误工具被复用，错误会累积；标准化注册、文档和验证要与新工具一并维护。

6.4 Full scaffolding（p.40—41）：明确写成 `Σ_(t+1) = I_(Σ_t)(Σ_t; S_t)`，improver 实现在当前 scaffold 里，因而自身可变。候选 patch 经 `V(Σ_candidate)` 检查才能接受。作者将该类称为最接近 RSI，同时承认现有系统仍在人工设计目标、benchmark 和安全协议内。列表中的系统复杂程度不一，不能仅凭归类证明每个系统均修改了改进器。

### 7. Applications（p.41—50）

7.1 SWE（p.42—43）：编译、测试、CI 使反馈可自动化；SWE-agent/Agentless 默认只是 episode 内迭代，不属于持久自改进。benchmark 是评价基底，不等于自改进算法。测试可 flaky、覆盖不全、环境昂贵；需跨仓库、变异基准和防 verifier 过拟合。

7.2 Web（p.43—44）：非平稳界面、长轨迹、弱可观察结果；memory/grounding 快速适应与 reward-model/curriculum 训练互补，但对特定站点过拟合和旧数据漂移都存在。

7.3 Games（p.44—45）：规则清楚、可 reset 支持 self-play；窄对手分布、模拟器漏洞、非传递性和策略循环限制 win rate 的解释。

7.4 Scientific Discovery（p.45—48）：计算实验可能用 code/simulation/ablation，真实实验信号则延迟、昂贵、噪声大。证据管理、异质工具与协议往往比更新权重更直接。p.47 明确：系统难以自行确认 novelty、correctness、reproducibility，表面改进可能只是利用弱代理。建议 reproducibility-centered evaluation、evidence tracking、标准化实验/计算协议。此节不构成对任何“无幻觉科学验证器”的新实验支持。

7.5 Embodied（p.48—49）：试错成本、sim-to-real、硬件漂移与不可逆行动要求受限探索和恢复测试。7.6 General Computer Control（p.49—50）：跨应用程序过程复用、GUI 状态验证困难；state-based verification 优于仅凭语言自报告，但也受状态可观察性制约。

### 8. Evaluation（p.50—55）

以固定累计预算下的整个性能轨迹代替最终峰值。区分 executable metric 与 learned/model judge；两者都需要交代评估分布、持久对象、预算和可用反馈。p.51 建议报告 baseline、固定预算后的结果、逐轮曲线、held-out transfer、以前已解任务的 regression 和成本/人工监督。

p.52 对 judge 独立性和预算有直接要求：更新与最终报告共用 evaluator 容易过拟合，报告 judge identity、prompt、rubric、所见证据及其计算成本。独立 judge 配置并不等于事实真值，建议在可验证子集/人工复核上校准。

p.53 的机制归因要求组件消融、固定环境替换模块、旧任务回归检查。对科学工作流，p.54 优先可执行分析、可复现结果与可追溯来源；本文没有提供统一新 benchmark 实验。

### 9—10. Discussion / Conclusion（p.55—57）与 Notation（p.96—97）

p.55 建议先让外显 scaffold 进行快探索，再将经验证稳定的行为慢慢蒸馏进权重；critic 应作为受保护基础设施。生成更新与接受更新由同一主体无约束控制，会形成自我确认。演化 critic 可以被限制为单调新增测试并保留外部审计轨迹，但这只是建议，不是性能定理。p.56—57 讨论 test-time adaptation、curiosity、joint θ/Σ optimization、资源效率、multi-agent artifacts、开放世界漂移。

符号表进一步确认 `g_t` 可包括 control/routing/verification logic，`I_(Σ_t)` 为 scaffold improver，`V` 为 validation function。它没有为科学前提真值引入单独形式化或证明义务。

## 关键原文与页码

| 页码 | 简短原文 | 可支持的判断 |
|---|---|---|
| 13 | “the operator U commits durable changes” | 持久配置变化与临时上下文变化应分开 |
| 15 | “the improver evolves together with the system it improves” | 改进器自身变化是更强的递归层次 |
| 20 | “no longer preserves the constraints of the original task” | 自生成子任务/分解可能改变原始约束 |
| 23 | “consistency is only a proxy for correctness” | 自一致不能充当科学前提的真值检查 |
| 25 | “The agent may choose what to try, while the environment determines whether the attempt succeeds.” | 自生成任务和独立评价可以并存 |
| 38—39 | “a gatekeeping process that controls what enters the structural skill repository” | 验证既用于即时纠错，也用于防止错误持久化 |
| 40 | “the improvement procedure is itself implemented within the current scaffolding” | 此节存在明确自指形式化 |
| 47 | “Systems cannot easily verify novelty, correctness, or reproducibility on their own.” | 科学发现的验证瓶颈不能仅靠反思解决 |
| 51 | “Report trajectories under a fixed budget.” | 评估自改进过程而非择优末点 |
| 55 | “its updates can not be under the unconstrained control of the agent it evaluates” | critic 的更新权限需要受到独立约束 |

## 校准与对当前科学验证器的影响

本文最直接支持的设计启发是：把推理、记忆和技能的持久化当作需要验证的更新操作，保存来源、版本、适用条件和回滚依赖；把生成候选与批准入库分开。本文不证明只有一种架构有效，也没有验证“逐步逻辑检查”可保证科学结论真实。

“使用外部工具/引用”仍不等于“已验证前提”。例如模拟器只验证其模型条件下的预测，文献只证明某作者/实验报告了一个结论；语义范围、假设和测量误差需要保留。对用户设想，应区分可检查的推导正确性和实证前提的支持程度。

与后读 SEAL 的比较必须限制为：单调增加自写测试**本身**不能确保它覆盖真实分布；这不反驳综述中把单调约束与独立审计联合使用的建议。p.17 对无灾难性遗忘、p.55 对能力上限与 critic 的强措辞也不是综述给出的普遍定理。

本文综述引文（例如 CoEvoSkills、MetaTextGrad、DGM、STELLA、EVE-Agent、VASO、MemQ）只是本轮从综述中读到或从参考文献定位的线索，**不代表已全文精读这些原始论文**。文中任何性能数字均属被综述作者转述，本轮不拿它们作为经原文复核的实验事实。
