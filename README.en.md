# Codex Local Cleanup Tool

An unofficial Windows GUI for inspecting, backing up, restoring, and cleaning local records created by the Codex desktop app. The interface supports Chinese and English.

English | [简体中文](README.md)

> This community project is not affiliated with or supported by OpenAI. Fully exit Codex before modifying local data.

## Download and Start

1. Download `codex_local_cleanup_tool_windows_x64.zip` from [Releases](https://github.com/yeh2017/codex-local-cleanup-tool/releases).
2. Extract the complete folder. Do not copy only the EXE.
3. Run `Codex Local Cleanup Tool.exe`.
4. If startup fails, run `diagnose_codex_cleanup_tool.bat` from the same folder.

The standalone package does not require Python, OpenCV, or other third-party runtimes. Because the EXE is unsigned, Windows SmartScreen may display a warning. Verify the SHA-256 value shown on the Release page before running it.

The executable is named `Codex Local Cleanup Tool.exe` in both Chinese and English interface modes.

## Supported Systems

- Windows 10 64-bit
- Windows 11 64-bit

Windows 32-bit, macOS, and Linux are not supported.

## Main Features

- Scan the total `.codex` size and show storage used by records, logs, and caches.
- List local task history and select individual tasks for backup or deletion.
- Before deleting a task, create a persistent backup and remove its session files, database relationships, local task index entries, and logs with the same task ID.
- Restore session files, database records, relationships, indexes, and related logs from a backup created by the tool.
- Inspect the log database and run a short log-growth check.
- Back up, validate, clean, and compact old logs, with automatic rollback on failure.
- Move allowlisted cache items to the Windows Recycle Bin instead of permanently deleting them.

## Correctly Delete a History Task

1. Fully exit the Codex desktop app and make sure it is no longer using the local databases.
2. Start the tool and verify the `.codex` data folder and task backup folder.
3. Select **Start Scan**, then select the tasks to delete in the history list.
4. Review the task titles, counts, related log rows, and estimated space to be released.
5. Select delete and confirm the operation again.
6. The tool first creates and validates a persistent backup. It then moves session files to the Windows Recycle Bin and removes the matching database relationships, local task index entries, and related logs.
7. Restart Codex and check that the sidebar has updated.

Do not manually delete records from Codex databases, and do not use the Windows Recycle Bin as the only backup.

## Correctly Restore a History Task

1. Fully exit the Codex desktop app.
2. Start the tool and verify that the current `.codex` folder matches the folder associated with the backup.
3. Select **Restore Backup** on the history page.
4. Select a task backup folder created by this tool, not a ZIP or an individual session file.
5. Confirm the restore. The tool validates integrity and conflicts before restoring session files, database records, relationships, indexes, and related logs.
6. Restart Codex and check the restored task.

The tool refuses to overwrite an existing task with the same task ID. Restoring only session files from the Windows Recycle Bin does not reliably restore database relationships, indexes, or related logs; use **Restore Backup** whenever possible.

## Paths and Local Data

The Codex data folder is detected in this order:

1. The `CODEX_HOME` environment variable;
2. `%USERPROFILE%\.codex`;
3. The last folder selected manually.

Settings and startup logs are stored under:

```text
%LOCALAPPDATA%\CodexLocalCleanupTool
```

The default persistent backup folder is:

```text
%USERPROFILE%\Documents\Codex历史记录备份
```

You can change the backup folder in the application. If it is moved or deleted, the tool prompts you to recreate or locate it.

## Safety Boundaries

- Nothing is selected for deletion by default. The tool shows estimated space and asks for confirmation.
- An allowlist limits which categories can be cleaned, and every target path is validated again before execution.
- The tool does not process `auth.json`, `config.toml`, `plugins`, `skills`, `vendor_imports`, or the entire `.codex` root.
- The backup folder must be outside the Codex data folder and cannot be a symbolic link or directory junction.
- Codex must be fully closed before task backup, restore, deletion, or log optimization.
- Backup integrity is validated before restore, and conflicting task IDs are not overwritten.

## Test and Build from Source

The application uses only the Python standard library at runtime. Building the standalone package requires 64-bit Python, PyInstaller, and PowerShell.

```powershell
python -B -m unittest discover -s tests
```

Build the Windows standalone folder and ZIP:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_cleanup_package.ps1
```
