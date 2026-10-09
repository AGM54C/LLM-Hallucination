# SciR

[返回数据目录](../README.md)

**类别：** 形式诊断　｜　**取得状态：** 公开文件

## 下载地址

下列是因果、演绎主任务文件示例；归纳和难度变体见完整目录。数据卡限制为评测用途，不作为训练集。

- [causal/tasks/main/tasks_5n1c_transformed_n200.json](https://huggingface.co/datasets/sci-reason/scir/resolve/main/causal/tasks/main/tasks_5n1c_transformed_n200.json?download=true)
- [deduction/tasks/main/tasks_e4d1_transformed_n200.json](https://huggingface.co/datasets/sci-reason/scir/resolve/main/deduction/tasks/main/tasks_e4d1_transformed_n200.json?download=true)
- [完整文件目录](https://huggingface.co/datasets/sci-reason/scir/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download sci-reason/scir --repo-type dataset --local-dir downloads/SciR
```

## 数据内容与用途

- **特征与规模：** 数据卡给出 1,200 个 main tasks；形式前提、因果图与可接受答案池。
- **过程或标签：** 形式真值，非专家自然语言过程。
- **课题用途：** 方向2：形式前提下的演绎、归纳和因果诊断。 结构化科学推理诊断。
- **局限性：** 明确仅供评测，不是训练集；不能把可下载直接解释为可做 SFT。

## 来源与核验

- **数据核验：** 已核数据卡与论文
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 b8ad4795c8aedc01520f6bad9ba3849e7dce6fc2。
- **许可与来源：** 2026-09-30；CC BY-NC 4.0；arXiv:2606.13020。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/sci-reason/scir)。
