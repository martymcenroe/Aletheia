import boto3
import argparse
import sys
from operator import itemgetter
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

def parse_args():
    parser = argparse.ArgumentParser(description="Aletheia Log Inspector")
    parser.add_argument("--tail", type=int, default=0, help="Limit output to the last N records")
    parser.add_argument("--full-url", action="store_true", help="Show full URL instead of just the domain")
    return parser.parse_args()

def format_timestamp(iso_str):
    """Parses ISO string and converts to Central Time (Dec 20 10:01)."""
    if not iso_str:
        return "N/A"
    try:
        # Parse ISO (e.g., 2025-12-16T20:05:29.124328+00:00)
        dt_utc = datetime.fromisoformat(iso_str)
        # Convert to Central
        dt_central = dt_utc.astimezone(ZoneInfo("America/Chicago"))
        # Format: Dec 20 10:01
        return dt_central.strftime("%b %d %H:%M")
    except ValueError:
        return iso_str

def extract_domain(url_str):
    """Extracts domain (e.g., wsj.com) from a URL."""
    if not url_str or "://" not in url_str:
        return url_str # Return as-is if it's a Title or malformed
    try:
        return urlparse(url_str).netloc
    except Exception:
        return url_str

def get_display_data(item):
    """Extracts and normalizes display fields from a DynamoDB item."""
    word = item.get('user_input') or item.get('word') or "N/A"
    site = item.get('url') or item.get('title') or "Unknown"
    raw_ts = item.get('timestamp') or ""

    return {
        "raw_timestamp": raw_ts,
        "display_time": format_timestamp(raw_ts),
        "word": word,
        "site_full": site,
        "site_domain": extract_domain(site),
        "thread_id": item.get('thread_id', '')
    }

def main():
    args = parse_args()

    # 1. Connect & Scan
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('AletheiaAgentState')
        response = table.scan()
        items = response.get('Items', [])
    except Exception as e:
        print(f"Error connecting to DynamoDB: {e}")
        sys.exit(1)

    # 2. Extract & Sort
    data = [get_display_data(item) for item in items]
    data.sort(key=itemgetter('raw_timestamp'))

    # 3. Filter (Tail)
    total_count = len(data)
    if args.tail > 0:
        data = data[-args.tail:]

    if not data:
        print("No records found.")
        sys.exit(0)

    # 4. Resolve Site Display (Domain vs Full)
    # We must do this before width calc
    for entry in data:
        entry['display_site'] = entry['site_full'] if args.full_url else entry['site_domain']

    # 5. Dynamic Width Calculation
    idx_digits = len(str(total_count))
    w_idx = 1 + idx_digits + 1 + idx_digits + 1

    w_time = max(len(d['display_time']) for d in data)
    w_word = max(len(d['word']) for d in data)
    w_site = max(len(d['display_site']) for d in data)

    # 6. Print
    for i, entry in enumerate(data):
        offset = total_count - len(data) if args.tail > 0 else 0
        current_idx = offset + i + 1

        idx_str = f"[{current_idx:0{idx_digits}d}/{total_count}]"

        print(
            f"{idx_str:<{w_idx}}   "
            f"{entry['display_time']:<{w_time}}   "
            f"{entry['word']:<{w_word}}   "
            f"{entry['display_site']:<{w_site}}"
        )

if __name__ == "__main__":
    main()
