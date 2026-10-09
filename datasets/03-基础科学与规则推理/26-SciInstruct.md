# SciInstruct

[返回数据目录](../README.md)

**类别：** 跨科学　｜　**取得状态：** 公开文件

## 下载地址

三类数据分别下载。课题优先核查物理化学部分，不能把数学和证明数据都计为科学机理监督。

- [train_en_phy_chem.json](https://huggingface.co/datasets/zd21/SciInstruct/resolve/main/train_en_phy_chem.json?download=true)
- [train_cn_math.json](https://huggingface.co/datasets/zd21/SciInstruct/resolve/main/train_cn_math.json?download=true)
- [train_lean.json](https://huggingface.co/datasets/zd21/SciInstruct/resolve/main/train_lean.json?download=true)
- [完整文件目录](https://huggingface.co/datasets/zd21/SciInstruct/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download zd21/SciInstruct --repo-type dataset --local-dir downloads/SciInstruct
```

## 数据内容与用途

- **特征与规模：** 官方报告 123,869 物理化学、89,934 数学、40,248 形式证明；已解析 5 条。
- **过程或标签：** 模型生成并自我修订的解答。
- **课题用途：** 3.1.1 科学题求解过程辅助语料。 补充科学解题监督。
- **局限性：** 多为考试题，没有独立证据库及逐步专家标签；不同学科应分开。

## 来源与核验

- **数据核验：** 已核少量原始记录
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 098a7e88a9385dd170f78ed9edbce2c1b130cf81。
- **许可与来源：** 2026-09-30；数据卡 CC BY 4.0；代码 THUDM/SciGLM。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/zd21/SciInstruct)。
