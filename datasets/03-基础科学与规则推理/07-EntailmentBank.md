# EntailmentBank

[返回数据目录](../README.md)

**类别：** 基础科学　｜　**取得状态：** 公开文件

## 下载地址

已列 task_1 三个划分和事实库；task_2、task_3 在完整目录中，是同一题目的不同输入设置。

- [task_1/train.jsonl](https://raw.githubusercontent.com/allenai/entailment_bank/HEAD/data/public_dataset/entailment_trees_emnlp2021_data_v2/dataset/task_1/train.jsonl)
- [task_1/dev.jsonl](https://raw.githubusercontent.com/allenai/entailment_bank/HEAD/data/public_dataset/entailment_trees_emnlp2021_data_v2/dataset/task_1/dev.jsonl)
- [task_1/test.jsonl](https://raw.githubusercontent.com/allenai/entailment_bank/HEAD/data/public_dataset/entailment_trees_emnlp2021_data_v2/dataset/task_1/test.jsonl)
- [支持事实库](https://raw.githubusercontent.com/allenai/entailment_bank/HEAD/data/public_dataset/entailment_trees_emnlp2021_data_v2/supporting_data/worldtree_corpus_sentences_extended.json)
- [完整数据目录](https://github.com/allenai/entailment_bank/tree/HEAD/data/public_dataset/entailment_trees_emnlp2021_data_v2)

## 数据内容与用途

- **特征与规模：** train/dev/test 为 1,313/187/340；有前提、中间结论与证明树。
- **过程或标签：** 人工自然语言蕴涵树。
- **课题用途：** 3.1.1、3.1.2 前提—中间结论结构。 前提检索、推理图、依赖边诊断。
- **局限性：** 原输入 hypothesis 已含答案；不是科研级任务或形式证明；需核对事实编号对应。

## 来源与核验

- **数据核验：** 已读开发集与多步原始样本
- **下载路径核验：** 2026-10-09：已核对官方文件目录或下载说明。
- **许可与来源：** 2026-09-30；仓库 Apache-2.0；底层题目条款另核。
- **资源来源：** [原始页面或下载说明](https://github.com/allenai/entailment_bank)。
