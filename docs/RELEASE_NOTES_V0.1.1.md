# VoC Insight v0.1.1

这是一个 Windows 启动兼容性修复版本。

## 修复内容

- 修复无控制台模式下 Uvicorn 默认日志格式化器访问 `sys.stderr.isatty()` 导致 EXE 启动崩溃的问题；
- 打包版关闭 Uvicorn 控制台日志配置和访问日志；
- 增加 `%LOCALAPPDATA%\VoCInsight\voc-insight.log` 文件日志，便于排查后续启动问题；
- 已使用真正的桌面托盘模式启动产物，并验证内置前端与健康检查接口可访问。

## 使用方式

1. 下载 `VoC-Insight-Windows-x64.exe`；
2. 双击运行，应用自动在默认浏览器打开；
3. 使用系统托盘中的 VoC Insight 图标重新打开或退出应用。

业务数据仍保存在 `%LOCALAPPDATA%\VoCInsight\voc.db`，升级 EXE 不会覆盖已有数据。

