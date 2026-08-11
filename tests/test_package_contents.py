import subprocess
import unittest
from pathlib import Path


class PackageContentsTests(unittest.TestCase):
    def test_build_script_creates_windowed_onedir_application(self):
        project_root = Path(__file__).resolve().parents[1]
        script = (project_root / "build_cleanup_package.ps1").read_text(
            encoding="utf-8-sig"
        )

        self.assertIn("PyInstaller", script)
        self.assertIn("--onedir", script)
        self.assertIn("--windowed", script)
        self.assertIn("--icon", script)
        self.assertIn("Codex 本地记录清理工具", script)
        self.assertIn("codex_local_cleanup_tool_windows_x64", script)
        self.assertLess(
            script.index("Remove-Item -LiteralPath $zipPath"),
            script.index("-m PyInstaller"),
        )

    def test_built_package_is_independent_folder(self):
        project_root = Path(__file__).resolve().parents[1]
        package_root = (
            project_root.parent / "outputs" / "codex_local_cleanup_tool_windows_x64"
        )

        self.assertTrue((package_root / "Codex 本地记录清理工具.exe").is_file())
        self.assertFalse((package_root / "CodexLocalCleanupTool.exe").exists())
        self.assertTrue((package_root / "_internal").is_dir())
        self.assertTrue((package_root / "diagnose_codex_cleanup_tool.bat").is_file())
        self.assertFalse(any(package_root.rglob("*.py")))
        self.assertFalse(any(package_root.rglob("*.pyc")))
        self.assertFalse((package_root / "start_codex_cleanup_tool.vbs").exists())
        self.assertFalse(any(package_root.glob("README_*.md")))
        self.assertFalse((package_root / "cleanup_tool_settings.json").exists())

    def test_diagnostic_launcher_uses_bundled_executable(self):
        project_root = Path(__file__).resolve().parents[1]
        launcher = (project_root / "diagnose_codex_cleanup_tool.bat").read_text(
            encoding="utf-8-sig"
        )

        self.assertIn("chcp 65001", launcher)
        self.assertIn("Codex 本地记录清理工具.exe", launcher)
        self.assertIn("--startup-check", launcher)
        self.assertIn("startup.log", launcher)
        self.assertIn("pause", launcher.lower())
        self.assertNotIn("python", launcher.lower())

    def test_launcher_uses_windows_crlf_line_endings(self):
        project_root = Path(__file__).resolve().parents[1]
        launcher = (project_root / "diagnose_codex_cleanup_tool.bat").read_bytes()

        self.assertIn(b"\r\n", launcher)
        self.assertNotIn(b"\n", launcher.replace(b"\r\n", b""))

    def test_built_executable_passes_startup_check(self):
        project_root = Path(__file__).resolve().parents[1]
        executable = (
            project_root.parent
            / "outputs"
            / "codex_local_cleanup_tool_windows_x64"
            / "Codex 本地记录清理工具.exe"
        )

        result = subprocess.run(
            [str(executable), "--startup-check"],
            cwd=executable.parent,
            timeout=30,
            check=False,
        )

        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
