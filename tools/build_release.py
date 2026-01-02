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

# Paths
REPO_ROOT = Path(__file__).parent.parent
EXTENSION_DIR = REPO_ROOT / "extension"
DIST_DIR = REPO_ROOT / "dist"

# Config
ICON_SIZES = [16, 32, 48, 128]
EXCLUDE_PATTERNS = {".git", "__pycache__", ".DS_Store", ".pyc"}

# Keys that MUST match between Chrome and Firefox manifests
PARITY_KEYS = [
    "name",
    "version",
    "description",
    "permissions",
    "host_permissions",
    "icons",
    "action",
]


def verify_icons() -> None:
    """Verify all required icons exist. Raises FileNotFoundError if missing."""
    for size in ICON_SIZES:
        icon = EXTENSION_DIR / "icons" / f"icon{size}.png"
        if not icon.exists():
            raise FileNotFoundError(
                f"Missing: {icon}. Commit icons before building."
            )
    print(f"  [OK] All {len(ICON_SIZES)} icons present")


def load_manifest(path: Path) -> dict:
    """Load and parse a manifest JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def validate_parity() -> None:
    """Ensure manifests are in sync on required keys. Raises ValueError on drift."""
    chrome_path = EXTENSION_DIR / "manifest.json"
    firefox_path = EXTENSION_DIR / "manifest.firefox.json"

    if not chrome_path.exists():
        raise FileNotFoundError(f"Missing: {chrome_path}")
    if not firefox_path.exists():
        raise FileNotFoundError(f"Missing: {firefox_path}")

    chrome = load_manifest(chrome_path)
    firefox = load_manifest(firefox_path)

    for key in PARITY_KEYS:
        chrome_val = chrome.get(key)
        firefox_val = firefox.get(key)
        if chrome_val != firefox_val:
            raise ValueError(
                f"Manifest drift on '{key}':\n"
                f"  Chrome:  {chrome_val}\n"
                f"  Firefox: {firefox_val}\n"
                f"Update both manifests to match."
            )
    print(f"  [OK] Manifest parity verified ({len(PARITY_KEYS)} keys)")


def should_include(path: Path) -> bool:
    """Filter out excluded patterns."""
    return not any(pattern in path.parts for pattern in EXCLUDE_PATTERNS)


def build_zip(output: Path, manifest_src: str) -> None:
    """Create a zip archive with the specified manifest.

    Args:
        output: Path to output zip file
        manifest_src: Which manifest file to include ("manifest.json" or "manifest.firefox.json")
    """
    file_count = 0
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        for file in EXTENSION_DIR.rglob("*"):
            if not file.is_file():
                continue
            if not should_include(file):
                continue

            relative = file.relative_to(EXTENSION_DIR)

            # Skip both manifests - we add the correct one explicitly
            if relative.name in ("manifest.json", "manifest.firefox.json"):
                continue

            z.write(file, arcname=str(relative))
            file_count += 1

        # Add the correct manifest as "manifest.json"
        manifest_path = EXTENSION_DIR / manifest_src
        z.write(manifest_path, arcname="manifest.json")
        file_count += 1

    print(f"  [OK] {output.name} ({file_count} files)")


def main() -> int:
    """CLI entry point. Returns 0 on success, 1 on error."""
    print("Building Aletheia release artifacts...")
    print()

    try:
        # Step 1: Verify icons exist
        print("Step 1: Verifying icons...")
        verify_icons()

        # Step 2: Validate manifest parity
        print("Step 2: Validating manifest parity...")
        validate_parity()

        # Step 3: Extract version
        print("Step 3: Reading version...")
        chrome_manifest = load_manifest(EXTENSION_DIR / "manifest.json")
        version = chrome_manifest["version"]
        print(f"  [OK] Version: {version}")

        # Step 4: Create dist directory
        print("Step 4: Creating dist directory...")
        DIST_DIR.mkdir(exist_ok=True)
        print(f"  [OK] {DIST_DIR}")

        # Step 5: Build Chrome zip
        print("Step 5: Building Chrome artifact...")
        chrome_zip = DIST_DIR / f"aletheia-chrome-v{version}.zip"
        build_zip(chrome_zip, "manifest.json")

        # Step 6: Build Firefox zip
        print("Step 6: Building Firefox artifact...")
        firefox_zip = DIST_DIR / f"aletheia-firefox-v{version}.zip"
        build_zip(firefox_zip, "manifest.firefox.json")

        # Done
        print()
        print("Build complete!")
        print(f"  Chrome:  {chrome_zip}")
        print(f"  Firefox: {firefox_zip}")
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
