# SCIPRM70K / SCI-PRM

[返回数据目录](../README.md)

**类别：** 科学工具过程监督　｜　**取得状态：** 公开文件

## 下载地址

已找到与论文官方 GitHub 同属 InternScience 的数据仓库；原始文件未全量统计。仓库 README 报告 17,818 条轨迹、86,314 个标注步骤，名称中的 70K 不能直接当作轨迹数。

- [train.jsonl](https://huggingface.co/datasets/InternScience/SCIPRM70K/resolve/main/train.jsonl?download=true)
- [test_search.jsonl](https://huggingface.co/datasets/InternScience/SCIPRM70K/resolve/main/test_search.jsonl?download=true)
- [test_tool.jsonl](https://huggingface.co/datasets/InternScience/SCIPRM70K/resolve/main/test_tool.jsonl?download=true)
- [完整文件目录](https://huggingface.co/datasets/InternScience/SCIPRM70K/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download InternScience/SCIPRM70K --repo-type dataset --local-dir downloads/SCIPRM70K
```

## 数据内容与用途

- **特征与规模：** 官方 GitHub 报告 17,818 条工具轨迹、86,314 个标注步骤；HF 发布 train.jsonl、test_search.jsonl、test_tool.jsonl，未独立计数。
- **过程或标签：** 推理与工具执行交织，论文称覆盖工具选择、执行和结果解释的过程标签。
- **课题用途：** 3.1.2、4.1.3：过程检查与奖励的待核候选；不能先当作科学正确性金标。
- **局限性：** 过程标签质量、奖励可靠性和答案泄漏仍需核验；可下载不代表可以直接作为科学正确性金标。

## 来源与核验

- **数据核验：** 2026-10-09 核到论文、官方 GitHub 与同组织 HF 数据文件目录；尚未全量核对记录、标注与验证器。
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 3b706094c0444c45f253495f0d7450dc09985c62。
- **许可与来源：** HF 数据仓库暂无 README 或明确许可（2026-10-09）；数据可下载不等于条款已明确。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/InternScience/SCIPRM70K)。
