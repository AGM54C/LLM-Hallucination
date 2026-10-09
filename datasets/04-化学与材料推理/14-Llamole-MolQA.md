# Llamole-MolQA

[返回数据目录](../README.md)

**类别：** 分子设计　｜　**取得状态：** 公开文件

## 下载地址

可按文件下载；下方命令可下载完整数据仓库。

- [molqa_train.json](https://huggingface.co/datasets/liuganghuggingface/Llamole-MolQA/resolve/main/molqa_train.json?download=true)
- [molqa_drug.json](https://huggingface.co/datasets/liuganghuggingface/Llamole-MolQA/resolve/main/molqa_drug.json?download=true)
- [molqa_material.json](https://huggingface.co/datasets/liuganghuggingface/Llamole-MolQA/resolve/main/molqa_material.json?download=true)
- [完整文件目录](https://huggingface.co/datasets/liuganghuggingface/Llamole-MolQA/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download liuganghuggingface/Llamole-MolQA --repo-type dataset --local-dir downloads/Llamole-MolQA
```

## 数据内容与用途

- **特征与规模：** 论文约 126K 训练；9,986 药物测试、750 材料测试；含分子、性质、路线。
- **过程或标签：** 搜索反应路线与模型生成的设计解释。
- **课题用途：** 3.1.2、4.1.1 分子约束与路线结构。 受限反应路线组合、结构约束。
- **局限性：** 部分性质是预测标签；材料任务是单体路线；模板可执行不等于真实可合成。

## 来源与核验

- **数据核验：** 已取训练样本；已实数 750 条材料测试
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 d4afbacfa6a2c6371ca32287519b1bba78aea5e0。
- **许可与来源：** 2026-09-30；数据卡 MIT；arXiv:2410.04223。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/liuganghuggingface/Llamole-MolQA)。
