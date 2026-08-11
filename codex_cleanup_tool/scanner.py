import os
import stat
from pathlib import Path

from .models import CategorySpec, ScanItem, ScanSummary
from .path_detection import is_codex_home


CATEGORY_SPECS = (
    CategorySpec("sessions", "当前聊天记录", "正在使用的本地任务与聊天记录", ("sessions",)),
    CategorySpec(
        "archived_sessions",
        "归档聊天记录",
        "已归档的本地任务与聊天记录",
        ("archived_sessions",),
    ),
    CategorySpec("session_index", "会话索引", "本地任务索引文件", ("session_index.jsonl",)),
    CategorySpec(
        "logs",
        "日志",
        "Codex 运行日志数据库及其临时旁路文件",
        ("logs_*.sqlite", "logs_*.sqlite-wal", "logs_*.sqlite-shm"),
    ),
    CategorySpec(
        "generated_images",
        "生成图片缓存",
        "Codex 生成图片的本地缓存",
        ("generated_images",),
    ),
    CategorySpec(
        "visualizations",
        "可视化缓存",
        "可视化工具生成的本地内容",
        ("visualizations",),
    ),
    CategorySpec("cache", "普通缓存", "可重新生成的通用缓存", ("cache",)),
    CategorySpec("temp", "临时文件", "Codex 临时工作文件", (".tmp", "tmp")),
)


def _is_link_like(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return path.is_symlink() or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _resolve_targets(root: Path, patterns: tuple[str, ...]) -> tuple[Path, ...]:
    targets: dict[str, Path] = {}
    for pattern in patterns:
        for path in root.glob(pattern):
            if _is_link_like(path):
                continue
            absolute = path.absolute()
            targets[str(absolute).casefold()] = absolute
    return tuple(sorted(targets.values(), key=lambda item: str(item).casefold()))


def _measure_target(path: Path) -> tuple[int, int, int, list[str]]:
    warnings: list[str] = []
    if _is_link_like(path):
        return 0, 0, 0, [f"已跳过符号链接：{path}"]
    if path.is_file():
        try:
            return 1, 0, path.stat().st_size, warnings
        except OSError as exc:
            return 0, 0, 0, [f"无法读取：{path}（{exc}）"]

    file_count = 0
    folder_count = 1 if path.is_dir() else 0
    total_bytes = 0
    pending = [path] if path.is_dir() else []
    while pending:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            warnings.append(f"无法读取目录：{directory}（{exc}）")
            continue
        for entry in entries:
            entry_path = Path(entry.path)
            try:
                if _is_link_like(entry_path):
                    warnings.append(f"已跳过符号链接：{entry_path}")
                elif entry.is_dir(follow_symlinks=False):
                    folder_count += 1
                    pending.append(entry_path)
                elif entry.is_file(follow_symlinks=False):
                    file_count += 1
                    total_bytes += entry.stat(follow_symlinks=False).st_size
            except OSError as exc:
                warnings.append(f"无法读取：{entry_path}（{exc}）")
    return file_count, folder_count, total_bytes, warnings


def scan_codex_home(root: Path) -> ScanSummary:
    root = Path(root).expanduser().resolve()
    if not is_codex_home(root):
        raise ValueError(f"不是有效的 Codex 数据目录：{root}")

    _, _, root_total_bytes, root_warnings = _measure_target(root)
    items: list[ScanItem] = []
    all_warnings: list[str] = list(root_warnings)
    for spec in CATEGORY_SPECS:
        paths = _resolve_targets(root, spec.patterns)
        file_count = folder_count = total_bytes = 0
        warnings: list[str] = []
        for path in paths:
            files, folders, size, target_warnings = _measure_target(path)
            file_count += files
            folder_count += folders
            total_bytes += size
            warnings.extend(target_warnings)
        all_warnings.extend(warnings)
        items.append(
            ScanItem(
                key=spec.key,
                label=spec.label,
                description=spec.description,
                paths=paths,
                file_count=file_count,
                folder_count=folder_count,
                total_bytes=total_bytes,
                warnings=tuple(warnings),
            )
        )
    return ScanSummary(
        root=root,
        items=tuple(items),
        root_total_bytes=root_total_bytes,
        warnings=tuple(all_warnings),
    )
