#!/usr/bin/env python3
"""Generate Chrome Web Store promotional images from a source screenshot.

Usage:
    poetry run python tools/generate_store_images.py <source_image_path>

Outputs (saved to docs/assets/store/):
    - store-screenshot-1280x800.png  (Store Screenshot)
    - promo-small-440x280.png        (Small Promo Tile)
    - promo-marquee-1400x560.png     (Marquee Promo Tile)
"""

import sys
from pathlib import Path

from PIL import Image


BACKGROUND_COLOR = (32, 33, 36)  # #202124 - Dark grey
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "assets" / "store"


def resize_and_pad(img: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """Resize image to fit within target dimensions, padding with background color."""
    # Calculate scaling to fit within target while maintaining aspect ratio
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        # Image is wider - fit to width
        new_width = target_width
        new_height = int(target_width / img_ratio)
    else:
        # Image is taller - fit to height
        new_height = target_height
        new_width = int(target_height * img_ratio)

    # Resize with high quality
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create canvas and paste centered
    canvas = Image.new("RGB", (target_width, target_height), BACKGROUND_COLOR)
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    canvas.paste(resized, (x_offset, y_offset))

    return canvas


def resize_and_crop(img: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """Resize image to cover target dimensions, cropping excess."""
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        # Image is wider - fit to height, crop width
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        # Image is taller - fit to width, crop height
        new_width = target_width
        new_height = int(target_width / img_ratio)

    # Resize with high quality
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Center crop
    x_offset = (new_width - target_width) // 2
    y_offset = (new_height - target_height) // 2
    cropped = resized.crop((x_offset, y_offset, x_offset + target_width, y_offset + target_height))

    return cropped


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: poetry run python tools/generate_store_images.py <source_image_path>")
        return 1

    source_path = Path(sys.argv[1])
    if not source_path.exists():
        print(f"Error: Source image not found: {source_path}")
        return 1

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load source image
    print(f"Loading source image: {source_path}")
    img = Image.open(source_path)

    # Convert to RGB (remove alpha if present)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    print(f"Source dimensions: {img.width}x{img.height}")

    # Generate Store Screenshot (1280x800) - pad to fit
    print("\nGenerating Store Screenshot (1280x800)...")
    screenshot = resize_and_pad(img, 1280, 800)
    screenshot_path = OUTPUT_DIR / "store-screenshot-1280x800.png"
    screenshot.save(screenshot_path, "PNG")
    print(f"  Saved: {screenshot_path}")

    # Generate Small Promo Tile (440x280) - crop to fill
    print("\nGenerating Small Promo Tile (440x280)...")
    small_promo = resize_and_crop(img, 440, 280)
    small_promo_path = OUTPUT_DIR / "promo-small-440x280.png"
    small_promo.save(small_promo_path, "PNG")
    print(f"  Saved: {small_promo_path}")

    # Generate Marquee Promo Tile (1400x560) - crop to fill
    print("\nGenerating Marquee Promo Tile (1400x560)...")
    marquee = resize_and_crop(img, 1400, 560)
    marquee_path = OUTPUT_DIR / "promo-marquee-1400x560.png"
    marquee.save(marquee_path, "PNG")
    print(f"  Saved: {marquee_path}")

    print("\n" + "=" * 50)
    print("Images generated. Ready to drag-and-drop into the Dashboard.")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
