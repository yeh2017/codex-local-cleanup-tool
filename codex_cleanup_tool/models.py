from dataclasses import dataclass, field
from pathlib import Path


def format_size(size_bytes: int) -> str:
    size = float(max(0, size_bytes))
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    return f"{size_bytes} B"


@dataclass(frozen=True)
class CategorySpec:
    key: str
    label: str
    description: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class ScanItem:
    key: str
    label: str
    description: str
    paths: tuple[Path, ...]
    file_count: int
    folder_count: int
    total_bytes: int
    warnings: tuple[str, ...] = ()

    @property
    def exists(self) -> bool:
        return bool(self.paths)


@dataclass(frozen=True)
class ScanSummary:
    root: Path
    items: tuple[ScanItem, ...]
    root_total_bytes: int = 0
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def by_key(self, key: str) -> ScanItem:
        for item in self.items:
            if item.key == key:
                return item
        raise KeyError(key)


@dataclass(frozen=True)
class RecycleResult:
    succeeded: tuple[Path, ...]
    failed: tuple[tuple[Path, str], ...]
    aborted: bool = False
