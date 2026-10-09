# DiscoveryBench

[返回数据目录](../README.md)

**类别：** 科学发现　｜　**取得状态：** 公开文件

## 下载地址

参考答案与一个真实数据表如上。完整数据及元信息在 discoverybench/；真实/合成、开发/测试分别保留，实际运行需下载完整仓库。

- [answer_key/answer_key_real.csv](https://huggingface.co/datasets/allenai/discoverybench/resolve/main/answer_key/answer_key_real.csv?download=true)
- [answer_key/answer_key_synth.csv](https://huggingface.co/datasets/allenai/discoverybench/resolve/main/answer_key/answer_key_synth.csv?download=true)
- [discoverybench/real/test/archaeology/capital.csv](https://huggingface.co/datasets/allenai/discoverybench/resolve/main/discoverybench/real/test/archaeology/capital.csv?download=true)
- [完整文件目录](https://huggingface.co/datasets/allenai/discoverybench/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download allenai/discoverybench --repo-type dataset --local-dir downloads/DiscoveryBench
```

## 数据内容与用途

- **特征与规模：** 论文报告 264 个真实任务、903 个合成任务，提供数据、元信息与发现目标。
- **过程或标签：** 参考假设及条件、变量、关系等评价维度；部分评价使用模型裁判。
- **课题用途：** 3.1.3、方向2适用边界：核对假设条件与数据证据是否一致。
- **局限性：** 匹配参考假设不穷尽正确发现；模型评分不等于科学真值，也不是现实发现成功率。

## 来源与核验

- **数据核验：** 依据既有全文记录核对任务与官方发布地址；未逐行审计。
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 e54ec033049d3a0fd95d3c746919cc8c01c25781。
- **许可与来源：** 2026-10-08 文献记录 R37；arXiv:2407.01725v1；论文说明数据 ODC-BY、代码 Apache-2.0。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/allenai/discoverybench)。
