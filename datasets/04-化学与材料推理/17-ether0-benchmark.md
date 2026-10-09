# ether0-benchmark

[返回数据目录](../README.md)

**类别：** 化学推理　｜　**取得状态：** 公开文件

## 下载地址

可按文件下载；下方命令可下载完整数据仓库。

- [data/test-00000-of-00001.parquet](https://huggingface.co/datasets/futurehouse/ether0-benchmark/resolve/main/data/test-00000-of-00001.parquet?download=true)
- [完整文件目录](https://huggingface.co/datasets/futurehouse/ether0-benchmark/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download futurehouse/ether0-benchmark --repo-type dataset --local-dir downloads/ether0-benchmark
```

## 数据内容与用途

- **特征与规模：** 325 条 test，含问题、分子答案和奖励函数编码。
- **过程或标签：** ideal 是答案；solution 是奖励调用字符串。
- **课题用途：** 3.1.2 工具可检查的分子约束。 现成化学评测与奖励工具。
- **局限性：** 没有公开训练 CoT；不能把 solution 字段名理解为推理过程。

## 来源与核验

- **数据核验：** 已读全 325 条
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 c7d5e59960087f360bc32a5006bb994324b38c35。
- **许可与来源：** 2026-09-30；数据 CC BY 4.0；代码 Apache-2.0。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/futurehouse/ether0-benchmark)。
