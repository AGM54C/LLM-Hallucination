# DISCERN

[返回数据目录](../README.md)

**类别：** 科学数据与分析诊断　｜　**取得状态：** 公开文件

## 下载地址

下列为任务总表和单轨清单，不能替代完整输入。任务输入与结果在 tracks/；完整运行前按 EXTERNAL_RUNTIME.md 另取 CADD、ESM 等依赖。下载命令只取发布仓库，不会代为运行付费模型。

- [results/world_registry.csv](https://huggingface.co/datasets/discern-bench-anon/discern-benchmark/resolve/main/results/world_registry.csv?download=true)
- [tracks/bulk_rnaseq/L1/results/bulkrna_l1_run/manifest.json](https://huggingface.co/datasets/discern-bench-anon/discern-benchmark/resolve/main/tracks/bulk_rnaseq/L1/results/bulkrna_l1_run/manifest.json?download=true)
- [完整文件目录](https://huggingface.co/datasets/discern-bench-anon/discern-benchmark/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download discern-bench-anon/discern-benchmark --repo-type dataset --local-dir downloads/DISCERN
```

## 数据内容与用途

- **特征与规模：** 论文报告 79 个数据预处理任务、102 个分析核验任务和 22 个假设档案。
- **过程或标签：** 干净对照、受控数据缺陷、分析混杂与对抗审阅；三层分别评价。
- **课题用途：** 3.1.2、4.1.3：定位数据、分析和假设层面的错误并分别验收。
- **局限性：** 三个层次不是一条已验证的端到端修复链；发现错误不能直接记为修复完成。

## 来源与核验

- **数据核验：** 既有全文记录已核设计；2026-10-09 核到匿名官方发布仓库、任务总表和分轨文件目录，未全量审计输入或重跑评价。
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 a7bf6c225d6a2ccf7cc02403484ddfc817d5e75c。
- **许可与来源：** DISCERN 自有代码和文档 MIT；底层数据逐项见官方 DATA_SOURCES_AND_LICENSES.md 与 THIRD_PARTY_NOTICES.md；2026-10-09。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/discern-bench-anon/discern-benchmark)。
