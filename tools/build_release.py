#!/usr/bin/env python3
"""Build release artifacts for Chrome and Firefox.

Usage:
    poetry run python tools/build_release.py

Outputs:
    dist/aletheia-chrome-v{version}.zip
    dist/aletheia-firefox-v{version}.zip

Ref: docs/1053-store-assets.md
"""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
import sys

# Paths - Updated for separated extension directories (Issue #100)
REPO_ROOT = Path(__file__).parent.parent
CHROME_DIR = REPO_ROOT / "extensions" / "chrome"
FIREFOX_DIR = REPO_ROOT / "extensions" / "firefox"
DIST_DIR = REPO_ROOT / "dist"

# Config
ICON_SIZES = [16, 32, 48, 128]
EXCLUDE_PATTERNS = {".git", "__pycache__", ".DS_Store", ".pyc", "node_modules"}

# Keys that MUST match between Chrome and Firefox manifests
# Note: permissions/host_permissions differ by design (MV3 vs MV2)
# Only check identity/branding keys that should always match
PARITY_KEYS = [
    "name",
    "version",
    "description",
    "icons",
]


def verify_icons(extension_dir: Path, browser: str) -> None:
    """Verify all required icons exist. Raises FileNotFoundError if missing."""
    for size in ICON_SIZES:
        icon = extension_dir / "icons" / f"icon{size}.png"
        if not icon.exists():
            raise FileNotFoundError(
                f"Missing {browser} icon: {icon}. Commit icons before building."
            )
        # Per Gemini review: Check file is not empty placeholder
        if icon.stat().st_size < 100:
            raise ValueError(
                f"Suspicious {browser} icon: {icon} is only {icon.stat().st_size} bytes. "
                "May be empty placeholder."
            )
    print(f"  [OK] {browser}: All {len(ICON_SIZES)} icons present and non-empty")


def load_manifest(path: Path) -> dict:
    """Load and parse a manifest JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def validate_parity() -> None:
    """Ensure manifests are in sync on required keys. Raises ValueError on drift."""
    chrome_path = CHROME_DIR / "manifest.json"
    firefox_path = FIREFOX_DIR / "manifest.json"

    if not chrome_path.exists():
        raise FileNotFoundError(f"Missing: {chrome_path}")
    if not firefox_path.exists():
        raise FileNotFoundError(f"Missing: {firefox_path}")

    chrome = load_manifest(chrome_path)
    firefox = load_manifest(firefox_path)

    drifts = []
    for key in PARITY_KEYS:
        chrome_val = chrome.get(key)
        firefox_val = firefox.get(key)
        if chrome_val != firefox_val:
            drifts.append(
                f"  '{key}':\n"
                f"    Chrome:  {chrome_val}\n"
                f"    Firefox: {firefox_val}"
            )

    if drifts:
        raise ValueError(
            "Manifest parity drift detected:\n" + "\n".join(drifts) +
            "\n\nUpdate both manifests to match on these keys."
        )
    print(f"  [OK] Manifest parity verified ({len(PARITY_KEYS)} keys)")


def should_include(path: Path) -> bool:
    """Filter out excluded patterns."""
    return not any(pattern in path.parts for pattern in EXCLUDE_PATTERNS)


def build_zip(source_dir: Path, output: Path, browser: str) -> None:
    """Create a zip archive from a source directory.

    Args:
        source_dir: Path to extension source directory
        output: Path to output zip file
        browser: Browser name for logging
    """
    file_count = 0
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        for file in source_dir.rglob("*"):
            if not file.is_file():
                continue
            if not should_include(file):
                continue

            relative = file.relative_to(source_dir)
            z.write(file, arcname=str(relative))
            file_count += 1

    print(f"  [OK] {browser}: {output.name} ({file_count} files)")


def main() -> int:
    """CLI entry point. Returns 0 on success, 1 on error."""
    print("=" * 50)
    print("Building Aletheia release artifacts")
    print("=" * 50)
    print()

    try:
        # Step 1: Verify icons exist in both directories
        print("Step 1: Verifying icons...")
        verify_icons(CHROME_DIR, "Chrome")
        verify_icons(FIREFOX_DIR, "Firefox")

        # Step 2: Validate manifest parity
        print("\nStep 2: Validating manifest parity...")
        validate_parity()

        # Step 3: Extract version from Chrome manifest (source of truth)
        print("\nStep 3: Reading version...")
        chrome_manifest = load_manifest(CHROME_DIR / "manifest.json")
        version = chrome_manifest["version"]
        print(f"  [OK] Version: {version}")

        # Step 4: Create dist directory
        print("\nStep 4: Creating dist directory...")
        DIST_DIR.mkdir(exist_ok=True)
        print(f"  [OK] {DIST_DIR}")

        # Step 5: Build Chrome zip
        print("\nStep 5: Building Chrome artifact...")
        chrome_zip = DIST_DIR / f"aletheia-chrome-v{version}.zip"
        build_zip(CHROME_DIR, chrome_zip, "Chrome")

        # Step 6: Build Firefox zip
        print("\nStep 6: Building Firefox artifact...")
        firefox_zip = DIST_DIR / f"aletheia-firefox-v{version}.zip"
        build_zip(FIREFOX_DIR, firefox_zip, "Firefox")

        # Done
        print()
        print("=" * 50)
        print("Build complete!")
        print("=" * 50)
        print(f"  Chrome:  {chrome_zip}")
        print(f"  Firefox: {firefox_zip}")
        print()
        print("Next steps:")
        print("  1. Unzip and test locally in each browser")
        print("  2. Upload to Chrome Web Store / Firefox Add-ons")
        return 0

    except FileNotFoundError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"\nERROR: Invalid JSON in manifest: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
