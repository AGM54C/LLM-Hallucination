# 实验

当前对象是 **Qwen3-14B 与一次普通 LoRA 微调模型**。数据来自同一个 Buchwald–Hartwig 实验来源；V3–V5 使用 330 个验证任务、4 个添加剂组、11 张条件表。

## 每一轮回答什么

| 轮次 | 问题 | 已有结果 | 入口 |
|---|---|---|---|
| V1 | 高分歧选样是否优于普通训练？ | 当前五臂实验不支持；选样还存在覆盖与难度差异。 | [结果](results/v1/结果分析.md) |
| V2 | 换序主要改变了什么？ | 保持目标记录相邻时较稳；完全打散后明显下降。 | [结果](results/v2/结果分析.md) |
| V3 | 显式读值后比较能否修复？ | 修复了大量直接决策错误，但仍有读对选错。 | [结果](results/v3/结果分析.md) |
| V4 | 残余错误能否由输出顺序或固定标签解释？ | 呈现敏感真实存在；一个简单规则无法覆盖全部错误。 | [结果](results/v4/结果分析.md) |
| V5 | 同样的四个数，去掉表格是否更好？ | 没有；仅数字条件准确率更低、平均损失更高。 | [结果](results/v5/结果分析.md) |

这些是开发实验。旧测试集已参与方向选择，之后的方法确认需要新的独立数据。当前没有验证新内部机制，也没有验证新的训练方法优于强基线。

## 文件怎么用

- [scientific-evidence-learning](scientific-evidence-learning/README.md)：V1–V5 实验实现、配置和测试。
- [化学数据准备](chemical-materials-pilot-20261004/README.md)：运行代码所需的实测数据、来源回接与审计。
- [results](results/)：每轮简明结论、机器可读指标、压缩原始记录；V1 另含训练记录。
- [tools/replay_results.py](tools/replay_results.py)：不依赖服务器绝对路径的 V4/V5 离线重算。

```bash
# 在仓库根目录执行；只需 Python 3.11+ 标准库
python experiments/tools/replay_results.py

# 检查实验代码；缺少 torch 等可选依赖的模型测试会明确跳过
cd experiments/scientific-evidence-learning
python -m unittest discover -s tests
```

原始记录保留提示、响应、评分、协议和运行元数据。压缩包内的 `SHA256.json` 用于检查文件字节；这些哈希检查不能替代评分复算。模型权重与 adapter 未打包。

V1–V5 的实验实现、配置与原服务器脚本保持原字节。仅迁移了一个测试夹具的位置；历史服务器绝对路径保留在运行元数据中。当前复核没有重新训练或调用模型。
