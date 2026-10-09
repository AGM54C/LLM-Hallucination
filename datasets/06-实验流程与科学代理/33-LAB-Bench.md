# LAB-Bench（含 ProtocolQA）

[返回数据目录](../README.md)

**类别：** 生物研究与协议修复　｜　**取得状态：** 公开文件

## 下载地址

逐项列出八个子集文件。发布路径名为 train，但这些是基准评测题，不能据此当作训练材料。

- [ProtocolQA/train-00000-of-00001.parquet](https://huggingface.co/datasets/futurehouse/lab-bench/resolve/main/ProtocolQA/train-00000-of-00001.parquet?download=true)
- [CloningScenarios/train-00000-of-00001.parquet](https://huggingface.co/datasets/futurehouse/lab-bench/resolve/main/CloningScenarios/train-00000-of-00001.parquet?download=true)
- [DbQA/train-00000-of-00001.parquet](https://huggingface.co/datasets/futurehouse/lab-bench/resolve/main/DbQA/train-00000-of-00001.parquet?download=true)
- [FigQA/train-00000-of-00001.parquet](https://huggingface.co/datasets/futurehouse/lab-bench/resolve/main/FigQA/train-00000-of-00001.parquet?download=true)
- [LitQA2/train-00000-of-00001.parquet](https://huggingface.co/datasets/futurehouse/lab-bench/resolve/main/LitQA2/train-00000-of-00001.parquet?download=true)
- [SeqQA/train-00000-of-00001.parquet](https://huggingface.co/datasets/futurehouse/lab-bench/resolve/main/SeqQA/train-00000-of-00001.parquet?download=true)
- [SuppQA/train-00000-of-00001.parquet](https://huggingface.co/datasets/futurehouse/lab-bench/resolve/main/SuppQA/train-00000-of-00001.parquet?download=true)
- [TableQA/train-00000-of-00001.parquet](https://huggingface.co/datasets/futurehouse/lab-bench/resolve/main/TableQA/train-00000-of-00001.parquet?download=true)
- [完整文件目录](https://huggingface.co/datasets/futurehouse/lab-bench/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download futurehouse/lab-bench --repo-type dataset --local-dir downloads/LAB-Bench
```

## 数据内容与用途

- **特征与规模：** 论文全套 2,457 题、ProtocolQA 135 题；当前公开数据卡为 1,967 题，其中 ProtocolQA 108 题。
- **过程或标签：** 选择题答案与干扰项；协议子任务由专家注错、核验影响并构造修复题。
- **课题用途：** 4.1.1、4.1.3 协议错误诊断与修复选择。 候选 03：协议错误诊断与修复选择；文献、表格等子任务可作局部评价。
- **局限性：** 公开子集不等于完整评测；选择题可利用排除法，正确选项不证明修复后可实施；train 字段不代表已按来源隔离训练与确认样本。

## 来源与核验

- **数据核验：** 已核原论文方法与官方数据卡；未下载全量题目、未复核逐题标签。
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 5c77cec648430f30611808808861eb86f81d5eaa。
- **许可与来源：** 2026-10-09；数据卡 CC BY-SA 4.0；arXiv:2407.10362v3；本次数据版本 5c77cec648430f30611808808861eb86f81d5eaa。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/futurehouse/lab-bench)。
