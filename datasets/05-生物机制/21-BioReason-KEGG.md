# BioReason KEGG

[返回数据目录](../README.md)

**类别：** 生物通路　｜　**取得状态：** 公开文件

## 下载地址

可按文件下载；下方命令可下载完整数据仓库。

- [data/train-00000-of-00001.parquet](https://huggingface.co/datasets/wanglab/kegg/resolve/main/data/train-00000-of-00001.parquet?download=true)
- [data/val-00000-of-00001.parquet](https://huggingface.co/datasets/wanglab/kegg/resolve/main/data/val-00000-of-00001.parquet?download=true)
- [data/test-00000-of-00001.parquet](https://huggingface.co/datasets/wanglab/kegg/resolve/main/data/test-00000-of-00001.parquet?download=true)
- [完整文件目录](https://huggingface.co/datasets/wanglab/kegg/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download wanglab/kegg --repo-type dataset --local-dir downloads/BioReason-KEGG
```

## 数据内容与用途

- **特征与规模：** train/val/test 为 1,159/144/146；序列、变异、问题与解释。
- **过程或标签：** Claude 3.7 Sonnet 合成的通路解释。
- **课题用途：** 3.1.1、方向2：生物解释与通路对应；非逐步机理金标。 序列到通路的证据推断。
- **局限性：** 规模小；需要领域审核；原发布代码可合并 val/test，实验需自行保持隔离。

## 来源与核验

- **数据核验：** 已解析 146 条测试行并取样
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 9f0ef941a362f0e308e11861ed82c36338e23586。
- **许可与来源：** 2026-09-30；数据卡 Apache-2.0；KEGG 上游条款仍适用。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/wanglab/kegg)。
