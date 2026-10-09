# 化学表格候选 · 归档代码

候选现有版本已停止推进；以下命令用于理解和复核历史实验，不是默认的下一步研究计划。

从实测反应表构造条件选择任务，比较训练、记录顺序、显式读值和上下文控制。先读[实验总览](../README.md)。

## 最小运行

Python 3.11+。以下步骤只用 CPU，不下载模型：

```bash
cd experiments/scientific-evidence-learning
python run.py doctor
python -m unittest discover -s tests
python run.py prepare --config configs/pilot_balanced.json --out artifacts/dataset-demo
python run.py verify --dataset artifacts/dataset-demo
python run.py rules --dataset artifacts/dataset-demo --split validation --out artifacts/rules-demo
```

`balanced_marginals` 数据准备需要 `requirements-design.txt` 中的依赖；模型实验另需 `requirements-models.txt`。检查工具使用 `requirements-dev.txt`。已有环境可直接复用。

## 各入口

| 入口 | 用途 | 为什么做、验证什么 |
|---|---|---|
| `run.py train / evaluate` | 五臂 LoRA 与多呈现评价 | [V1：选样原则是否比普通训练更有效](../results/v1/结果分析.md) |
| `run_v2.py` | 记录顺序与独立读出 | [V2：拆分行序、条件关联与最终选择](../results/v2/结果分析.md) |
| `run_v3.py` | 正确四值比较、缓存比较、同次读值再选择 | [V3：显式中间结果能否修复决策](../results/v3/结果分析.md) |
| `run_v4.py` | 四种别名映射 × 两种输出顺序 | [V4：区分位置、字母与化学身份解释](../results/v4/结果分析.md) |
| `run_v5.py` | 固定 V4 读数，比较有无原表 | [V5：原表上下文是否带来可移除的干扰](../results/v5/结果分析.md) |

使用 `python run_v5.py --help` 等查看参数。各轮源码位于 `src/evidence_lab*`，配置位于 `configs`。

模型运行示例：

```bash
python run.py evaluate --dataset artifacts/dataset-demo \
  --model /your/models/Qwen3-14B --device cuda --thinking-mode off \
  --split validation --limit 12 --out artifacts/evaluate-demo
```

新实验使用新的输出目录。`scripts/run_next_v*.sh` 保留原服务器路径，是历史运行脚本；在其他机器上使用上述 Python 入口并传入本机路径。V5 还依赖完整 V4 输出和对应冻结数据，不能直接拿展示用的小样本运行。

已有结果的便携复核请在仓库根目录执行 `python experiments/tools/replay_results.py`，无需安装模型依赖。

## 辅助入口与结果状态

“有实现”和“有对应实验结果”分开记录。下面的程序基线、盲样与机制开发不能计作 V1–V5 已验证的新贡献。

| 入口 | 为什么做、验证什么 | 方法与设计依据 | 本次公开证据 |
|---|---|---|---|
| `run.py difficulty` | 区分规则分歧与模型自身难度 | 只在合格训练池上计算基座对正确答案的平均 token NLL，用于难例臂及难度分区匹配；不使用验证/测试表现选样。 | 冻结 `selection.json` 和五臂训练输入记录了应用结果，见 [V1](../results/v1/结果分析.md)。 |
| `run.py rules` | 检查标签、评分是否一致，以及指定捷径何时也能答对 | 正确条件规则确定性求最优，另计算跨底物均值、第一/最后底物、全表单条最大值四种规则；后两条不参与选样，避免所有规则都被选样目标覆盖。 | 本次压缩结果包未收录独立规则运行；只能说明已实现，不能据此填写新分数。 |
| `run.py diagnose` | 先检查抄值、条件关联、选择三个接口能否工作 | 三类独立请求，默认 12 个开发样本；指定记录号的读值额外提供定位信息。它是早期诊断入口，V2 扩展了正式控制。 | 小样本运行未单独收录；完整诊断使用 [V2 记录](../results/v2/结果分析.md)。 |
| `run.py blind` | 检查有限查询下，辨认盲样身份是否具有决策难度 | 枚举四个选项的 24 种隐藏映射，在查询预算 0/1/2/3 下比较四种程序策略；相同公开随机源避免暗用隐藏映射选动作。 | 本次包未收录独立运行结果；不是 LLM 成绩。 |
| `run.py blind-evaluate` | 检查模型能否合法查询、利用观测并在预算内选择 | 在相同盲样环境中让模型输出查询或最终选项，记录全过程；只公开历史表和已查询观测。 | 本次包未收录模型盲样结果，不能宣称已验证主动实验能力。 |
| `scripts/audit_training_pool_v3.py` | 检查加强难度和覆盖匹配后，能否仍选出高/低分歧子集 | 以普通臂为固定参照，逐步增加条件表、目标底物、NLL 十分位与均值范围、总 token 约束，再用整数规划寻找分歧上下界。 | 这是训练设计可行性审计；本次包未收录审计数值，没有对应的新训练臂。 |

盲样的四种策略各有作用：随机查询和按固定次序查询提供简单参照；信息增益优先减少身份不确定性；单步贝叶斯风险策略优先改善下一次观测后的决策效用。后两者分别关注“知道更多”和“选得更好”，单步策略不是完整规划最优解。环境返回的是无噪声历史查表值，可能使身份识别很容易，也没有生成新化学实验或解释化学机制。实现见 [blinding.py](src/evidence_lab/blinding.py) 和 [blind_agent.py](src/evidence_lab/blind_agent.py)。

## 内部干预入口：设计意图与边界

`run.py intervene` 是唯一直接修改模型内部状态的开发入口。**本次公开归档没有该入口的运行结果；V2–V5 的读出和提示对照不能替代它。**

它想检查：将原序证据中的某条记录表示搬到逆序提示的对应位置，能否改变答案偏好。做法是在指定模块、记录末尾 token 捕获整个隐藏向量，再替换接收提示的对应向量。供体仅输入证据、不含最后的问题，以减少供体状态对最后提问的依赖；这不能排除向量中携带其他内容。

| 条件 | 为何这样设计 |
|---|---|
| 原序、逆序不干预 | 给出两种呈现本身的参照。 |
| 原位原值替换 `identity` | 检查 hook 操作本身是否改变结果。 |
| 同一记录的供体状态 | 检查搬运该记录末端表示是否影响接收提示的答案偏好。 |
| 等扰动范数控制 `norm_matched_rotation` | 将供体与原状态之差沿向量维度循环平移，保留扰动范数、改变方向；检查效果是否只是相近强度的任意扰动。 |
| 另一记录的供体状态 | 检查是否需要指定记录内容，而非任意一条记录的状态。 |

这里的读出是四个显式 JSON 答案的平均 token NLL，选损失最低者，不是自由生成。它使用常见的激活替换思路，替换整个状态，没有隔离“条件关联”子空间；即使效果为正，也只能作为开发线索，不能单凭此认定独特内部机制。实现见 [mechanism.py](src/evidence_lab/mechanism.py) 和 [interventions.py](src/evidence_lab/interventions.py)。

## 工程检查为什么需要

`doctor` 检查依赖；`prepare` 生成任务、划分和训练输入并冻结来源；`verify` 检查字节和依赖是否与冻结记录一致。各轮脚本的 `smoke / verify` 及单元测试用于发现格式、解析、评分和迁移错误。它们通过说明运行与记录满足对应检查，不能证明假设成立；科学判断以各轮完整对照结果为准。
