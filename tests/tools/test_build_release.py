"""
Unit tests for build_release.py tool.

Issue #189: Test zip generation, manifest parity, and icon existence.

Target: tools/build_release.py
"""

import json
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import pytest

from tools.build_release import (
    ICON_SIZES,
    PARITY_KEYS,
    EXCLUDE_PATTERNS,
    verify_icons,
    load_manifest,
    validate_parity,
    should_include,
    build_zip,
    main,
)


class TestVerifyIcons:
    """Tests for verify_icons function - icon existence validation."""

    def test_all_icons_present_passes(self, tmp_path):
        """All required icons present and valid passes verification."""
        icons_dir = tmp_path / "icons"
        icons_dir.mkdir()

        # Create valid icon files (>100 bytes)
        for size in ICON_SIZES:
            icon_file = icons_dir / f"icon{size}.png"
            icon_file.write_bytes(b"x" * 200)  # 200 bytes > 100 minimum

        # Should not raise
        verify_icons(tmp_path, "Test")

    def test_missing_icon_raises_file_not_found(self, tmp_path):
        """Missing icon raises FileNotFoundError."""
        icons_dir = tmp_path / "icons"
        icons_dir.mkdir()

        # Create only some icons (missing icon128.png)
        for size in [16, 32, 48]:
            icon_file = icons_dir / f"icon{size}.png"
            icon_file.write_bytes(b"x" * 200)

        with pytest.raises(FileNotFoundError, match="Missing.*icon"):
            verify_icons(tmp_path, "Test")

    def test_empty_icon_raises_value_error(self, tmp_path):
        """Icon smaller than 100 bytes raises ValueError."""
        icons_dir = tmp_path / "icons"
        icons_dir.mkdir()

        # Create icons, one suspiciously small
        for size in ICON_SIZES:
            icon_file = icons_dir / f"icon{size}.png"
            if size == 128:
                icon_file.write_bytes(b"x" * 50)  # Too small
            else:
                icon_file.write_bytes(b"x" * 200)

        with pytest.raises(ValueError, match="Suspicious.*icon"):
            verify_icons(tmp_path, "Test")

    def test_icon_sizes_constant(self):
        """ICON_SIZES contains expected values."""
        assert ICON_SIZES == [16, 32, 48, 128]


class TestLoadManifest:
    """Tests for load_manifest function - JSON parsing."""

    def test_valid_manifest_loads(self, tmp_path):
        """Valid JSON manifest loads correctly."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {"name": "Test", "version": "1.0.0"}
        manifest_path.write_text(json.dumps(manifest_data))

        result = load_manifest(manifest_path)

        assert result == manifest_data

    def test_invalid_json_raises_error(self, tmp_path):
        """Invalid JSON raises JSONDecodeError."""
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_manifest(manifest_path)


class TestValidateParity:
    """Tests for validate_parity function - manifest synchronization."""

    def test_matching_manifests_pass(self, tmp_path):
        """Manifests with matching parity keys pass validation."""
        chrome_dir = tmp_path / "extensions" / "chrome"
        firefox_dir = tmp_path / "extensions" / "firefox"
        chrome_dir.mkdir(parents=True)
        firefox_dir.mkdir(parents=True)

        shared_values = {
            "name": "Aletheia",
            "version": "1.2.3",
            "description": "Etymology insights",
            "icons": {"16": "icons/icon16.png"},
        }

        # Chrome manifest (MV3 extras)
        chrome_manifest = {**shared_values, "manifest_version": 3}
        (chrome_dir / "manifest.json").write_text(json.dumps(chrome_manifest))

        # Firefox manifest (MV2 extras)
        firefox_manifest = {**shared_values, "manifest_version": 2}
        (firefox_dir / "manifest.json").write_text(json.dumps(firefox_manifest))

        # Patch the module constants to use temp dirs
        with patch("tools.build_release.CHROME_DIR", chrome_dir), \
             patch("tools.build_release.FIREFOX_DIR", firefox_dir):
            # Should not raise
            validate_parity()

    def test_version_drift_raises_error(self, tmp_path):
        """Different versions raises ValueError."""
        chrome_dir = tmp_path / "extensions" / "chrome"
        firefox_dir = tmp_path / "extensions" / "firefox"
        chrome_dir.mkdir(parents=True)
        firefox_dir.mkdir(parents=True)

        # Different versions
        chrome_manifest = {"name": "Aletheia", "version": "1.2.3", "description": "Test", "icons": {}}
        firefox_manifest = {"name": "Aletheia", "version": "1.2.4", "description": "Test", "icons": {}}

        (chrome_dir / "manifest.json").write_text(json.dumps(chrome_manifest))
        (firefox_dir / "manifest.json").write_text(json.dumps(firefox_manifest))

        with patch("tools.build_release.CHROME_DIR", chrome_dir), \
             patch("tools.build_release.FIREFOX_DIR", firefox_dir):
            with pytest.raises(ValueError, match="parity drift"):
                validate_parity()

    def test_name_drift_raises_error(self, tmp_path):
        """Different names raises ValueError."""
        chrome_dir = tmp_path / "extensions" / "chrome"
        firefox_dir = tmp_path / "extensions" / "firefox"
        chrome_dir.mkdir(parents=True)
        firefox_dir.mkdir(parents=True)

        chrome_manifest = {"name": "Aletheia", "version": "1.0.0", "description": "Test", "icons": {}}
        firefox_manifest = {"name": "Aletheia Beta", "version": "1.0.0", "description": "Test", "icons": {}}

        (chrome_dir / "manifest.json").write_text(json.dumps(chrome_manifest))
        (firefox_dir / "manifest.json").write_text(json.dumps(firefox_manifest))

        with patch("tools.build_release.CHROME_DIR", chrome_dir), \
             patch("tools.build_release.FIREFOX_DIR", firefox_dir):
            with pytest.raises(ValueError, match="parity drift"):
                validate_parity()

    def test_missing_chrome_manifest_raises(self, tmp_path):
        """Missing Chrome manifest raises FileNotFoundError."""
        firefox_dir = tmp_path / "extensions" / "firefox"
        firefox_dir.mkdir(parents=True)
        (firefox_dir / "manifest.json").write_text("{}")

        with patch("tools.build_release.CHROME_DIR", tmp_path / "extensions" / "chrome"), \
             patch("tools.build_release.FIREFOX_DIR", firefox_dir):
            with pytest.raises(FileNotFoundError):
                validate_parity()

    def test_parity_keys_constant(self):
        """PARITY_KEYS contains expected identity/branding keys."""
        assert "name" in PARITY_KEYS
        assert "version" in PARITY_KEYS
        assert "description" in PARITY_KEYS
        assert "icons" in PARITY_KEYS


class TestShouldInclude:
    """Tests for should_include function - file filtering."""

    def test_normal_file_included(self):
        """Normal files are included."""
        assert should_include(Path("src/content.js")) is True
        assert should_include(Path("manifest.json")) is True
        assert should_include(Path("icons/icon16.png")) is True

    def test_git_excluded(self):
        """Git directories are excluded."""
        assert should_include(Path(".git/config")) is False
        assert should_include(Path("src/.git/HEAD")) is False

    def test_pycache_excluded(self):
        """Python cache directories are excluded."""
        assert should_include(Path("__pycache__/module.pyc")) is False

    def test_ds_store_excluded(self):
        """macOS .DS_Store files are excluded."""
        assert should_include(Path(".DS_Store")) is False
        assert should_include(Path("icons/.DS_Store")) is False

    def test_node_modules_excluded(self):
        """node_modules directories are excluded."""
        assert should_include(Path("node_modules/package/index.js")) is False

    def test_exclude_patterns_constant(self):
        """EXCLUDE_PATTERNS contains expected patterns."""
        assert ".git" in EXCLUDE_PATTERNS
        assert "__pycache__" in EXCLUDE_PATTERNS
        assert ".DS_Store" in EXCLUDE_PATTERNS
        assert "node_modules" in EXCLUDE_PATTERNS


class TestBuildZip:
    """Tests for build_zip function - zip archive creation."""

    def test_creates_valid_zip(self, tmp_path):
        """Creates a valid zip file with correct contents."""
        source_dir = tmp_path / "extension"
        source_dir.mkdir()

        # Create test files
        (source_dir / "manifest.json").write_text('{"name": "test"}')
        (source_dir / "content.js").write_text("console.log('test');")

        icons_dir = source_dir / "icons"
        icons_dir.mkdir()
        (icons_dir / "icon16.png").write_bytes(b"PNG data")

        output_zip = tmp_path / "output.zip"
        build_zip(source_dir, output_zip, "Test")

        # Verify zip exists and contains expected files
        assert output_zip.exists()
        with ZipFile(output_zip, "r") as z:
            names = z.namelist()
            assert "manifest.json" in names
            assert "content.js" in names
            assert "icons/icon16.png" in names

    def test_excludes_filtered_patterns(self, tmp_path):
        """Excluded patterns are not in the zip."""
        source_dir = tmp_path / "extension"
        source_dir.mkdir()

        # Create files including ones that should be excluded
        (source_dir / "manifest.json").write_text('{"name": "test"}')

        git_dir = source_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")

        cache_dir = source_dir / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "module.pyc").write_bytes(b"bytecode")

        output_zip = tmp_path / "output.zip"
        build_zip(source_dir, output_zip, "Test")

        with ZipFile(output_zip, "r") as z:
            names = z.namelist()
            assert "manifest.json" in names
            assert ".git/config" not in names
            assert "__pycache__/module.pyc" not in names

    def test_preserves_directory_structure(self, tmp_path):
        """Nested directory structure is preserved in zip."""
        source_dir = tmp_path / "extension"
        source_dir.mkdir()

        nested = source_dir / "src" / "utils"
        nested.mkdir(parents=True)
        (nested / "helper.js").write_text("export const helper = () => {};")

        output_zip = tmp_path / "output.zip"
        build_zip(source_dir, output_zip, "Test")

        with ZipFile(output_zip, "r") as z:
            assert "src/utils/helper.js" in z.namelist()


class TestMainCLI:
    """Integration tests for main() CLI entry point."""

    def test_returns_zero_on_success(self, tmp_path):
        """Successful build returns exit code 0."""
        # Set up complete extension structure
        chrome_dir = tmp_path / "extensions" / "chrome"
        firefox_dir = tmp_path / "extensions" / "firefox"
        dist_dir = tmp_path / "dist"

        for ext_dir in [chrome_dir, firefox_dir]:
            ext_dir.mkdir(parents=True)

            # Create manifest
            manifest = {
                "name": "Aletheia",
                "version": "1.0.0",
                "description": "Test",
                "icons": {"16": "icons/icon16.png"},
            }
            (ext_dir / "manifest.json").write_text(json.dumps(manifest))

            # Create icons
            icons_dir = ext_dir / "icons"
            icons_dir.mkdir()
            for size in ICON_SIZES:
                (icons_dir / f"icon{size}.png").write_bytes(b"x" * 200)

        with patch("tools.build_release.CHROME_DIR", chrome_dir), \
             patch("tools.build_release.FIREFOX_DIR", firefox_dir), \
             patch("tools.build_release.DIST_DIR", dist_dir), \
             patch("tools.build_release.run_firefox_lint"):  # Skip lint
            result = main()

        assert result == 0
        assert (dist_dir / "aletheia-chrome-v1.0.0.zip").exists()
        assert (dist_dir / "aletheia-firefox-v1.0.0.zip").exists()

    def test_returns_one_on_missing_icons(self, tmp_path):
        """Missing icons returns exit code 1."""
        chrome_dir = tmp_path / "extensions" / "chrome"
        chrome_dir.mkdir(parents=True)

        # Manifest but no icons
        (chrome_dir / "manifest.json").write_text('{"version": "1.0.0"}')

        with patch("tools.build_release.CHROME_DIR", chrome_dir), \
             patch("tools.build_release.FIREFOX_DIR", tmp_path / "firefox"):
            result = main()

        assert result == 1

    def test_returns_one_on_parity_drift(self, tmp_path):
        """Manifest parity drift returns exit code 1."""
        chrome_dir = tmp_path / "extensions" / "chrome"
        firefox_dir = tmp_path / "extensions" / "firefox"

        for ext_dir in [chrome_dir, firefox_dir]:
            ext_dir.mkdir(parents=True)
            icons_dir = ext_dir / "icons"
            icons_dir.mkdir()
            for size in ICON_SIZES:
                (icons_dir / f"icon{size}.png").write_bytes(b"x" * 200)

        # Different versions = parity drift
        (chrome_dir / "manifest.json").write_text(
            json.dumps({"name": "Aletheia", "version": "1.0.0", "description": "Test", "icons": {}})
        )
        (firefox_dir / "manifest.json").write_text(
            json.dumps({"name": "Aletheia", "version": "2.0.0", "description": "Test", "icons": {}})
        )

        with patch("tools.build_release.CHROME_DIR", chrome_dir), \
             patch("tools.build_release.FIREFOX_DIR", firefox_dir):
            result = main()

        assert result == 1
