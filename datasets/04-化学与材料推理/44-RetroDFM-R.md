# RetroDFM-R 过程语料与推理集

[返回数据目录](../README.md)

**类别：** 逆合成　｜　**取得状态：** 评测文件公开

## 下载地址

官方确认这些是推理/评测文件。冷启动 122,812 条 CoT 训练语料仍未核实公开下载；aug1、aug20 是增强设置，不能算独立数据源。

- [50k/reason_aug1.jsonl](https://huggingface.co/datasets/OpenDFM/retrodfm-R-inference/resolve/main/50k/reason_aug1.jsonl?download=true)
- [50k/reason_aug20.jsonl](https://huggingface.co/datasets/OpenDFM/retrodfm-R-inference/resolve/main/50k/reason_aug20.jsonl?download=true)
- [full/reason.jsonl](https://huggingface.co/datasets/OpenDFM/retrodfm-R-inference/resolve/main/full/reason.jsonl?download=true)
- [完整文件目录](https://huggingface.co/datasets/OpenDFM/retrodfm-R-inference/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download OpenDFM/retrodfm-R-inference --repo-type dataset --local-dir downloads/RetroDFM-R
```

## 数据内容与用途

- **特征与规模：** 论文报告 122,812 条冷启动示范；公开来源、推理集与冷启动 CoT 需区分。
- **过程或标签：** 教师看到真实反应物后生成的解释；冷启动训练文件未在旧核验中取得。
- **课题用途：** 3.1.2、4.1.1：路线结构与操作约束的备选；不能直接列为可训练过程数据。
- **局限性：** 训练路径示例不等于文件已发布；逆合成路线也不等于完整实验操作方案。

## 来源与核验

- **数据核验：** 2026-10-09 核到官方推理集三个 JSONL 路径及仓库说明；尚未核到冷启动 CoT 训练文件，也未全量审计推理集。
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 0a18e7f7d228fc8aef4136387a13acbeb7cce67b。
- **许可与来源：** 官方推理数据仓库未声明明确许可（2026-10-09）；代码许可不能自动套用到数据。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/OpenDFM/retrodfm-R-inference)。
