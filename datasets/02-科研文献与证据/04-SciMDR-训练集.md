# SciMDR 训练集

[返回数据目录](../README.md)

**类别：** 科研文献　｜　**取得状态：** 公开文件

## 下载地址

图像与原文另在 arxiv/、nature/ 的压缩包中；完整下载命令会一并取得，体积较大。

- [tqa.jsonl](https://huggingface.co/datasets/scimdr/SciMDR/resolve/main/tqa.jsonl?download=true)
- [vqa.jsonl](https://huggingface.co/datasets/scimdr/SciMDR/resolve/main/vqa.jsonl?download=true)
- [mqa.jsonl](https://huggingface.co/datasets/scimdr/SciMDR/resolve/main/mqa.jsonl?download=true)
- [完整文件目录](https://huggingface.co/datasets/scimdr/SciMDR/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download scimdr/SciMDR --repo-type dataset --local-dir downloads/SciMDR-训练集
```

## 数据内容与用途

- **特征与规模：** 论文报告 304,461 条；TQA、VQA、MQA；提供论文来源、问题与分步答案。
- **过程或标签：** GPT-5.1 在已知断言条件下重建的解释链。
- **课题用途：** 3.1.1、3.1.3 科研单元抽取与证据链。 证据定位、条件推断、结构化过程监督。
- **局限性：** 不是逐步专家金标；跨学科混合；须检查输入泄漏及图文是否真正支持结论。

## 来源与核验

- **数据核验：** 已读 TQA/MQA 小样本
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 cf83d685a06ed6a9fda67d7a5b70f4b26a894e1a。
- **许可与来源：** 2026-09-30；数据卡仅写 cc，具体变体待核；arXiv:2603.12249。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/scimdr/SciMDR)。
