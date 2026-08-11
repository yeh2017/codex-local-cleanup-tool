# Codex 本地记录清理工具

一个面向 Windows 10/11 64 位系统的本地 GUI 工具，用于扫描、备份、恢复和清理 Codex 桌面应用的本地记录。界面支持中文和英文。

> 本项目是非官方社区工具，不隶属于或由 OpenAI 提供支持。修改本地数据前请完全退出 Codex。

## 下载与启动

1. 从 [Releases](https://github.com/yeh2017/codex-local-cleanup-tool/releases) 下载 `codex_local_cleanup_tool_windows_x64.zip`。
2. 解压整个文件夹，不要只复制 EXE。
3. 双击 `Codex 本地记录清理工具.exe`。
4. 如果启动失败，运行同目录下的 `diagnose_codex_cleanup_tool.bat` 查看诊断信息。

独立文件夹版不要求安装 Python、OpenCV 或其他第三方运行库。未签名的 EXE 可能触发 Windows SmartScreen，请核对 Release 页面中的 SHA-256 后再运行。

## 主要功能

- 扫描 `.codex` 总占用空间及各类记录、日志和缓存的大小。
- 列出本地历史任务，按任务选择、备份和删除。
- 删除历史任务前创建永久备份，并同步处理会话文件、数据库关系、本地任务索引及相同任务 ID 的关联日志。
- 从工具创建的任务备份中恢复会话文件、数据库记录、关系、索引及关联日志。
- 检查日志数据库状态和短时增长情况。
- 在备份和完整性校验后清理旧日志并压缩数据库；失败时自动恢复。
- 将普通缓存等白名单项目移入 Windows 回收站，不自动永久删除。

## 路径与数据

Codex 数据目录按以下顺序识别：

1. `CODEX_HOME` 环境变量；
2. `%USERPROFILE%\.codex`；
3. 上次手动选择的目录。

程序设置和启动日志保存在：

```text
%LOCALAPPDATA%\CodexLocalCleanupTool
```

默认任务备份目录为：

```text
%USERPROFILE%\Documents\Codex历史记录备份
```

备份目录可以在程序中更改。目录被移动或删除时，程序会提示重新创建或重新选择。

## 安全边界

- 默认不选择任何删除项，执行前显示预计释放空间并要求二次确认。
- 使用白名单限制可清理类别，并在执行前重新验证目标路径。
- 不处理 `auth.json`、`config.toml`、`plugins`、`skills`、`vendor_imports` 或整个 `.codex` 根目录。
- 任务备份目录必须位于 Codex 数据目录之外，且不能是符号链接或目录联接。
- 备份、恢复、删除历史任务及日志优化前必须完全退出 Codex。
- 恢复时校验备份完整性，并在冲突时拒绝覆盖。

## 从源码运行测试

项目运行时只使用 Python 标准库；构建独立包需要 64 位 Python、PyInstaller 和 PowerShell。

```powershell
python -B -m unittest discover -s tests
```

构建 Windows 独立文件夹和 ZIP：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_cleanup_package.ps1
```

## English

Codex Local Cleanup Tool is an unofficial Windows 10/11 x64 GUI for inspecting, backing up, restoring, and cleaning local Codex desktop records. The interface supports Chinese and English. Download the standalone ZIP from [Releases](https://github.com/yeh2017/codex-local-cleanup-tool/releases), extract the complete folder, and run `Codex 本地记录清理工具.exe`.

