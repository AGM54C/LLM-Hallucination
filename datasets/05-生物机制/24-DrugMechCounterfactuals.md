# DrugMechCounterfactuals

[返回数据目录](../README.md)

**类别：** 药物机制　｜　**取得状态：** 公开文件

## 下载地址

下列 JSON 是已读样本文件；全量 AddLink、change、delete 和 factuals 在同一目录。部分实验还需要上游 DrugMechDB。

- [Data/Counterfactuals/AddLink_pos_dpi_r1k.json](https://raw.githubusercontent.com/czi-ai/DrugMechCounterfactuals/HEAD/Data/Counterfactuals/AddLink_pos_dpi_r1k.json)
- [完整数据目录](https://github.com/czi-ai/DrugMechCounterfactuals/tree/HEAD/Data/Counterfactuals)
- [仓库 ZIP（含数据与代码）](https://github.com/czi-ai/DrugMechCounterfactuals/archive/HEAD.zip)

## 数据内容与用途

- **特征与规模：** 约 6,000 反事实与 2,000 事实例；已解析 1,000 条 AddLink 样本。
- **过程或标签：** 基于机制图的修改与标签，没有 reasoning 文本。
- **课题用途：** 方向2：指定机制图下的反事实关系推断。 机制边干预、依赖传播。
- **局限性：** 需要从图导出过程；不能当专家 CoT；必须比较符号图执行器。

## 来源与核验

- **数据核验：** 已核原始 JSON 样本
- **下载路径核验：** 2026-10-09：已核对官方文件目录或下载说明。
- **许可与来源：** 2026-09-30；反事实仓库 MIT；上游来源各自许可。
- **资源来源：** [原始页面或下载说明](https://github.com/czi-ai/DrugMechCounterfactuals)。
