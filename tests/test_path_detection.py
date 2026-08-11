import json
import tempfile
import unittest
from pathlib import Path

from codex_cleanup_tool.path_detection import (
    default_backup_root,
    detect_codex_home,
    is_codex_home,
    load_or_migrate_settings,
    load_settings,
    save_settings,
    stable_settings_path,
)


class PathDetectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make_codex_home(self, name: str) -> Path:
        path = self.root / name / ".codex"
        (path / "sessions").mkdir(parents=True)
        (path / "state_5.sqlite").write_bytes(b"")
        (path / "installation_id").write_text("test", encoding="utf-8")
        return path

    def test_environment_path_has_priority(self):
        env_home = self.make_codex_home("env")
        user_home = self.make_codex_home("user")
        saved_home = self.make_codex_home("saved")

        result = detect_codex_home(
            {"CODEX_HOME": str(env_home)}, user_home.parent, saved_home
        )

        self.assertEqual(result, env_home.resolve())

    def test_user_profile_codex_path_is_second_choice(self):
        user_codex = self.make_codex_home("user")
        saved_home = self.make_codex_home("saved")

        result = detect_codex_home({}, user_codex.parent, saved_home)

        self.assertEqual(result, user_codex.resolve())

    def test_saved_path_is_used_when_other_candidates_are_missing(self):
        saved_home = self.make_codex_home("saved")

        result = detect_codex_home({}, self.root / "empty-user", saved_home)

        self.assertEqual(result, saved_home.resolve())

    def test_invalid_saved_path_is_ignored(self):
        result = detect_codex_home({}, self.root / "empty-user", self.root / "missing")

        self.assertIsNone(result)

    def test_single_marker_file_is_not_enough(self):
        candidate = self.root / "candidate"
        candidate.mkdir()
        (candidate / "config.toml").write_text("model = 'test'", encoding="utf-8")

        self.assertFalse(is_codex_home(candidate))

    def test_record_directory_and_identity_file_make_valid_codex_home(self):
        candidate = self.root / ".codex"
        (candidate / "sessions").mkdir(parents=True)
        (candidate / "state_5.sqlite").write_bytes(b"")
        (candidate / "installation_id").write_text("test", encoding="utf-8")

        self.assertTrue(is_codex_home(candidate))

    def test_custom_codex_home_name_is_supported_with_strong_markers(self):
        candidate = self.root / "CodexData"
        (candidate / "sessions").mkdir(parents=True)
        (candidate / "installation_id").write_text("test", encoding="utf-8")
        (candidate / ".codex-global-state.json").write_text("{}", encoding="utf-8")

        self.assertTrue(is_codex_home(candidate))

    def test_codex_like_ordinary_project_is_rejected(self):
        candidate = self.root / "ordinary-project"
        (candidate / "sessions").mkdir(parents=True)
        (candidate / "config.toml").write_text("model = 'test'", encoding="utf-8")

        self.assertFalse(is_codex_home(candidate))

    def test_home_remains_valid_after_record_directories_are_removed(self):
        candidate = self.root / "CodexData"
        candidate.mkdir()
        (candidate / "state_5.sqlite").write_bytes(b"")
        (candidate / "installation_id").write_text("test", encoding="utf-8")

        self.assertTrue(is_codex_home(candidate))

    def test_settings_round_trip(self):
        settings_file = self.root / "settings.json"
        payload = {"last_codex_home": str(self.root / ".codex")}

        save_settings(settings_file, payload)

        self.assertEqual(load_settings(settings_file), payload)
        self.assertEqual(json.loads(settings_file.read_text(encoding="utf-8")), payload)

    def test_invalid_settings_returns_empty_mapping(self):
        settings_file = self.root / "settings.json"
        settings_file.write_text("not-json", encoding="utf-8")

        self.assertEqual(load_settings(settings_file), {})

    def test_stable_settings_and_default_backup_paths(self):
        local = self.root / "LocalAppData"
        home = self.root / "User"

        self.assertEqual(
            stable_settings_path({"LOCALAPPDATA": str(local)}, home),
            local / "CodexLocalCleanupTool" / "settings.json",
        )
        self.assertEqual(
            default_backup_root(home), home / "Documents" / "Codex历史记录备份"
        )

    def test_legacy_settings_are_copied_only_when_stable_settings_are_missing(self):
        legacy = self.root / "legacy.json"
        stable = self.root / "stable" / "settings.json"
        save_settings(legacy, {"last_codex_home": "legacy"})

        self.assertEqual(
            load_or_migrate_settings(stable, legacy),
            {"last_codex_home": "legacy"},
        )
        self.assertEqual(load_settings(stable), {"last_codex_home": "legacy"})
        save_settings(stable, {"last_codex_home": "stable"})
        self.assertEqual(
            load_or_migrate_settings(stable, legacy),
            {"last_codex_home": "stable"},
        )

    def test_settings_can_migrate_from_first_available_legacy_location(self):
        stable = self.root / "new" / "settings.json"
        missing = self.root / "missing.json"
        old_user = self.root / "old-user" / "settings.json"
        save_settings(old_user, {"history_backup_root": "backup"})

        result = load_or_migrate_settings(stable, missing, old_user)

        self.assertEqual(result, {"history_backup_root": "backup"})
        self.assertEqual(load_settings(stable), result)


if __name__ == "__main__":
    unittest.main()
