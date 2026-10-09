# ScienceAgentBench

[返回数据目录](../README.md)

**类别：** 计算实验　｜　**取得状态：** 输入公开；完整包受限

## 下载地址

优先使用官方 2026-04-30 更新的 verified 划分，并配套 benchmark_verified.zip。HF 只提供输入注释；完整数据、参考程序和评测材料在下方外部包，解压密码为官方公开的 scienceagentbench。外部包本次请求返回 401，需在浏览器确认访问权限。

- [data/verified-00000-of-00001.parquet](https://huggingface.co/datasets/osunlp/ScienceAgentBench/resolve/main/data/verified-00000-of-00001.parquet?download=true)
- [ScienceAgentBench.csv](https://huggingface.co/datasets/osunlp/ScienceAgentBench/resolve/main/ScienceAgentBench.csv?download=true)
- [完整评测材料 benchmark_verified.zip（SharePoint）](https://buckeyemailosu-my.sharepoint.com/:u:/g/personal/chen_8336_osu_edu/IQB870QrmuqwS5Ck33cHpJfkAVt3LsMeariREIwP3AT7byA?e=3ckueC)
- [完整文件目录](https://huggingface.co/datasets/osunlp/ScienceAgentBench/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download osunlp/ScienceAgentBench --repo-type dataset --local-dir downloads/ScienceAgentBench
```

## 数据内容与用途

- **特征与规模：** 论文报告从 44 篇论文构造 102 个 Python 科学任务，覆盖四个学科。
- **过程或标签：** 任务说明、科学数据、参考程序与任务验收；不是湿实验执行标签。
- **课题用途：** 4.1.1、4.1.3：分开检查代码执行、科学任务完成和修复后的结果。
- **局限性：** 公开依赖和任务标准限制覆盖；可运行不等于科学语义正确，重试择优需单列。

## 来源与核验

- **数据核验：** 既有全文记录已核任务与评价；本次核到 verified Parquet 和完整材料的官方外部下载入口，未重跑任务。
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 9c6e96c9e74572e979b0930ee735041cef528cb7。
- **许可与来源：** 2026-10-08 文献记录 R36；arXiv:2410.05080v3；各底层数据许可需逐项核对。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/osunlp/ScienceAgentBench)。
