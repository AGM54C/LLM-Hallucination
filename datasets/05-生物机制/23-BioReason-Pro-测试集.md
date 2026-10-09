# BioReason-Pro 测试集

[返回数据目录](../README.md)

**类别：** 蛋白功能　｜　**取得状态：** 公开文件

## 下载地址

可按文件下载；下方命令可下载完整数据仓库。

- [data/test-00000-of-00001.parquet](https://huggingface.co/datasets/wanglab/bioreason-pro-test-data/resolve/main/data/test-00000-of-00001.parquet?download=true)
- [完整文件目录](https://huggingface.co/datasets/wanglab/bioreason-pro-test-data/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download wanglab/bioreason-pro-test-data --repo-type dataset --local-dir downloads/BioReason-Pro-测试集
```

## 数据内容与用途

- **特征与规模：** README 8,630 test。
- **过程或标签：** 蛋白功能评价标签及相关信息。
- **课题用途：** 3.1.3 功能结论与证据的外部评价候选。 独立蛋白任务评价候选。
- **局限性：** 不能只凭官方 split 推断与其他训练来源无交叉；字段与评分需再核。

## 来源与核验

- **数据核验：** 已核官方入口；未逐行核验
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 a18315a77d27dd4fe5a28b9b757695cff4ba4e3f。
- **许可与来源：** 数据卡 Apache-2.0（2026-10-09）；底层蛋白与数据库来源条款另核。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/wanglab/bioreason-pro-test-data)。
