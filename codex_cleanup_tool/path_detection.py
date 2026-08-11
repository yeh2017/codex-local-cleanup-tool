import json
from pathlib import Path
from typing import Mapping


IDENTITY_FILE_MARKERS = (
    "state_5.sqlite",
    "installation_id",
    ".codex-global-state.json",
)


def is_codex_home(path: Path) -> bool:
    try:
        candidate = Path(path).expanduser()
        marker_count = sum(
            (candidate / marker).is_file() for marker in IDENTITY_FILE_MARKERS
        )
        return candidate.is_dir() and marker_count >= 2
    except OSError:
        return False


def detect_codex_home(
    env: Mapping[str, str], user_home: Path, saved_path: Path | str | None
) -> Path | None:
    candidates = (env.get("CODEX_HOME"), Path(user_home) / ".codex", saved_path)
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if is_codex_home(path):
            return path.resolve()
    return None


def load_settings(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(path: Path, settings: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(target)


def stable_settings_path(env: Mapping[str, str], user_home: Path) -> Path:
    local = Path(env.get("LOCALAPPDATA") or Path(user_home) / "AppData" / "Local")
    return local / "CodexLocalCleanupTool" / "settings.json"


def default_backup_root(user_home: Path) -> Path:
    return Path(user_home) / "Documents" / "Codex历史记录备份"


def load_or_migrate_settings(stable_path: Path, *legacy_paths: Path) -> dict:
    stable = load_settings(stable_path)
    if Path(stable_path).is_file():
        return stable
    for legacy_path in legacy_paths:
        legacy = load_settings(legacy_path)
        if legacy:
            save_settings(stable_path, legacy)
            return legacy
    return {}
