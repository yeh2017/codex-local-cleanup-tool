import base64
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import codex_cleanup_tool.recycle_bin as recycle_bin
from codex_cleanup_tool.recycle_bin import (
    RecycleBinClient,
    SafetyError,
    _windows_recycle_operation,
    build_windows_path_list,
    validate_targets,
)


class RecycleBinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root / ".codex"
        (self.home / "sessions").mkdir(parents=True)
        (self.home / "sessions" / "a.jsonl").write_text("x", encoding="utf-8")
        (self.home / "auth.json").write_text("secret", encoding="utf-8")
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

    def test_rejects_target_outside_codex_home(self):
        outside = self.root / "outside"
        outside.mkdir()

        with self.assertRaises(SafetyError):
            validate_targets(self.home, "sessions", (outside,))

    def test_rejects_protected_path_even_inside_home(self):
        with self.assertRaises(SafetyError):
            validate_targets(self.home, "sessions", (self.home / "auth.json",))

    def test_rejects_path_belonging_to_different_category(self):
        (self.home / "cache").mkdir()

        with self.assertRaises(SafetyError):
            validate_targets(self.home, "sessions", (self.home / "cache",))

    def test_accepts_exact_whitelist_target(self):
        result = validate_targets(
            self.home, "sessions", (self.home / "sessions",)
        )

        self.assertEqual(result, ((self.home / "sessions").resolve(),))

    def test_path_list_is_double_null_terminated(self):
        payload = build_windows_path_list((Path(r"C:\temp\a"), Path(r"C:\temp\b")))

        self.assertEqual(payload, "C:\\temp\\a\0C:\\temp\\b\0\0")

    def test_empty_recycle_request_is_rejected(self):
        client = RecycleBinClient(operation=lambda _paths: (0, False))

        with self.assertRaises(ValueError):
            client.recycle(())

    def test_successful_operation_reports_all_paths(self):
        called = []

        def fake_operation(paths):
            called.append(paths)
            return 0, False

        paths = (self.home / "sessions",)
        result = RecycleBinClient(operation=fake_operation).recycle(paths)

        self.assertEqual(called, [paths])
        self.assertEqual(result.succeeded, paths)
        self.assertEqual(result.failed, ())
        self.assertFalse(result.aborted)

    def test_nonzero_shell_result_is_reported_as_failure(self):
        paths = (self.home / "sessions",)
        result = RecycleBinClient(operation=lambda _paths: (5, False)).recycle(paths)

        self.assertEqual(result.succeeded, ())
        self.assertEqual(result.failed[0][0], paths[0])
        self.assertIn("5", result.failed[0][1])

    def test_each_target_is_reported_independently(self):
        first = self.home / "sessions"
        second = self.home / "archived_sessions"
        second.mkdir()
        calls = []

        def partly_failing_operation(paths):
            calls.append(paths)
            return (0, False) if paths == (first,) else (5, False)

        result = RecycleBinClient(operation=partly_failing_operation).recycle(
            (first, second)
        )

        self.assertEqual(calls, [(first,), (second,)])
        self.assertEqual(result.succeeded, (first,))
        self.assertEqual(result.failed[0][0], second)

    @unittest.skipUnless(os.name == "nt", "Windows 目录联接测试")
    def test_rejects_directory_junction_to_protected_content(self):
        protected = self.home / "plugins"
        protected.mkdir()
        junction = self.home / "cache"
        result = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", str(junction), str(protected)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        with self.assertRaises(SafetyError):
            validate_targets(self.home, "cache", (junction,))

    def test_revalidates_codex_identity_before_cleanup(self):
        (self.home / "auth.json").unlink()
        (self.home / "state_5.sqlite").unlink()
        (self.home / "installation_id").unlink()

        with self.assertRaises(SafetyError):
            validate_targets(self.home, "sessions", (self.home / "sessions",))

    def test_default_operation_explicitly_uses_recycle_bin(self):
        script = getattr(recycle_bin, "POWERSHELL_RECYCLE_SCRIPT", "")
        self.assertIn("RecycleOption]::SendToRecycleBin", script)
        self.assertNotIn("DeletePermanently", script)

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell 参数测试")
    def test_target_path_is_encoded_in_environment_not_command_text(self):
        target = Path(r"C:\safe;Write-Output INJECTED;.tmp")
        completed = MagicMock(returncode=0, stdout="", stderr="")

        with patch("codex_cleanup_tool.recycle_bin.subprocess.run", return_value=completed) as run:
            _windows_recycle_operation((target,))

        args = run.call_args.args[0]
        self.assertIn("env", run.call_args.kwargs)
        env = run.call_args.kwargs["env"]
        self.assertNotIn(str(target), args)
        decoded = base64.b64decode(env["CODEX_RECYCLE_TARGET_B64"]).decode("utf-8")
        self.assertEqual(decoded, str(target))


if __name__ == "__main__":
    unittest.main()
