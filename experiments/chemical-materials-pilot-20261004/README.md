# 化学数据准备

这里保留已归档化学表格实验必需的数据与来源核对材料，位于 `sources/chemistry`。

- `buchwald_hartwig_annotated.csv`：3,955 个实测条件，回接名称、孔位与来源行；当前配置直接读取它。
- `Dreher_and_Doyle_input_data.xlsx`、`doyle_CN_raw.csv`：两种公开整理版本，来自同一实验。
- `audit_buchwald.py`、`verify_lab_crosswalk_and_interactions.py`：工作簿与条件回接审计；对应 JSON 保存已完成的核对结果。

来源：[Ahneman et al., Science 2018](https://doi.org/10.1126/science.aar5169)、[rxn_yields](https://github.com/rxn4chemistry/rxn_yields)、[Doyle 实验室 CN 数据](https://github.com/doyle-lab-ucla/ochem-data/tree/main/CN)。Doyle 数据采用 CC BY 4.0，许可原文随文件保留；本项目派生表增加了条件映射和来源标识。

工作簿的 16 张表是同一批记录的重排。数据没有独立重复与测量误差模型，不能将排序比较解释为化学因果机制。更多资源见[数据集清单](../../datasets/数据集清单.xlsx)。

## 为什么做这些检查

| 检查 | 要验证什么 | 方法与设计依据 |
|---|---|---|
| 工作簿一致性 | 多张工作表是否真是不同实验，有无缺失或重复条件 | [audit_buchwald.py](sources/chemistry/audit_buchwald.py) 比较逐表记录的多重集合，检查条件重复、笛卡尔网格缺项及数值范围；避免把重排当成独立样本或重复测量。结果见 [workbook_audit.json](sources/chemistry/workbook_audit.json)。 |
| 来源与名称回接 | 整理后的分子、条件、产率能否对应实验室原始行 | [verify_lab_crosswalk_and_interactions.py](sources/chemistry/verify_lab_crosswalk_and_interactions.py) 先用两表中全局唯一的产率建立名称映射，再按四因素条件逐条核对全部 3,955 行；保留原始行和孔位以便追溯。结果见 [lab_crosswalk_audit.json](sources/chemistry/lab_crosswalk_audit.json)。 |
| 条件与实验板关系 | 跨添加剂差异是否还混有实验板差异 | 按添加剂统计实验板覆盖。现有记录中每个具名添加剂只在一块板上，因而不能把跨添加剂差异直接解释成添加剂的独立因果效应。 |

这些是数据身份和适用范围检查，没有算法创新或模型内部机制结论。脚本另可枚举匹配条件下的排序变化；这种有限表格观察仍不等于新化学规律。
