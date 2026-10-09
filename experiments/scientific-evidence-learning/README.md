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

| 入口 | 用途 |
|---|---|
| `run.py` | 数据准备、基线、诊断、LoRA 训练、评价 |
| `run_v2.py` | 记录顺序与独立读出控制 |
| `run_v3.py` | 短数字比较、缓存读值比较、同次读值再选择 |
| `run_v4.py` | 四种别名映射 × 两种输出顺序 |
| `run_v5.py` | 固定 V4 读数，比较有无原表上下文 |

使用 `python run_v5.py --help` 等查看参数。各轮源码位于 `src/evidence_lab*`，配置位于 `configs`。

模型运行示例：

```bash
python run.py evaluate --dataset artifacts/dataset-demo \
  --model /your/models/Qwen3-14B --device cuda --thinking-mode off \
  --split validation --limit 12 --out artifacts/evaluate-demo
```

新实验使用新的输出目录。`scripts/run_next_v*.sh` 保留原服务器路径，是历史运行脚本；在其他机器上使用上述 Python 入口并传入本机路径。V5 还依赖完整 V4 输出和对应冻结数据，不能直接拿展示用的小样本运行。

已有结果的便携复核请在仓库根目录执行 `python experiments/tools/replay_results.py`，无需安装模型依赖。
