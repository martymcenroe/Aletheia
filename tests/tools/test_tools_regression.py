"""
Tooling Regression Suite (Issue #158).

Ensures critical admin tools in tools/ don't break when shared libraries
or schemas change. Tests import capability and --help invocation for each tool.

Test Targets:
- tools/log_viewer.py (requires boto3)
- tools/smoke_test.py
- tools/data_hygiene.py (requires boto3)
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"


def import_tool_module(tool_path: Path):
    """Import a tool module dynamically without executing main."""
    spec = importlib.util.spec_from_file_location(tool_path.stem, tool_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {tool_path}")
    module = importlib.util.module_from_spec(spec)
    # Don't add to sys.modules to avoid side effects
    spec.loader.exec_module(module)
    return module


def run_tool_help(tool_path: Path) -> subprocess.CompletedProcess:
    """Run a tool with --help and return the result."""
    return subprocess.run(
        [sys.executable, str(tool_path), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )


# =============================================================================
# log_viewer.py Tests
# =============================================================================

# Check if boto3 is available (required by log_viewer.py and data_hygiene.py)
try:
    import boto3  # noqa: F401

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
class TestLogViewer:
    """Regression tests for tools/log_viewer.py."""

    tool_path = TOOLS_DIR / "log_viewer.py"

    def test_log_viewer_import(self):
        """Verify log_viewer.py can be imported without error."""
        assert self.tool_path.exists(), f"Tool not found: {self.tool_path}"
        module = import_tool_module(self.tool_path)
        # Verify expected functions exist
        assert hasattr(module, "main"), "Missing main() function"
        assert hasattr(module, "parse_args"), "Missing parse_args() function"

    def test_log_viewer_help(self):
        """Verify log_viewer.py --help returns exit code 0."""
        result = run_tool_help(self.tool_path)
        assert result.returncode == 0, f"--help failed: {result.stderr}"
        assert "usage:" in result.stdout.lower(), "Missing usage in help output"


# =============================================================================
# smoke_test.py Tests
# =============================================================================


class TestSmokeTest:
    """Regression tests for tools/smoke_test.py."""

    tool_path = TOOLS_DIR / "smoke_test.py"

    def test_smoke_test_import(self):
        """Verify smoke_test.py can be imported without error."""
        assert self.tool_path.exists(), f"Tool not found: {self.tool_path}"
        module = import_tool_module(self.tool_path)
        # Verify expected functions exist
        assert hasattr(module, "main"), "Missing main() function"
        assert hasattr(module, "send_request"), "Missing send_request() function"

    def test_smoke_test_help(self):
        """Verify smoke_test.py --help returns exit code 0."""
        result = run_tool_help(self.tool_path)
        assert result.returncode == 0, f"--help failed: {result.stderr}"
        assert "usage:" in result.stdout.lower(), "Missing usage in help output"


# =============================================================================
# data_hygiene.py Tests
# =============================================================================


@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
class TestDataHygiene:
    """Regression tests for tools/data_hygiene.py."""

    tool_path = TOOLS_DIR / "data_hygiene.py"

    def test_data_hygiene_import(self):
        """Verify data_hygiene.py can be imported without error."""
        assert self.tool_path.exists(), f"Tool not found: {self.tool_path}"
        module = import_tool_module(self.tool_path)
        # Verify expected functions exist
        assert hasattr(module, "main"), "Missing main() function"

    def test_data_hygiene_help(self):
        """Verify data_hygiene.py --help returns exit code 0."""
        result = run_tool_help(self.tool_path)
        assert result.returncode == 0, f"--help failed: {result.stderr}"
        assert "usage:" in result.stdout.lower(), "Missing usage in help output"
