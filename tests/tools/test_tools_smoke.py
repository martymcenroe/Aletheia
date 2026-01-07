"""
Smoke tests for CLI tools.

Ensures tools can be imported and their argument parsers work correctly.
This catches breaking changes to tool interfaces before they reach production.
"""

import subprocess
import sys
from pathlib import Path


# Path to tools directory
TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"


class TestLogViewerSmoke:
    """Smoke tests for log_viewer.py."""

    def test_import(self):
        """Tool can be imported without errors."""
        # Use subprocess to test import in isolation
        result = subprocess.run(
            [sys.executable, "-c", "import sys; sys.path.insert(0, 'tools'); import log_viewer"],
            cwd=TOOLS_DIR.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    def test_help_flag(self):
        """Tool responds to --help flag."""
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "log_viewer.py"), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"--help failed: {result.stderr}"
        assert "Aletheia Log Inspector" in result.stdout

    def test_argparse_options(self):
        """Tool accepts expected arguments."""
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "log_viewer.py"), "--help"],
            capture_output=True,
            text=True,
        )
        # Verify expected options exist
        assert "--tail" in result.stdout
        assert "--full-url" in result.stdout


class TestDataHygieneSmoke:
    """Smoke tests for data_hygiene.py."""

    def test_import(self):
        """Tool can be imported without errors."""
        result = subprocess.run(
            [sys.executable, "-c", "import sys; sys.path.insert(0, 'tools'); import data_hygiene"],
            cwd=TOOLS_DIR.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    def test_help_flag(self):
        """Tool responds to --help flag."""
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "data_hygiene.py"), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"--help failed: {result.stderr}"
        assert "DynamoDB Data Hygiene Tool" in result.stdout

    def test_argparse_options(self):
        """Tool accepts expected arguments."""
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "data_hygiene.py"), "--help"],
            capture_output=True,
            text=True,
        )
        # Verify expected options exist
        assert "--scan" in result.stdout
        assert "--normalize" in result.stdout
        assert "--backfill-ttl" in result.stdout
        assert "--clean-common" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--no-dry-run" in result.stdout

    def test_no_args_shows_help(self):
        """Tool shows help when no arguments provided."""
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "data_hygiene.py")],
            capture_output=True,
            text=True,
        )
        # Should exit with error but show usage
        assert result.returncode == 1
        assert "usage:" in result.stdout or "usage:" in result.stderr
