#!/usr/bin/env python3
"""
Create trimmed web asset icons from extension icons.

The extension icons have the lambda centered with padding (good for browser toolbars).
Web typography needs icons with no padding so CSS sizing/alignment is straightforward.

This script:
1. Loads extension icons
2. Detects the bounding box of non-transparent pixels
3. Crops to that bounding box (removes padding)
4. Saves trimmed versions to docs/assets/
"""

from pathlib import Path
from PIL import Image


def get_content_bbox(img: Image.Image, alpha_threshold: int = 128) -> tuple[int, int, int, int]:
    """
    Get bounding box of non-transparent content.
    Uses alpha threshold to ignore anti-aliasing pixels.
    Returns (left, top, right, bottom) of the content area.
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Get alpha channel and apply threshold
    alpha = img.split()[3]

    # Find rows and columns with pixels above threshold
    width, height = img.size
    left, top, right, bottom = width, height, 0, 0

    for y in range(height):
        for x in range(width):
            if alpha.getpixel((x, y)) >= alpha_threshold:
                left = min(left, x)
                top = min(top, y)
                right = max(right, x + 1)
                bottom = max(bottom, y + 1)

    if right <= left or bottom <= top:
        # No content found, return full image
        return (0, 0, width, height)

    return (left, top, right, bottom)


def trim_icon(input_path: Path, output_path: Path) -> dict:
    """
    Trim transparent padding from an icon and save.
    Returns info about the operation.
    """
    img = Image.open(input_path)
    original_size = img.size

    # Get content bounding box
    bbox = get_content_bbox(img)

    # Crop to content
    trimmed = img.crop(bbox)

    # Save
    trimmed.save(output_path, 'PNG')

    return {
        'input': input_path.name,
        'output': output_path.name,
        'original_size': original_size,
        'trimmed_size': trimmed.size,
        'bbox': bbox,
        'padding_removed': {
            'left': bbox[0],
            'top': bbox[1],
            'right': original_size[0] - bbox[2],
            'bottom': original_size[1] - bbox[3],
        }
    }


def main():
    # Paths
    project_root = Path(__file__).parent.parent
    extension_dir = project_root / 'extensions' / 'chrome' / 'icons'
    web_assets_dir = project_root / 'docs' / 'assets'

    # Ensure output directory exists
    web_assets_dir.mkdir(parents=True, exist_ok=True)

    # Icons to process
    icons = [
        # (source, destination, description)
        (extension_dir / 'icon128.png', web_assets_dir / 'lambda-web-hero.png', 'Hero wordmark'),
        (extension_dir / 'icon32.png', web_assets_dir / 'lambda-web-32.png', 'Header logo'),
        (extension_dir / 'icon16.png', web_assets_dir / 'lambda-web-16.png', 'Footer logo'),
    ]

    print("Creating trimmed web icons...")
    print("=" * 60)

    for source, dest, description in icons:
        if not source.exists():
            print(f"SKIP: {source.name} not found")
            continue

        info = trim_icon(source, dest)

        print(f"\n{description}:")
        print(f"  Source: {info['input']} ({info['original_size'][0]}x{info['original_size'][1]})")
        print(f"  Output: {info['output']} ({info['trimmed_size'][0]}x{info['trimmed_size'][1]})")
        print(f"  Padding removed: L={info['padding_removed']['left']}, "
              f"T={info['padding_removed']['top']}, "
              f"R={info['padding_removed']['right']}, "
              f"B={info['padding_removed']['bottom']}")

    print("\n" + "=" * 60)
    print("Done! Update docs/index.html to use the new icons:")
    print("  - lambda-web-hero.png (for hero wordmark)")
    print("  - lambda-web-32.png (for header logo)")
    print("  - lambda-web-16.png (for footer logo)")


if __name__ == '__main__':
    main()
