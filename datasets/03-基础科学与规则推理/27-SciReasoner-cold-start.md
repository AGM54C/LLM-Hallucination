# SciReasoner cold-start

[返回数据目录](../README.md)

**类别：** 跨科学　｜　**取得状态：** 公开文件

## 下载地址

下列是此前抽样的 BBBP 和蛋白溶解性文件，其余任务见完整目录。

- [prediction-bbbp.json](https://huggingface.co/datasets/SciReason/SciLM-CoT_ColdStart/resolve/main/prediction-bbbp.json?download=true)
- [Solubility.json](https://huggingface.co/datasets/SciReason/SciLM-CoT_ColdStart/resolve/main/Solubility.json?download=true)
- [完整文件目录](https://huggingface.co/datasets/SciReason/SciLM-CoT_ColdStart/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download SciReason/SciLM-CoT_ColdStart --repo-type dataset --local-dir downloads/SciReasoner-cold-start
```

## 数据内容与用途

- **特征与规模：** input、reference、answer、evaluation；已读 BBBP 与蛋白溶解性各 3 条。
- **过程或标签：** 教师模型采样筛选的解释。
- **课题用途：** 3.1.1 合成过程辅助语料。 合成过程质量审计。
- **局限性：** correct=True 不保证每步正确；抽样出现答案语气与标签不完全对应，不能推算全量错误率。

## 来源与核验

- **数据核验：** 已核少量原始记录
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 270aef00a8f138aa6cf3d54f0a998da61b7e92e6。
- **许可与来源：** 2026-09-30；元数据 MIT、正文徽章 Apache-2.0，需澄清。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/SciReason/SciLM-CoT_ColdStart)。
