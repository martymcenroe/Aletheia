import os
import sys
from PIL import Image

# --- CONFIGURATION ---
# The source image must be in the same directory as this script or provide full path
SOURCE_FILENAME = "master_lambda.png" 
# Output directory relative to where the script is run
OUTPUT_DIR = "../extension/icons"
# Required Chrome Extension sizes
SIZES = [16, 32, 48, 128]

def generate_icons():
    """
    Reads a master image, crops it to a center square (removing watermarks),
    and generates specific PNG sizes required for Chrome Extensions.
    """
    # 1. Locate Source
    # Assume script is run from project root, so tools/ is part of path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(script_dir, SOURCE_FILENAME)
    
    # Check if file exists
    if not os.path.exists(source_path):
        print(f"Error: Could not find source image at: {source_path}")
        print(f"Please place '{SOURCE_FILENAME}' in the tools/ folder.")
        sys.exit(1)

    # 2. Prepare Output Directory
    # Resolve output path relative to script location to be safe
    output_abs_path = os.path.join(script_dir, OUTPUT_DIR)
    if not os.path.exists(output_abs_path):
        try:
            os.makedirs(output_abs_path)
            print(f"Created directory: {output_abs_path}")
        except OSError as e:
            print(f"Error creating directory {output_abs_path}: {e}")
            sys.exit(1)

    # 3. Process Image
    try:
        with Image.open(source_path) as img:
            width, height = img.size
            print(f"Loaded '{SOURCE_FILENAME}' ({width}x{height} pixels)")

            # Auto-Crop Logic (Center Square)
            if width != height:
                min_dim = min(width, height)
                left = (width - min_dim) // 2
                top = (height - min_dim) // 2
                right = (width + min_dim) // 2
                bottom = (height + min_dim) // 2
                
                img = img.crop((left, top, right, bottom))
                print(f"  [✓] Auto-cropped to center square: {min_dim}x{min_dim}")
            
            # Resize and Save
            for size in SIZES:
                # Lanczos filter provides best quality for downsampling
                resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
                
                output_filename = f"icon{size}.png"
                full_output_path = os.path.join(output_abs_path, output_filename)
                
                resized_img.save(full_output_path, "PNG")
                print(f"  [✓] Generated: {output_filename}")

            print(f"\nSuccess! All icons saved to: {output_abs_path}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_icons()