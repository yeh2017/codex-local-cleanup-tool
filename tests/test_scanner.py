import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from codex_cleanup_tool.scanner import CATEGORY_SPECS, scan_codex_home


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / ".codex"
        self.home.mkdir()
        (self.home / "sessions").mkdir()
        (self.home / "state_5.sqlite").write_bytes(b"")
        (self.home / "installation_id").write_text("test", encoding="utf-8")

    def tearDown(self):
        junction = self.home / "cache"
        if os.name == "nt" and junction.exists() and junction.is_dir():
            try:
                if getattr(junction, "is_junction", lambda: False)():
                    os.rmdir(junction)
            except OSError:
                pass
        self.temp.cleanup()

    def test_scan_counts_only_whitelisted_targets(self):
        (self.home / "sessions" / "2026").mkdir(parents=True)
        (self.home / "sessions" / "2026" / "a.jsonl").write_bytes(b"1234")
        (self.home / "auth.json").write_bytes(b"secret")

        summary = scan_codex_home(self.home)
        sessions = summary.by_key("sessions")

        self.assertEqual(sessions.file_count, 1)
        self.assertEqual(sessions.folder_count, 2)
        self.assertEqual(sessions.total_bytes, 4)
        all_paths = {path.name for item in summary.items for path in item.paths}
        self.assertNotIn("auth.json", all_paths)

    def test_scan_reports_total_codex_home_size_including_protected_files(self):
        (self.home / "sessions" / "a.jsonl").write_bytes(b"1234")
        (self.home / "auth.json").write_bytes(b"protected")

        summary = scan_codex_home(self.home)

        expected = sum(
            path.stat().st_size for path in self.home.rglob("*") if path.is_file()
        )
        self.assertEqual(summary.root_total_bytes, expected)
        self.assertGreater(summary.root_total_bytes, summary.by_key("sessions").total_bytes)

    def test_log_sidecars_are_grouped_without_duplicates(self):
        for name in ("logs_2.sqlite", "logs_2.sqlite-wal", "logs_2.sqlite-shm"):
            (self.home / name).write_bytes(b"xx")

        logs = scan_codex_home(self.home).by_key("logs")

        self.assertEqual(logs.file_count, 3)
        self.assertEqual(logs.total_bytes, 6)
        self.assertEqual(len(logs.paths), 3)

    def test_missing_category_is_reported_as_empty(self):
        generated = scan_codex_home(self.home).by_key("generated_images")

        self.assertFalse(generated.exists)
        self.assertEqual(generated.file_count, 0)
        self.assertEqual(generated.total_bytes, 0)

    def test_session_index_file_is_counted(self):
        (self.home / "session_index.jsonl").write_bytes(b"index")

        item = scan_codex_home(self.home).by_key("session_index")

        self.assertEqual(item.file_count, 1)
        self.assertEqual(item.folder_count, 0)
        self.assertEqual(item.total_bytes, 5)

    def test_all_expected_categories_are_defined_once(self):
        keys = [spec.key for spec in CATEGORY_SPECS]

        self.assertEqual(
            keys,
            [
                "sessions",
                "archived_sessions",
                "session_index",
                "logs",
                "generated_images",
                "visualizations",
                "cache",
                "temp",
            ],
        )
        self.assertEqual(len(keys), len(set(keys)))

    def test_invalid_codex_home_is_rejected(self):
        invalid = Path(self.temp.name) / "ordinary"
        invalid.mkdir()

        with self.assertRaises(ValueError):
            scan_codex_home(invalid)

    @unittest.skipUnless(os.name == "nt", "Windows 目录联接测试")
    def test_top_level_directory_junction_is_skipped(self):
        protected = self.home / "plugins"
        protected.mkdir()
        (protected / "important.txt").write_bytes(b"do-not-scan")
        junction = self.home / "cache"
        result = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", str(junction), str(protected)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        item = scan_codex_home(self.home).by_key("cache")

        self.assertFalse(item.exists)
        self.assertEqual(item.total_bytes, 0)

    @unittest.skipUnless(os.name == "nt", "Windows 目录联接测试")
    def test_nested_directory_junction_is_not_traversed(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "private.txt").write_bytes(b"outside-data")
        junction = self.home / "sessions" / "linked-outside"
        result = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", str(junction), str(outside)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        item = scan_codex_home(self.home).by_key("sessions")

        self.assertEqual(item.file_count, 0)
        self.assertEqual(item.total_bytes, 0)


if __name__ == "__main__":
    unittest.main()
