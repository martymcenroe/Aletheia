#!/usr/bin/env python3
"""Generate Chrome Web Store promotional tiles.

Usage:
    poetry run python tools/generate_promo_tiles.py

Outputs (saved to docs/assets/store/):
    - promo-small-440x280.png   (Small Promo Tile)
    - promo-marquee-1400x560.png (Marquee Promo Tile)

Requirements:
    - Small promo tile: 440x280, PNG/JPEG, no alpha
    - Marquee promo tile: 1400x560, PNG/JPEG, no alpha
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ICON_PATH = PROJECT_ROOT / "extensions" / "chrome" / "icons" / "icon128.png"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "assets" / "store"
SCREENSHOT_PATH = OUTPUT_DIR / "screenshot-2-hover.png"

# Brand colors
BRAND_GREEN = (0, 230, 118)  # #00e676 - vibrant green
BRAND_DARK = (15, 15, 26)    # #0f0f1a - deep navy/black
BRAND_ACCENT = (74, 144, 226) # #4a90e2 - accent blue
WHITE = (255, 255, 255)
GRAY = (160, 160, 180)

# Taglines
TAGLINE_PRIMARY = "AI-Powered Context Analysis"
TAGLINE_SECONDARY = "Understand the words behind the words"


def create_gradient_background(width: int, height: int) -> Image.Image:
    """Create a subtle diagonal gradient background."""
    img = Image.new("RGB", (width, height), BRAND_DARK)
    draw = ImageDraw.Draw(img)

    # Create subtle gradient from dark to slightly lighter
    for y in range(height):
        for x in range(width):
            # Diagonal gradient factor
            factor = (x / width * 0.3 + y / height * 0.7)
            r = int(BRAND_DARK[0] + factor * 20)
            g = int(BRAND_DARK[1] + factor * 20)
            b = int(BRAND_DARK[2] + factor * 35)
            draw.point((x, y), fill=(r, g, b))

    return img


def create_simple_gradient(width: int, height: int) -> Image.Image:
    """Create a simple vertical gradient - faster than pixel-by-pixel."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        factor = y / height
        r = int(BRAND_DARK[0] + factor * 15)
        g = int(BRAND_DARK[1] + factor * 15)
        b = int(BRAND_DARK[2] + factor * 30)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return img


def add_glow(img: Image.Image, center: tuple, radius: int, color: tuple, intensity: float = 0.3) -> Image.Image:
    """Add a subtle glow effect at a position."""
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)

    for r in range(radius, 0, -5):
        alpha = int(255 * intensity * (1 - r / radius) ** 2)
        fill = (*color, alpha)
        draw.ellipse(
            [center[0] - r, center[1] - r, center[0] + r, center[1] + r],
            fill=fill
        )

    # Blur the glow
    glow = glow.filter(ImageFilter.GaussianBlur(radius=radius // 4))

    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, glow)
    return result.convert("RGB")


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a system font, with fallbacks."""
    # Try various system fonts
    font_options = [
        "C:/Windows/Fonts/segoeui.ttf",      # Windows Segoe UI
        "C:/Windows/Fonts/segoeuib.ttf",     # Windows Segoe UI Bold
        "C:/Windows/Fonts/arial.ttf",         # Arial
        "C:/Windows/Fonts/calibri.ttf",       # Calibri
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
    ]

    if bold:
        font_options = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
        ] + font_options

    for font_path in font_options:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue

    # Fallback to default
    return ImageFont.load_default()


def create_small_promo(output_path: Path) -> None:
    """Create 440x280 small promo tile."""
    width, height = 440, 280

    # Create gradient background
    img = create_simple_gradient(width, height)

    # Add subtle green glow behind logo area
    img = add_glow(img, (width // 2, height // 2 - 20), 150, BRAND_GREEN, 0.15)

    # Load and place logo
    logo = Image.open(ICON_PATH).convert("RGBA")
    logo_size = 80
    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

    # Center logo horizontally, place in upper portion
    logo_x = (width - logo_size) // 2
    logo_y = 50
    img.paste(logo, (logo_x, logo_y), logo)

    # Add text
    draw = ImageDraw.Draw(img)

    # "Aletheia" title
    title_font = get_font(42, bold=True)
    title = "Aletheia"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = logo_y + logo_size + 15
    draw.text((title_x, title_y), title, fill=WHITE, font=title_font)

    # Tagline
    tagline_font = get_font(16)
    tagline = TAGLINE_PRIMARY
    tagline_bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tagline_width = tagline_bbox[2] - tagline_bbox[0]
    tagline_x = (width - tagline_width) // 2
    tagline_y = title_y + 50
    draw.text((tagline_x, tagline_y), tagline, fill=GRAY, font=tagline_font)

    # Save
    img.save(output_path, "PNG")
    print(f"   Saved: {output_path.name} ({width}x{height})")


def create_marquee_promo(output_path: Path) -> None:
    """Create 1400x560 marquee promo tile."""
    width, height = 1400, 560

    # Create gradient background
    img = create_simple_gradient(width, height)

    # Add green glow on left side
    img = add_glow(img, (350, height // 2), 250, BRAND_GREEN, 0.12)

    # Add blue accent glow on right
    img = add_glow(img, (width - 300, height // 2 + 50), 200, BRAND_ACCENT, 0.08)

    # Load logo
    logo = Image.open(ICON_PATH).convert("RGBA")
    logo_size = 140
    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

    # Position logo on left side
    logo_x = 120
    logo_y = (height - logo_size) // 2
    img.paste(logo, (logo_x, logo_y), logo)

    # Add text on left-center
    draw = ImageDraw.Draw(img)

    text_x = logo_x + logo_size + 50

    # "Aletheia" title - large
    title_font = get_font(72, bold=True)
    title = "Aletheia"
    title_y = height // 2 - 70
    draw.text((text_x, title_y), title, fill=WHITE, font=title_font)

    # Primary tagline
    tagline_font = get_font(28)
    tagline_y = title_y + 85
    draw.text((text_x, tagline_y), TAGLINE_PRIMARY, fill=GRAY, font=tagline_font)

    # Secondary tagline (smaller, more muted)
    tagline2_font = get_font(20)
    tagline2_y = tagline_y + 40
    draw.text((text_x, tagline2_y), TAGLINE_SECONDARY, fill=(120, 120, 140), font=tagline2_font)

    # Add screenshot preview on right side if available
    if SCREENSHOT_PATH.exists():
        screenshot = Image.open(SCREENSHOT_PATH)

        # Scale screenshot to fit nicely
        ss_height = 380
        ss_width = int(screenshot.width * ss_height / screenshot.height)
        screenshot = screenshot.resize((ss_width, ss_height), Image.Resampling.LANCZOS)

        # Add rounded corners effect (simple crop for now)
        # Position on right side
        ss_x = width - ss_width - 80
        ss_y = (height - ss_height) // 2

        # Add subtle shadow
        shadow = Image.new("RGBA", (ss_width + 20, ss_height + 20), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle([10, 10, ss_width + 10, ss_height + 10], fill=(0, 0, 0, 80))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))

        img_rgba = img.convert("RGBA")
        img_rgba.paste(shadow, (ss_x - 10, ss_y - 10), shadow)
        img_rgba.paste(screenshot, (ss_x, ss_y))
        img = img_rgba.convert("RGB")

    # Save
    img.save(output_path, "PNG")
    print(f"   Saved: {output_path.name} ({width}x{height})")


def main() -> int:
    print("=" * 50)
    print("Generating Chrome Web Store Promo Tiles")
    print("=" * 50)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check for icon
    if not ICON_PATH.exists():
        print(f"Error: Icon not found at {ICON_PATH}")
        return 1

    # Generate tiles
    print("\n[1/2] Creating Small Promo Tile (440x280)...")
    create_small_promo(OUTPUT_DIR / "promo-small-440x280.png")

    print("\n[2/2] Creating Marquee Promo Tile (1400x560)...")
    create_marquee_promo(OUTPUT_DIR / "promo-marquee-1400x560.png")

    print("\n" + "=" * 50)
    print("Promo tiles generated successfully!")
    print("=" * 50)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nReady to upload to Chrome Web Store.")

    return 0


if __name__ == "__main__":
    exit(main())
