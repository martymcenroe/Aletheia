#!/usr/bin/env python3
"""
Print Markdown to PDF

General-purpose utility to convert markdown files to PDF with fancy headers and print them.

Usage:
    python tools/print_markdown.py <file.md>          # Double-sided (default)
    python tools/print_markdown.py <file.md> -ss      # Single-sided
    python tools/print_markdown.py <file.md> -ds      # Double-sided (explicit)
"""

import argparse
import subprocess
import sys
from pathlib import Path


# Configuration
PANDOC_PATH = "pandoc"  # Use PATH
SUMATRA_PATH = r"C:\Users\mcwiz\AppData\Local\SumatraPDF\SumatraPDF.exe"
PRINTER_NAME = "Brother HL-L6300DW series Printer"
PANDOC_HEADER = ".pandoc-header.tex"


def generate_pdf(markdown_path, duplex=False):
    """Generate PDF using pandoc with fancy headers."""
    pdf_path = markdown_path.with_suffix('.pdf')

    print(f"Generating PDF from {markdown_path}...")

    # Create custom header with actual filepath and timestamp
    header_template = Path(PANDOC_HEADER).read_text(encoding='utf-8')

    # Get actual Windows local time
    result = subprocess.run(
        ['powershell.exe', '-Command', 'Get-Date -Format "yyyy-MM-dd HH:mm"'],
        capture_output=True,
        text=True,
        check=True
    )
    timestamp = result.stdout.strip()

    # Replace placeholders with actual values
    filepath_display = str(markdown_path).replace('\\', '/')
    custom_header = header_template.replace('FILEPATH', filepath_display)
    custom_header = custom_header.replace('MODTIME', f'Generated: {timestamp} CT')

    # Write to temporary header file
    temp_header = Path('.pandoc-header-temp.tex')
    temp_header.write_text(custom_header, encoding='utf-8')

    # Pandoc command with XeLaTeX engine and custom header
    cmd = [
        PANDOC_PATH,
        "-f", "gfm",  # GitHub-flavored markdown
        str(markdown_path),
        "-o", str(pdf_path),
        "--pdf-engine=xelatex",
        "-H", str(temp_header),
        "-V", "geometry:margin=1in"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Generated {pdf_path}")
        return pdf_path
    except subprocess.CalledProcessError as e:
        print(f"Pandoc error: {e.stderr}")
        sys.exit(1)
    finally:
        # Clean up temp header
        if temp_header.exists():
            temp_header.unlink()


def print_pdf(pdf_path, duplex=False):
    """Print PDF using SumatraPDF."""
    print(f"Printing {pdf_path}...")

    # SumatraPDF command with duplex control
    cmd = [
        SUMATRA_PATH,
        "-print-to", PRINTER_NAME,
        "-silent",
    ]

    # Add print settings for duplex/simplex
    if duplex:
        print("Double-sided printing requested.")
        cmd.extend(["-print-settings", "duplex"])
    else:
        print("Single-sided printing requested.")
        cmd.extend(["-print-settings", "simplex"])

    cmd.append(str(pdf_path.absolute()))

    try:
        subprocess.run(cmd, check=True)
        mode = "double-sided" if duplex else "single-sided"
        print(f"Sent to printer: {PRINTER_NAME} ({mode})")
    except subprocess.CalledProcessError as e:
        print(f"Print error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert markdown to PDF with fancy headers and print. Default: double-sided"
    )
    parser.add_argument('markdown_file', type=Path,
                       help='Path to the markdown file to print')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-ss', '--single-sided', action='store_true',
                      help='Print single-sided (overrides default)')
    group.add_argument('-ds', '--double-sided', action='store_true',
                      help='Print double-sided (default - explicit flag)')

    args = parser.parse_args()

    # Validate input file exists
    if not args.markdown_file.exists():
        print(f"Error: File not found: {args.markdown_file}")
        sys.exit(1)

    if not args.markdown_file.suffix == '.md':
        print(f"Error: File must be a markdown file (.md): {args.markdown_file}")
        sys.exit(1)

    # Determine print mode (default to double-sided)
    duplex = not args.single_sided  # True unless -ss specified
    mode_str = "double-sided" if duplex else "single-sided"
    print(f"Print mode: {mode_str}")
    print("")

    # Workflow
    pdf_path = generate_pdf(args.markdown_file, duplex)
    print_pdf(pdf_path, duplex)

    print("")
    print("Complete!")
    print(f"   Markdown: {args.markdown_file}")
    print(f"   PDF: {pdf_path}")
    print(f"   Printed to: {PRINTER_NAME} ({mode_str})")


if __name__ == "__main__":
    main()
