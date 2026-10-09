# SciMDR-Eval

[返回数据目录](../README.md)

**类别：** 科研文献　｜　**取得状态：** 公开文件

## 下载地址

图像在 images/；只下载 JSONL 不包含配套图像。完整下载命令会一并取得。

- [data/test.jsonl](https://huggingface.co/datasets/scimdr/SciMDR-Eval/resolve/main/data/test.jsonl?download=true)
- [完整文件目录](https://huggingface.co/datasets/scimdr/SciMDR-Eval/tree/main)

批量下载（需已安装 Hugging Face CLI；安装方法见[总目录](../README.md#下载说明)）：

```bash
hf download scimdr/SciMDR-Eval --repo-type dataset --local-dir downloads/SciMDR-Eval
```

## 数据内容与用途

- **特征与规模：** 907 条人工评测；HVI 244 条；评测答案格式与训练不同。
- **过程或标签：** 细节与结论标签，评价涉及关键点覆盖和模型裁判。
- **课题用途：** 3.1.3 科研结论与证据对应。 科研证据推断的外部评价候选。
- **局限性：** 未逐例核对图像与来源；不宜与训练解释链混用；裁判分数非程序真值。

## 来源与核验

- **数据核验：** 已读 3 条评测记录
- **下载路径核验：** 2026-10-09：官方文件目录已核对；数据仓库版本 72ae71a32224008644d8506be64ec5ea23a02ab0。
- **许可与来源：** 2026-09-30；具体数据许可待核；arXiv:2603.12249。
- **资源来源：** [原始页面或下载说明](https://huggingface.co/datasets/scimdr/SciMDR-Eval)。
