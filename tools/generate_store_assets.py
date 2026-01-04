import os
import zipfile
from PIL import Image, ImageDraw

# Config
DIST_DIR = "dist"
EXT_DIR = "extension"
ASSETS = {
    "icon-128.png": (128, 128),
    "screenshot-1280x800.png": (1280, 800),
    "small-promo-440x280.png": (440, 280)
}

def create_zip():
    zip_name = os.path.join(DIST_DIR, "aletheia_v1.zip")
    print(f"Creating {zip_name}...")
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(EXT_DIR):
            for file in files:
                # exclude hidden files or source maps
                if file.startswith('.') or file.endswith('.map'):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, EXT_DIR)
                zf.write(file_path, arcname)

def create_images():
    for name, size in ASSETS.items():
        path = os.path.join(DIST_DIR, name)
        print(f"Generating {name} ({size})...")
        img = Image.new('RGB', size, color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        # Simple crosshatch to show it's a placeholder
        d.line((0, 0) + size, fill=(255, 255, 255), width=3)
        d.line((0, size[1], size[0], 0), fill=(255, 255, 255), width=3)
        img.save(path)

if __name__ == "__main__":
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
    create_zip()
    create_images()
    print("Done. Assets in /dist")
