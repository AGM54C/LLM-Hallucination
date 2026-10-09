# 数据集与下载目录

**47 项调研记录，按六类逐项列出。** 每项有独立中文说明，包含下载地址、数据特征、用途、局限与许可。

既有 33 项资源、9 项科学评测补充和 5 条历史线索全部保留。训练集、测试集、同源整理表和工具分别注明，数量不代表相互独立的数据源。

“公开文件”表示已核到文件路径；“官方外部下载”表示原作者提供网盘或压缩包；“需申请权限”需要登录授权。**未找到数据包的条目明确留空，不把论文或代码当成数据。**

[Excel 汇总与课题索引](数据集清单.xlsx)可筛选查看；下表可直接打开每项说明和下载地址。

## 按课题选择

| 要核查的问题 | 可先查看 | 仍缺什么 |
|---|---|---|
| 断言、证据与条件是否对齐 | [SciFact](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/30-SciFact.md)、[QASPER](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/31-QASPER.md)、[DISCERN](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/38-DISCERN.md) | 完整适用条件和自然错误标签 |
| 因果方向、条件更新与机制一致性 | [DrugMechCounterfactuals](05-%E7%94%9F%E7%89%A9%E6%9C%BA%E5%88%B6/24-DrugMechCounterfactuals.md)、[SciR](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/13-SciR.md)、[DeReLab](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/37-DeReLab.md) | 真实领域机理与专家裁定 |
| 实验方案是否可实施、修复是否有效 | [BioProt](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/32-BioProt-BioPlanner.md)、[LAB-Bench](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/33-LAB-Bench.md)、[ScienceAgentBench](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/34-ScienceAgentBench.md)、[XRDBench](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/42-XRDBench.md) | 真实资源、资质和风险边界；四级可实施性标签 |

上述用途是候选适配关系，尚未确定研究方向。

## 实测化学与材料（3 项）

| 数据集或资源 | 下载地址 | 取得状态 |
|---|---|---|
| [Buchwald–Hartwig 工作簿](01-%E5%AE%9E%E6%B5%8B%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99/01-Buchwald-Hartwig.md) | [文件下载](https://raw.githubusercontent.com/rxn4chemistry/rxn_yields/HEAD/data/Buchwald-Hartwig/Dreher_and_Doyle_input_data.xlsx) | 公开文件 |
| [Doyle 实验室 CN 整理表](01-%E5%AE%9E%E6%B5%8B%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99/02-Doyle-CN.md) | [文件下载](https://raw.githubusercontent.com/doyle-lab-ucla/ochem-data/HEAD/CN/raw.csv) | 公开文件 |
| [LILA 酸性 OER 薄膜催化剂](01-%E5%AE%9E%E6%B5%8B%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99/03-LILA-OER.md) | [下载目录](https://github.com/fl97inc/lila_oer_manuscript/tree/HEAD/data) | 公开文件 |

## 科研文献与证据（12 项）

| 数据集或资源 | 下载地址 | 取得状态 |
|---|---|---|
| [SciMDR 训练集](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/04-SciMDR-%E8%AE%AD%E7%BB%83%E9%9B%86.md) | [下载目录](https://huggingface.co/datasets/scimdr/SciMDR/tree/main) | 公开文件 |
| [SciMDR-Eval](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/05-SciMDR-Eval.md) | [下载目录](https://huggingface.co/datasets/scimdr/SciMDR-Eval/tree/main) | 公开文件 |
| [CrossTrace](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/06-CrossTrace.md) | [下载目录](https://github.com/andrewbouras/crosstrace/tree/HEAD/data) | 公开文件 |
| [SciRIFF](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/29-SciRIFF.md) | [下载目录](https://huggingface.co/datasets/allenai/SciRIFF/tree/main) | 公开文件 |
| [SciFact](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/30-SciFact.md) | [文件下载](https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz) | 公开文件 |
| [QASPER](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/31-QASPER.md) | [文件下载](https://qasper-dataset.s3.us-west-2.amazonaws.com/qasper-train-dev-v0.3.tgz) | 公开文件 |
| [DiscoveryBench](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/35-DiscoveryBench.md) | [下载目录](https://huggingface.co/datasets/allenai/discoverybench/tree/main) | 公开文件 |
| [DISCERN](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/38-DISCERN.md) | [下载目录](https://huggingface.co/datasets/discern-bench-anon/discern-benchmark/tree/main) | 公开文件 |
| [SciRigor](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/39-SciRigor.md) | 暂无已核实地址 | 未找到数据包 |
| [HalluPeer](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/40-HalluPeer.md) | 暂无已核实地址 | 未找到数据包 |
| [SciRAG-SSLI / DeepEra](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/45-SciRAG-SSLI-DeepEra.md) | 暂无已核实地址 | 未找到数据包 |
| [Sci-MMR](02-%E7%A7%91%E7%A0%94%E6%96%87%E7%8C%AE%E4%B8%8E%E8%AF%81%E6%8D%AE/46-Sci-MMR.md) | 暂无已核实地址 | 未找到数据包 |

## 基础科学与规则推理（10 项）

| 数据集或资源 | 下载地址 | 取得状态 |
|---|---|---|
| [EntailmentBank](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/07-EntailmentBank.md) | [下载目录](https://github.com/allenai/entailment_bank/tree/HEAD/data/public_dataset/entailment_trees_emnlp2021_data_v2) | 公开文件 |
| [WorldTree / ExplanationBank](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/08-WorldTree.md) | [文件下载](https://cognitiveai.org/dist/WorldtreeExplanationCorpusV2.1_Feb2020.zip) | 官方外部下载 |
| [QASC](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/09-QASC.md) | [下载目录](https://huggingface.co/datasets/allenai/qasc/tree/main) | 公开文件 |
| [eQASC](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/10-eQASC.md) | [下载目录](https://drive.google.com/drive/folders/1Mal9Xi4VA8LRCsmQSisF3D0_I_ir_WJm?usp=sharing) | 官方外部下载 |
| [SciR](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/13-SciR.md) | [下载目录](https://huggingface.co/datasets/sci-reason/scir/tree/main) | 公开文件 |
| [SciInstruct](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/26-SciInstruct.md) | [下载目录](https://huggingface.co/datasets/zd21/SciInstruct/tree/main) | 公开文件 |
| [SciReasoner cold-start](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/27-SciReasoner-cold-start.md) | [下载目录](https://huggingface.co/datasets/SciReason/SciLM-CoT_ColdStart/tree/main) | 公开文件 |
| [ScienceQA](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/28-ScienceQA.md) | [文件下载](https://raw.githubusercontent.com/lupantech/ScienceQA/HEAD/data/scienceqa/problems.json) | 公开文件 |
| [DeReLab](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/37-DeReLab.md) | [下载目录](https://github.com/Jayanta47/DeReLab/tree/HEAD/datasets) | 公开文件 |
| [SCIPRM70K / SCI-PRM](03-%E5%9F%BA%E7%A1%80%E7%A7%91%E5%AD%A6%E4%B8%8E%E8%A7%84%E5%88%99%E6%8E%A8%E7%90%86/47-SCIPRM70K.md) | [下载目录](https://huggingface.co/datasets/InternScience/SCIPRM70K/tree/main) | 公开文件 |

## 化学与材料推理（10 项）

| 数据集或资源 | 下载地址 | 取得状态 |
|---|---|---|
| [Llamole-MolQA](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/14-Llamole-MolQA.md) | [下载目录](https://huggingface.co/datasets/liuganghuggingface/Llamole-MolQA/tree/main) | 公开文件 |
| [ChemCoTDataset](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/15-ChemCoTDataset.md) | [申请入口](https://huggingface.co/datasets/IDEA-AI4S/ChemCoTDataset)；[文件目录](https://huggingface.co/datasets/IDEA-AI4S/ChemCoTDataset/tree/main) | 需申请权限 |
| [ChemCoTBench](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/16-ChemCoTBench.md) | [申请入口](https://huggingface.co/datasets/IDEA-AI4S/ChemCoTBench)；[文件目录](https://huggingface.co/datasets/IDEA-AI4S/ChemCoTBench/tree/main) | 需申请权限 |
| [ether0-benchmark](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/17-ether0-benchmark.md) | [下载目录](https://huggingface.co/datasets/futurehouse/ether0-benchmark/tree/main) | 公开文件 |
| [MatSciChartQ-Traces](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/18-MatSciChartQ-Traces.md) | [下载目录](https://huggingface.co/datasets/translorentz/matsci-visual-reasoning-nc/tree/main) | 公开文件 |
| [MatSciBench](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/19-MatSciBench.md) | [下载目录](https://huggingface.co/datasets/JunkaiZ/MatSciBench/tree/main) | 公开文件 |
| [ChemAgent / SciBench 示例](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/20-ChemAgent-SciBench%E7%A4%BA%E4%BE%8B.md) | [下载目录](https://github.com/gersteinlab/ChemAgent/tree/HEAD/dataset) | 公开文件 |
| [XRDBench / AutoXRD](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/42-XRDBench.md) | [下载目录](https://github.com/Stephen-SMJ/XRDBench/tree/HEAD/files) | 公开文件 |
| [ChemDFM-R / ChemFG-Tool](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/43-ChemDFM-R-ChemFG-Tool.md) | [工具文件](https://raw.githubusercontent.com/OpenDFM/ChemFG-Tool/HEAD/functional_group_list.tsv) | 仅核到工具 |
| [RetroDFM-R 过程语料与推理集](04-%E5%8C%96%E5%AD%A6%E4%B8%8E%E6%9D%90%E6%96%99%E6%8E%A8%E7%90%86/44-RetroDFM-R.md) | [下载目录](https://huggingface.co/datasets/OpenDFM/retrodfm-R-inference/tree/main) | 评测文件公开 |

## 生物机制（5 项）

| 数据集或资源 | 下载地址 | 取得状态 |
|---|---|---|
| [BioReason KEGG](05-%E7%94%9F%E7%89%A9%E6%9C%BA%E5%88%B6/21-BioReason-KEGG.md) | [下载目录](https://huggingface.co/datasets/wanglab/kegg/tree/main) | 公开文件 |
| [BioReason-Pro 训练集](05-%E7%94%9F%E7%89%A9%E6%9C%BA%E5%88%B6/22-BioReason-Pro-%E8%AE%AD%E7%BB%83%E9%9B%86.md) | [下载目录](https://huggingface.co/datasets/wanglab/bioreason-pro-sft-reasoning-data/tree/main) | 公开文件 |
| [BioReason-Pro 测试集](05-%E7%94%9F%E7%89%A9%E6%9C%BA%E5%88%B6/23-BioReason-Pro-%E6%B5%8B%E8%AF%95%E9%9B%86.md) | [下载目录](https://huggingface.co/datasets/wanglab/bioreason-pro-test-data/tree/main) | 公开文件 |
| [DrugMechCounterfactuals](05-%E7%94%9F%E7%89%A9%E6%9C%BA%E5%88%B6/24-DrugMechCounterfactuals.md) | [下载目录](https://github.com/czi-ai/DrugMechCounterfactuals/tree/HEAD/Data/Counterfactuals) | 公开文件 |
| [DrugMechDB](05-%E7%94%9F%E7%89%A9%E6%9C%BA%E5%88%B6/25-DrugMechDB.md) | [文件下载](https://raw.githubusercontent.com/SuLab/DrugMechDB/HEAD/indication_paths.yaml) | 公开文件 |

## 实验流程与科学代理（7 项）

| 数据集或资源 | 下载地址 | 取得状态 |
|---|---|---|
| [ScienceWorld](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/11-ScienceWorld.md) | [文件下载](https://raw.githubusercontent.com/allenai/ScienceWorld/HEAD/goldpaths/goldpaths-all.zip) | 公开文件 |
| [DiscoveryWorld](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/12-DiscoveryWorld.md) | [下载目录](https://drive.google.com/drive/folders/14FucVzVCm1HZ0EfPEKoPwdRsFnZi769k?usp=drive_link) | 官方外部下载 |
| [BioProt / BioPlanner](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/32-BioProt-BioPlanner.md) | [下载目录](https://github.com/bioplanner/bioplanner/tree/HEAD/bioprot) | 公开文件 |
| [LAB-Bench（含 ProtocolQA）](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/33-LAB-Bench.md) | [下载目录](https://huggingface.co/datasets/futurehouse/lab-bench/tree/main) | 公开文件 |
| [ScienceAgentBench](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/34-ScienceAgentBench.md) | [下载目录](https://huggingface.co/datasets/osunlp/ScienceAgentBench/tree/main) | 输入公开；完整包受限 |
| [SCHEMA](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/36-SCHEMA.md) | [代码 ZIP](https://github.com/circles-post/SCHEMA/archive/HEAD.zip) | 仅核到代码 |
| [CruxBench](06-%E5%AE%9E%E9%AA%8C%E6%B5%81%E7%A8%8B%E4%B8%8E%E7%A7%91%E5%AD%A6%E4%BB%A3%E7%90%86/41-CruxBench.md) | [下载目录](https://github.com/ai-prophet/cruxbench/tree/HEAD/data) | 公开文件 |

## 下载说明

单文件链接直接指向原始文件；网盘入口按作者说明下载。多个文件的资源同时提供完整目录，示例文件不代表全量数据。

Hugging Face 批量下载命令见对应条目。首次使用安装 CLI：

```bash
python -m pip install -U huggingface_hub
```

本目录维护下载入口，不把大体积原始数据打包上传。路径核对日期为 **2026-10-09**；历史样本核验记录、访问限制与未取得的数据分别写在各条目中。
