# 配图维护工具

从项目根目录执行。

重新导出指定 Draw.io（原生 mxGraph + 本机 Chrome，输出写入 `配图/图片/`）：

```powershell
python -X utf8 '综述选题-20261010/维护工具/render_figures.py' --figures 1,2,3,4,5,6
```

需 Python、Pillow 和本机 Chrome。渲染临时文件自动清理。修改单图后，合并文件和 Word 中的内嵌图仍需同步。

生图接口启动器复用当前用户 `.codex/config.toml` 的服务商地址和密钥；默认模型为 `gpt-image-2.5-sunburst`、质量为 `high`。密钥不会存入项目。接口连通检查：

```powershell
python -X utf8 '综述选题-20261010/维护工具/run_imagegen.py' --check
```

生成或编辑时可用 `generate` / `edit` 子命令，以及 `--prompt-file`、`--image`、`--out`；精确历史生成提示词保存在 `配图/来源资料/生成提示词/`。
