# 化学数据准备

这里保留当前实验必需的数据与来源核对材料，位于 `sources/chemistry`。

- `buchwald_hartwig_annotated.csv`：3,955 个实测条件，回接名称、孔位与来源行；当前配置直接读取它。
- `Dreher_and_Doyle_input_data.xlsx`、`doyle_CN_raw.csv`：两种公开整理版本，来自同一实验。
- `audit_buchwald.py`、`verify_lab_crosswalk_and_interactions.py`：工作簿与条件回接审计；对应 JSON 保存已完成的核对结果。

来源：[Ahneman et al., Science 2018](https://doi.org/10.1126/science.aar5169)、[rxn_yields](https://github.com/rxn4chemistry/rxn_yields)、[Doyle 实验室 CN 数据](https://github.com/doyle-lab-ucla/ochem-data/tree/main/CN)。Doyle 数据采用 CC BY 4.0，许可原文随文件保留；本项目派生表增加了条件映射和来源标识。

工作簿的 16 张表是同一批记录的重排。数据没有独立重复与测量误差模型，不能将排序比较解释为化学因果机制。更多资源见[数据集清单](../../datasets/数据集清单.xlsx)。
