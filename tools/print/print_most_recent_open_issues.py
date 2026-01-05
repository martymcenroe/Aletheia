#!/usr/bin/env python3
"""
Print Most Recent Open Issues

Fetches all open GitHub issues, formats them in markdown, saves to docs/,
and prints using pandoc + SumatraPDF with fancy headers.

Usage:
    python tools/print_most_recent_open_issues.py -ss    # Single-sided
    python tools/print_most_recent_open_issues.py -ds    # Double-sided (if printer supports)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# Configuration
REPO = "martymcenroe/Aletheia"
PANDOC_PATH = "pandoc"  # Use PATH
SUMATRA_PATH = r"C:\Users\mcwiz\AppData\Local\SumatraPDF\SumatraPDF.exe"
PRINTER_NAME = "Brother HL-L6300DW series Printer"
PANDOC_HEADER = "tools/print/pandoc-header.tex"
PRINT_OUTPUT_DIR = "temp-pdfs"


def fetch_open_issues():
    """Fetch all open issues from GitHub using gh CLI."""
    print("Fetching open issues from GitHub...")

    cmd = [
        "gh", "issue", "list",
        "--repo", REPO,
        "--state", "open",
        "--limit", "1000",  # Get all open issues
        "--json", "number,title,labels,createdAt,updatedAt,body"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace invalid chars instead of failing
            check=True
        )
        issues = json.loads(result.stdout)
        print(f"Fetched {len(issues)} open issues")
        return issues
    except subprocess.CalledProcessError as e:
        print(f"Error fetching issues: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)


def format_issues_markdown(issues):
    """Format issues as markdown document."""
    # Sort by issue number (ascending)
    issues_sorted = sorted(issues, key=lambda x: x['number'])

    # Generate markdown
    lines = []
    lines.append("# Aletheia - Open Issues")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M CT')}")
    lines.append(f"**Total Open Issues:** {len(issues)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for issue in issues_sorted:
        # Issue header
        lines.append(f"## Issue #{issue['number']}: {issue['title']}")
        lines.append("")

        # Labels
        if issue['labels']:
            label_names = [label['name'] for label in issue['labels']]
            lines.append(f"**Labels:** {', '.join(label_names)}")
            lines.append("")

        # Dates
        created = datetime.fromisoformat(issue['createdAt'].replace('Z', '+00:00'))
        updated = datetime.fromisoformat(issue['updatedAt'].replace('Z', '+00:00'))
        lines.append(f"**Created:** {created.strftime('%Y-%m-%d')}")
        lines.append(f"**Updated:** {updated.strftime('%Y-%m-%d')}")
        lines.append("")

        # Body (strip trailing whitespace from each line to pass pre-commit hooks)
        if issue['body']:
            lines.append("### Description")
            lines.append("")
            body_lines = [line.rstrip() for line in issue['body'].splitlines()]
            lines.append("\n".join(body_lines))
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def save_markdown(content):
    """Save markdown to docs/6000-open-issues.md (static filename)."""
    docs_dir = Path("docs")
    filepath = docs_dir / "6000-open-issues.md"

    print(f"Saving to {filepath}...")
    filepath.write_text(content, encoding='utf-8')
    print(f"Saved {filepath}")

    return filepath


def generate_pdf(markdown_path, duplex=False):
    """Generate PDF using pandoc with fancy headers."""
    # Ensure output directory exists
    output_dir = Path(PRINT_OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)

    # Generate PDF in temp-pdfs/ directory
    pdf_filename = markdown_path.stem + '.pdf'
    pdf_path = output_dir / pdf_filename

    print("Generating PDF with pandoc...")

    # Create custom header with actual filepath and timestamp
    header_template = Path(PANDOC_HEADER).read_text(encoding='utf-8')

    # Get markdown file's last modification time
    mtime = markdown_path.stat().st_mtime
    mod_datetime = datetime.fromtimestamp(mtime)
    timestamp = mod_datetime.strftime('%Y-%m-%d %H:%M')

    # Replace placeholders with actual values
    filepath_display = str(markdown_path).replace('\\', '/')  # e.g., docs/6000-open-issues-2025-12-28.md
    custom_header = header_template.replace('FILEPATH', filepath_display)
    custom_header = custom_header.replace('MODTIME', f'Modified: {timestamp} CT')

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
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
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

    cmd.append(str(pdf_path.absolute()))  # Use absolute path for Windows

    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        mode = "double-sided" if duplex else "single-sided"
        print(f"Sent to printer: {PRINTER_NAME} ({mode})")
    except subprocess.CalledProcessError as e:
        print(f"Print error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch open GitHub issues, save to docs/, and print with fancy headers. Default: double-sided"
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-ss', '--single-sided', action='store_true',
                      help='Print single-sided (overrides default)')
    group.add_argument('-ds', '--double-sided', action='store_true',
                      help='Print double-sided (default - uses printer duplex setting)')

    args = parser.parse_args()

    # Determine print mode (default to double-sided)
    duplex = not args.single_sided  # True unless -ss specified
    mode_str = "double-sided" if duplex else "single-sided"
    print(f"Print mode: {mode_str}")
    print("")

    # Workflow
    issues = fetch_open_issues()
    markdown_content = format_issues_markdown(issues)
    markdown_path = save_markdown(markdown_content)

    pdf_path = generate_pdf(markdown_path, duplex)
    print_pdf(pdf_path, duplex)

    # Clean up PDF after successful print
    if pdf_path.exists():
        pdf_path.unlink()

    print("")
    print("Complete!")
    print(f"   Markdown: {markdown_path}")
    print(f"   PDF: {pdf_path} (deleted after print)")
    print(f"   Printed to: {PRINTER_NAME} ({mode_str})")


if __name__ == "__main__":
    main()
