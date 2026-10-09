# ChemCoTDataset

[返回数据目录](../README.md)

**类别：** 化学操作　｜　**取得状态：** 需申请权限

## 下载地址

先在官方数据页登录并申请访问，通过后运行下方命令。文件名已由公开目录核对；未登录请求返回 401，未取得原始记录。下列仅是文件示例，完整任务见目录。

- [chemcotbench-cot/mol_edit/add.json](https://huggingface.co/datasets/IDEA-AI4S/ChemCoTDataset/resolve/main/chemcotbench-cot/mol_edit/add.json?download=true)
- [完整文件目录](https://huggingface.co/datasets/IDEA-AI4S/ChemCoTDataset/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf auth login
hf download IDEA-AI4S/ChemCoTDataset --repo-type dataset --local-dir downloads/ChemCoTDataset
```

## 数据内容与用途

- **特征与规模：** v3 论文报告 22,000 条化学编辑、优化与反应过程。
- **过程或标签：** 化学操作 CoT。
- **课题用途：** 3.1.2 分子操作约束。 专用化学操作链训练候选。
- **局限性：** 不能称为已经可直接训练；需核每个步骤的化学与结构正确性。

## 来源与核验

- **数据核验：** 有访问门槛；未取得原始行
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 d88a8af379ba4a7e79f58c04590ad037e79b06ba。
- **许可与来源：** 2026-09-30；HF 与旧仓库许可标记不同，取包后核；arXiv:2505.21318v3。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/IDEA-AI4S/ChemCoTDataset)。
