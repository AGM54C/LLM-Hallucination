# SciRIFF

[返回数据目录](../README.md)

**类别：** 科研文献　｜　**取得状态：** 公开文件

## 下载地址

下列为 4096 上下文版本；8192、16384 版本见完整目录，不应当作额外独立数据。

- [4096/train-00000-of-00001.parquet](https://huggingface.co/datasets/allenai/SciRIFF/resolve/main/4096/train-00000-of-00001.parquet?download=true)
- [4096/validation-00000-of-00001.parquet](https://huggingface.co/datasets/allenai/SciRIFF/resolve/main/4096/validation-00000-of-00001.parquet?download=true)
- [4096/test-00000-of-00001.parquet](https://huggingface.co/datasets/allenai/SciRIFF/resolve/main/4096/test-00000-of-00001.parquet?download=true)
- [完整文件目录](https://huggingface.co/datasets/allenai/SciRIFF/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download allenai/SciRIFF --repo-type dataset --local-dir downloads/SciRIFF
```

## 数据内容与用途

- **特征与规模：** 54 类科学文献任务，约 137K 指令数据。
- **过程或标签：** 证据句、结构化输出等多种监督。
- **课题用途：** 3.1.1 科研文本抽取与结构化任务。 文献任务训练与格式基线。
- **局限性：** 不提供统一逐步推理标签；137K 不能全部计为 CoT。

## 来源与核验

- **数据核验：** 已核官方说明
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 eddf83df1ab4acf1ead5b81898dd4c7e7450050e。
- **许可与来源：** 2026-09-30；不同源任务许可应分别核对。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/allenai/SciRIFF)。
