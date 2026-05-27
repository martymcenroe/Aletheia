"""Pad an image to a target canvas, filling the remaining space with a brand color.

Used to prepare store-listing screenshots (Chrome Web Store, AMO) where the
source needs a specific aspect ratio without cropping. The source is scaled
to fit within the target canvas while preserving aspect, then centered on a
solid-color background.

Defaults to CWS dimensions (1280x800) and the Aletheia brand blue (#3B82F6,
from .aletheia-badge.neutral in extensions/chrome/overlay.js).

Usage:
    poetry run python tools/cws_image_pad.py \\
        --input "C:/path/to/source.png" \\
        --output screenshots/cws/cws-image-1-epocha.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image


def pad(input_path: Path, output_path: Path, width: int, height: int, color: str) -> None:
    src = Image.open(input_path)
    src_ratio = src.width / src.height
    target_ratio = width / height

    if src_ratio > target_ratio:
        new_w, new_h = width, int(width / src_ratio)
    else:
        new_h, new_w = height, int(height * src_ratio)

    scaled = src.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), color)
    paste_x = (width - new_w) // 2
    paste_y = (height - new_h) // 2

    mask = scaled if scaled.mode == "RGBA" else None
    canvas.paste(scaled, (paste_x, paste_y), mask)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)

    print(f"Wrote {output_path}")
    print(f"  Canvas:     {width}x{height}")
    print(f"  Source:     {src.width}x{src.height}  ->  scaled to {new_w}x{new_h}")
    print(f"  Padding:    {paste_x}px left/right, {paste_y}px top/bottom")
    print(f"  Background: {color}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", required=True, type=Path, help="Source image path")
    parser.add_argument("--output", required=True, type=Path, help="Output path (parent dirs created if missing)")
    parser.add_argument("--width", type=int, default=1280, help="Target canvas width (default: 1280)")
    parser.add_argument("--height", type=int, default=800, help="Target canvas height (default: 800)")
    parser.add_argument("--color", default="#3B82F6", help="Fill color (default: #3B82F6 Aletheia blue)")
    args = parser.parse_args()

    pad(args.input, args.output, args.width, args.height, args.color)
    return 0


if __name__ == "__main__":
    sys.exit(main())
