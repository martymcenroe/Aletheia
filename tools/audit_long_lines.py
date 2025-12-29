#!/usr/bin/env python3
"""
Audit markdown files for long lines that would overflow when printed.
"""

from pathlib import Path

docs_dir = Path("docs")
md_files = sorted(docs_dir.glob("*.md"))

# Threshold for line length (rough estimate for printed page width)
# With 1-inch margins and typical font, ~100-120 chars is safe
THRESHOLD = 100

results = []

for md_file in md_files:
    try:
        content = md_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        max_len = max(len(line) for line in lines) if lines else 0

        if max_len > THRESHOLD:
            # Count how many long lines
            long_lines = [i+1 for i, line in enumerate(lines) if len(line) > THRESHOLD]
            results.append((md_file.name, max_len, len(long_lines)))
    except Exception as e:
        print(f"Error reading {md_file}: {e}")

# Sort by max length descending
results.sort(key=lambda x: x[1], reverse=True)

print(f"Files with lines longer than {THRESHOLD} characters:\n")
print(f"{'File':<50} {'Max Length':<12} {'# Long Lines'}")
print("=" * 80)

for filename, max_len, count in results:
    print(f"{filename:<50} {max_len:<12} {count}")

print(f"\nTotal files with long lines: {len(results)}/{len(md_files)}")
