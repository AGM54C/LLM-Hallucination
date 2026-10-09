# CrossTrace

[返回数据目录](../README.md)

**类别：** 科研构思　｜　**取得状态：** 公开文件

## 下载地址

all_traces 保留来源信息；另外三个文件提供原始训练、验证和测试划分。balanced 版本含重复，单独比较。

- [data/all_traces.jsonl](https://raw.githubusercontent.com/andrewbouras/crosstrace/HEAD/data/all_traces.jsonl)
- [data/train_ours_only.jsonl](https://raw.githubusercontent.com/andrewbouras/crosstrace/HEAD/data/train_ours_only.jsonl)
- [data/val.jsonl](https://raw.githubusercontent.com/andrewbouras/crosstrace/HEAD/data/val.jsonl)
- [data/test_ours.jsonl](https://raw.githubusercontent.com/andrewbouras/crosstrace/HEAD/data/test_ours.jsonl)
- [完整数据目录](https://github.com/andrewbouras/crosstrace/tree/HEAD/data)

## 数据内容与用途

- **特征与规模：** 1,389 条；train/val/test 为 1,180/102/107；生物医学、AI/ML 与跨领域。
- **过程或标签：** Claude Sonnet 4 从论文重建的 3–6 步过程与假设。
- **课题用途：** 3.1.1 科研推理单元；重建过程不等于真实发现。 来源约束的科学构思与修订。
- **局限性：** 重建已发表成果不是发现未知假设；balanced 4,720 含重复；对话格式省略部分来源字段。

## 来源与核验

- **数据核验：** 已取得完整 val 文件
- **下载路径核验：** 2026-10-09：已核对官方文件目录或下载说明。
- **许可与来源：** 2026-09-30；CC BY 4.0；arXiv:2603.28924。
- **资源来源：** [原始页面或下载说明](https://github.com/andrewbouras/crosstrace)。
