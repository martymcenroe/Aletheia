#!/usr/bin/env python3
"""
Print Markdown to PDF

General-purpose utility to convert markdown files to PDF with fancy headers and print them.
Supports batch printing directories with new/modified file filtering and spooler monitoring.

Usage:
    # Single file
    python tools/print_markdown.py <file.md>              # Double-sided (default)
    python tools/print_markdown.py <file.md> -ss          # Single-sided

    # Directory batch printing
    python tools/print_markdown.py docs/                  # New files only (default)
    python tools/print_markdown.py docs/ -new -modified   # New OR modified
    python tools/print_markdown.py docs/ -all             # All markdown files
    python tools/print_markdown.py docs/ -all -ss         # All files, single-sided
    python tools/print_markdown.py docs/ -wait 10         # 10 minute wait between prints
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import win32print
    import pywintypes
except ImportError:
    print("Error: pywin32 not installed. Run: poetry add pywin32")
    sys.exit(1)


# Configuration
PANDOC_PATH = "pandoc"  # Use PATH
SUMATRA_PATH = r"C:\Users\mcwiz\AppData\Local\SumatraPDF\SumatraPDF.exe"
PRINTER_NAME = "Brother HL-L6300DW series Printer"
PANDOC_HEADER = "tools/print/pandoc-header.tex"
PRINT_HISTORY_FILE = ".print-history.json"
PRINT_OUTPUT_DIR = "temp-pdfs"
JOB_TIMEOUT_SECONDS = 300  # 5 minutes


def load_print_history():
    """Load print history from JSON file."""
    history_path = Path(PRINT_HISTORY_FILE)
    if history_path.exists():
        with open(history_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_print_history(history):
    """Save print history to JSON file."""
    with open(PRINT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)


def is_new_file(filepath, history):
    """Check if file has never been printed."""
    return str(filepath) not in history


def is_modified_file(filepath, history):
    """Check if file has been modified since last print."""
    filepath_str = str(filepath)
    if filepath_str not in history:
        return False  # New files are "new", not "modified"

    last_mtime = history[filepath_str].get('mtime_at_print', 0)
    current_mtime = filepath.stat().st_mtime
    return current_mtime > last_mtime


def filter_markdown_files(directory, new=False, modified=False, all_files=False):
    """Get list of markdown files based on filter criteria."""
    md_files = sorted(directory.glob("*.md"))

    if all_files:
        # Skip 0003-file-inventory.md - save for end
        deferred = []
        regular = []
        for f in md_files:
            if f.name == "0003-file-inventory.md":
                deferred.append(f)
            else:
                regular.append(f)
        return regular + deferred

    # Default to new if no filters specified
    if not new and not modified:
        new = True

    history = load_print_history()
    filtered = []
    deferred = []

    for md_file in md_files:
        # Defer 0003-file-inventory.md to end
        if md_file.name == "0003-file-inventory.md":
            if new and is_new_file(md_file, history):
                deferred.append(md_file)
            elif modified and is_modified_file(md_file, history):
                deferred.append(md_file)
            continue

        if new and is_new_file(md_file, history):
            filtered.append(md_file)
        elif modified and is_modified_file(md_file, history):
            filtered.append(md_file)

    return filtered + deferred


def generate_pdf(markdown_path):
    """Generate PDF using pandoc with fancy headers."""
    # Ensure output directory exists
    output_dir = Path(PRINT_OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)

    # Generate PDF in temp-pdfs/ directory
    pdf_filename = markdown_path.stem + '.pdf'
    pdf_path = output_dir / pdf_filename

    print(f"Generating PDF from {markdown_path}...")

    # Create custom header with actual filepath and timestamp
    header_template = Path(PANDOC_HEADER).read_text(encoding='utf-8')

    # Get markdown file's last modification time
    mtime = markdown_path.stat().st_mtime
    mod_datetime = datetime.fromtimestamp(mtime)
    timestamp = mod_datetime.strftime('%Y-%m-%d %H:%M')

    # Replace placeholders with actual values
    filepath_display = str(markdown_path).replace('\\', '/')
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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Generated {pdf_path}")
        return pdf_path
    except subprocess.CalledProcessError as e:
        print(f"Pandoc error: {e.stderr}")
        raise
    finally:
        # Clean up temp header
        if temp_header.exists():
            temp_header.unlink()


def send_to_printer(pdf_path, duplex=False):
    """Send PDF to printer via SumatraPDF."""
    # SumatraPDF command with duplex control
    cmd = [
        SUMATRA_PATH,
        "-print-to", PRINTER_NAME,
        "-silent",
    ]

    # Add print settings for duplex/simplex
    if duplex:
        cmd.extend(["-print-settings", "duplex"])
    else:
        cmd.extend(["-print-settings", "simplex"])

    cmd.append(str(pdf_path.absolute()))

    subprocess.run(cmd, check=True)


def get_latest_print_job(printer_name, document_name):
    """Find the most recent print job matching the document name."""
    try:
        printer_handle = win32print.OpenPrinter(printer_name)
        jobs = win32print.EnumJobs(printer_handle, 0, 10)  # Get last 10 jobs
        win32print.ClosePrinter(printer_handle)

        # Find job matching our document name (PDF filename)
        for job in jobs:
            if document_name in job.get('pDocument', ''):
                return job['JobId']

        # If not found in first 10, return most recent
        if jobs:
            return jobs[0]['JobId']

        return None
    except Exception as e:
        print(f"Warning: Could not find print job: {e}")
        return None


def get_job_status_info(printer_name, job_id):
    """Get current status of a print job."""
    try:
        printer_handle = win32print.OpenPrinter(printer_name)
        job = win32print.GetJob(printer_handle, job_id, 1)
        win32print.ClosePrinter(printer_handle)

        status = job['Status']

        # Map status flags to readable states
        if status & win32print.JOB_STATUS_PRINTED:
            return 'PRINTED', None
        elif status & win32print.JOB_STATUS_ERROR:
            return 'ERROR', 'Print error occurred'
        elif status & win32print.JOB_STATUS_OFFLINE:
            return 'OFFLINE', 'Printer is offline'
        elif status & win32print.JOB_STATUS_PAPEROUT:
            return 'PAPEROUT', 'Printer out of paper'
        elif status & win32print.JOB_STATUS_PAUSED:
            return 'PAUSED', 'Print job paused'
        elif status & win32print.JOB_STATUS_DELETED:
            return 'DELETED', 'Print job was cancelled'
        elif status & win32print.JOB_STATUS_PRINTING:
            return 'PRINTING', None
        elif status & win32print.JOB_STATUS_SPOOLING:
            return 'SPOOLING', None
        else:
            return 'UNKNOWN', None

    except pywintypes.error as e:
        # Job might have completed and been removed from queue
        # Error 2151677952 = Job not found in queue
        # Error 87 = The parameter is incorrect (job completed and removed)
        if e.winerror == 2151677952 or e.winerror == 87:
            return 'COMPLETED', None
        raise


def monitor_print_job(printer_name, job_id, pdf_filename):
    """Monitor print job until completion or error."""
    start_time = time.time()
    last_status = None

    print(f"Monitoring print job #{job_id}...")

    while True:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > JOB_TIMEOUT_SECONDS:
            print(f"\nTimeout after {int(elapsed)}s - job may be stuck")
            response = input("Press Enter to continue waiting, or 's' to skip: ")
            if response.lower() == 's':
                return False, "Timeout - skipped by user"
            start_time = time.time()  # Reset timeout

        try:
            status, error_msg = get_job_status_info(printer_name, job_id)

            # Show status changes
            if status != last_status:
                print(f"Status: {status}")
                last_status = status

            # Handle terminal states
            if status in ['PRINTED', 'COMPLETED']:
                print(f"Print job completed successfully ({int(elapsed)}s)")
                return True, None

            elif status == 'DELETED':
                return False, "Job was cancelled"

            elif status in ['ERROR', 'OFFLINE', 'PAPEROUT', 'PAUSED']:
                print(f"\nPrinter error: {error_msg or status}")
                response = input("Press Enter when ready to continue, or 's' to skip: ")
                if response.lower() == 's':
                    return False, f"Skipped due to {status}"
                # User fixed it, continue monitoring
                print("Resuming monitoring...")

            elif status in ['SPOOLING', 'PRINTING', 'UNKNOWN']:
                # Still processing, show elapsed time
                print(f"  Elapsed: {int(elapsed)}s", end='\r')
                time.sleep(3)

        except Exception as e:
            print(f"\nError monitoring job: {e}")
            response = input("Press Enter to retry, or 's' to skip: ")
            if response.lower() == 's':
                return False, f"Monitoring error: {e}"


def print_with_monitoring(pdf_path, duplex=False):
    """Print PDF and monitor spooler until completion or error."""
    mode = "double-sided" if duplex else "single-sided"
    print(f"Printing {pdf_path.name} ({mode})...")

    try:
        # Send to printer
        send_to_printer(pdf_path, duplex)

        # Find the job in spooler
        document_name = pdf_path.name
        time.sleep(1)  # Give spooler a moment to register the job
        job_id = get_latest_print_job(PRINTER_NAME, document_name)

        if job_id is None:
            print("Warning: Could not find print job in spooler - assuming success")
            return True, None

        # Monitor until completion
        return monitor_print_job(PRINTER_NAME, job_id, document_name)

    except subprocess.CalledProcessError as e:
        print(f"Error sending to printer: {e}")
        response = input("Press Enter to retry, or 's' to skip: ")
        if response.lower() == 's':
            return False, f"Print error: {e}"
        # Retry
        return print_with_monitoring(pdf_path, duplex)


def countdown_wait(minutes):
    """Wait with countdown timer."""
    total_seconds = minutes * 60
    print(f"\nWaiting {minutes} minute(s) before next print...")

    for remaining in range(total_seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        print(f"  Time remaining: {mins:02d}:{secs:02d}", end='\r')
        time.sleep(1)

    print(f"  Time remaining: 00:00")
    print("Resuming...\n")


def update_print_history(filepath):
    """Update print history for a file."""
    history = load_print_history()

    history[str(filepath)] = {
        'last_printed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'mtime_at_print': filepath.stat().st_mtime
    }

    save_print_history(history)


def main():
    parser = argparse.ArgumentParser(
        description="Convert markdown to PDF with fancy headers and print. Default: double-sided, new files only"
    )
    parser.add_argument('path', type=Path,
                       help='Path to markdown file or directory')

    # Filter options
    filter_group = parser.add_argument_group('file filters (directory mode)')
    filter_group.add_argument('-new', action='store_true',
                             help='Include new files (default if no filter specified)')
    filter_group.add_argument('-modified', action='store_true',
                             help='Include modified files')
    filter_group.add_argument('-all', action='store_true',
                             help='Include all files (overrides -new/-modified)')

    # Print options
    print_group = parser.add_argument_group('print options')
    duplex_group = print_group.add_mutually_exclusive_group()
    duplex_group.add_argument('-ss', '--single-sided', action='store_true',
                             help='Print single-sided')
    duplex_group.add_argument('-ds', '--double-sided', action='store_true',
                             help='Print double-sided (default)')
    print_group.add_argument('-wait', type=int, default=0, metavar='N',
                            help='Minutes to wait after print completes before sending next job (default: 0 - immediate)')

    args = parser.parse_args()

    # Validate input path exists
    if not args.path.exists():
        print(f"Error: Path not found: {args.path}")
        sys.exit(1)

    # Determine print mode
    duplex = not args.single_sided
    mode_str = "double-sided" if duplex else "single-sided"

    # Handle directory vs single file
    if args.path.is_dir():
        # Directory mode - batch printing
        print(f"Directory mode: {args.path}")
        print(f"Print mode: {mode_str}")
        if args.wait > 0:
            print(f"Wait time: {args.wait} minute(s) after each job completes")
        else:
            print(f"Wait time: Immediate (send next job as soon as current completes)")
        print("")

        # Filter files
        files = filter_markdown_files(args.path, args.new, args.modified, args.all)

        if not files:
            print("No files to print based on filter criteria")
            sys.exit(0)

        print(f"Found {len(files)} file(s) to print:")
        for f in files:
            print(f"  - {f.name}")
        print("")

        # Batch print
        successful = 0
        skipped = 0

        for i, md_file in enumerate(files):
            print(f"[{i+1}/{len(files)}] Processing {md_file.name}")
            print("-" * 60)

            try:
                # Generate PDF
                pdf_path = generate_pdf(md_file)

                # Print with monitoring
                success, error = print_with_monitoring(pdf_path, duplex)

                if success:
                    update_print_history(md_file)
                    successful += 1
                    print(f"Success: {md_file.name}")

                    # Clean up PDF after successful print
                    if pdf_path.exists():
                        pdf_path.unlink()

                    # Wait before next file (unless last file)
                    if i < len(files) - 1 and args.wait > 0:
                        countdown_wait(args.wait)
                    elif i < len(files) - 1:
                        print("Sending next job immediately...")
                else:
                    skipped += 1
                    print(f"Skipped: {md_file.name} - {error}")
                    # Keep PDF for inspection on failure

            except Exception as e:
                print(f"Error processing {md_file.name}: {e}")
                response = input("Press Enter to continue to next file, or Ctrl-C to abort: ")
                skipped += 1

            print("")

        # Summary
        print("=" * 60)
        print("Batch printing complete!")
        print(f"  Successful: {successful}")
        print(f"  Skipped: {skipped}")
        print(f"  Total: {len(files)}")

    else:
        # Single file mode
        if not args.path.suffix == '.md':
            print(f"Error: File must be a markdown file (.md): {args.path}")
            sys.exit(1)

        print(f"Single file mode: {args.path}")
        print(f"Print mode: {mode_str}")
        print("")

        # Generate and print
        pdf_path = generate_pdf(args.path)
        success, error = print_with_monitoring(pdf_path, duplex)

        if success:
            update_print_history(args.path)

            # Clean up PDF after successful print
            if pdf_path.exists():
                pdf_path.unlink()

            print("")
            print("Complete!")
            print(f"   Markdown: {args.path}")
            print(f"   PDF: {pdf_path} (deleted after print)")
            print(f"   Printed to: {PRINTER_NAME} ({mode_str})")
        else:
            print(f"Print failed: {error}")
            print(f"   PDF kept for inspection: {pdf_path}")
            sys.exit(1)


if __name__ == "__main__":
    main()
