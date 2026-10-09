# BioReason-Pro 训练集

[返回数据目录](../README.md)

**类别：** 蛋白功能　｜　**取得状态：** 公开文件

## 下载地址

可按文件下载；下方命令可下载完整数据仓库。

- [data/train-00000-of-00003.parquet](https://huggingface.co/datasets/wanglab/bioreason-pro-sft-reasoning-data/resolve/main/data/train-00000-of-00003.parquet?download=true)
- [data/train-00001-of-00003.parquet](https://huggingface.co/datasets/wanglab/bioreason-pro-sft-reasoning-data/resolve/main/data/train-00001-of-00003.parquet?download=true)
- [data/train-00002-of-00003.parquet](https://huggingface.co/datasets/wanglab/bioreason-pro-sft-reasoning-data/resolve/main/data/train-00002-of-00003.parquet?download=true)
- [data/validation-00000-of-00001.parquet](https://huggingface.co/datasets/wanglab/bioreason-pro-sft-reasoning-data/resolve/main/data/validation-00000-of-00001.parquet?download=true)
- [完整文件目录](https://huggingface.co/datasets/wanglab/bioreason-pro-sft-reasoning-data/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download wanglab/bioreason-pro-sft-reasoning-data --repo-type dataset --local-dir downloads/BioReason-Pro-训练集
```

## 数据内容与用途

- **特征与规模：** README 117,002 train、7,365 val；含蛋白功能、GO 与互作信息。
- **过程或标签：** GPT-5 生成的推理轨迹。
- **课题用途：** 3.1.1、3.1.3 蛋白功能解释与多源证据。 蛋白功能解释训练候选。
- **局限性：** 不是专家逐步真值；原作已使用 GO 图模型；需领域审核和去泄漏。

## 来源与核验

- **数据核验：** 已核卡与版本；未取大分片实际行
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 2cab301d674487c4d8536aff4353f2df3c5f8235。
- **许可与来源：** 2026-09-30；数据卡 Apache-2.0；代码 MIT。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/wanglab/bioreason-pro-sft-reasoning-data)。
