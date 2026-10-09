# QASC

[返回数据目录](../README.md)

**类别：** 科学问答　｜　**取得状态：** 公开文件

## 下载地址

题目优先用 AI2 官方 HF 文件。17M 句检索语料需另取：原仓库公布的旧地址 http://data.allenai.org/downloads/qasc/qasc_corpus.tar.gz 本次未能连通，HF 下载命令不包含该语料。test 不含答案和事实标注，正式测试遵循官方评测流程。

- [data/train-00000-of-00001.parquet](https://huggingface.co/datasets/allenai/qasc/resolve/main/data/train-00000-of-00001.parquet?download=true)
- [data/validation-00000-of-00001.parquet](https://huggingface.co/datasets/allenai/qasc/resolve/main/data/validation-00000-of-00001.parquet?download=true)
- [data/test-00000-of-00001.parquet](https://huggingface.co/datasets/allenai/qasc/resolve/main/data/test-00000-of-00001.parquet?download=true)
- [完整文件目录](https://huggingface.co/datasets/allenai/qasc/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download allenai/qasc --repo-type dataset --local-dir downloads/QASC
```

## 数据内容与用途

- **特征与规模：** 基础科学多选题、两事实组合与检索语料。
- **过程或标签：** 两条支持事实及组合关系。
- **课题用途：** 3.1.3 短证据组合。 短证据组合基线。
- **局限性：** 链短；不是完整多步科研过程；本次未全量审计。

## 来源与核验

- **数据核验：** 已核官方 README
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 a34ba204eb9a33b919c10cc08f4f1c8dae5ec070。
- **许可与来源：** 2026-09-30；数据 CC BY 4.0；代码 Apache-2.0。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/allenai/qasc)。
