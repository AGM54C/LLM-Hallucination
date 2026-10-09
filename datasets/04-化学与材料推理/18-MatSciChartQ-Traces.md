# MatSciChartQ-Traces

[返回数据目录](../README.md)

**类别：** 材料图表　｜　**取得状态：** 公开文件

## 下载地址

下列是清单和一个图表分区；完整目录包含 12 个图表类型文件。

- [manifest.json](https://huggingface.co/datasets/translorentz/matsci-visual-reasoning-nc/resolve/main/manifest.json?download=true)
- [questions/aging_matrix_heatmap.parquet](https://huggingface.co/datasets/translorentz/matsci-visual-reasoning-nc/resolve/main/questions/aging_matrix_heatmap.parquet?download=true)
- [完整文件目录](https://huggingface.co/datasets/translorentz/matsci-visual-reasoning-nc/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download translorentz/matsci-visual-reasoning-nc --repo-type dataset --local-dir downloads/MatSciChartQ-Traces
```

## 数据内容与用途

- **特征与规模：** 数据卡 4,037 条、12 类图表；已读取一个 64 条分区。
- **过程或标签：** 确定性模板与绘图数值管线生成过程。
- **课题用途：** 3.1.3 图表证据与数值结论。 图表读取与数值比较。
- **局限性：** 个人发布资源；train 包装不代表独立训练划分；与父基准重合，须按来源和图实例隔离。

## 来源与核验

- **数据核验：** 已核原始分区
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 dc8f3433756389b2b2cddb4541f79fc5d030ad85。
- **许可与来源：** 2026-09-30；CC BY-NC 4.0。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/translorentz/matsci-visual-reasoning-nc)。
