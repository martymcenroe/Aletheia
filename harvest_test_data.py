import boto3
import json
import argparse
import sys
from decimal import Decimal

# Helper to handle DynamoDB Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Aletheia Data Harvester: Pulls captured test cases from DynamoDB to local JSON."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output (prints raw JSON for every record found)"
    )
    parser.add_argument(
        "-o", "--output",
        default="test_holistic_data.json",
        help="Specify output filename (default: test_holistic_data.json)"
    )
    return parser.parse_args()

def harvest(verbose=False, filename="test_holistic_data.json"):
    print("Connecting to DynamoDB table: AletheiaAgentState...")
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('AletheiaAgentState')
        response = table.scan()
    except Exception as e:
        print(f"Error connecting to DynamoDB: {e}")
        sys.exit(1)

    items = response.get('Items', [])
    count = len(items)
    print(f"Found {count} items in database.\n")

    export_records = []

    for i, item in enumerate(items):
        # normalize keys
        word = item.get('user_input') or item.get('word')
        doc_id = item.get('thread_id')

        if verbose:
            print(f"--- RECORD #{i+1} RAW DATA ---")
            print(json.dumps(item, cls=DecimalEncoder, indent=2))
            print("-----------------------------")

        if word:
            if not verbose:
                # One-line summary
                print(f" -> [{i+1}/{count}] Harvested: '{word}' (ID: {doc_id})")

            record = {
                "id": doc_id,
                "word": word,
                "url": item.get('url'),
                "title": item.get('title'),
                "context": item.get('raw_context') or item.get('context'),
                "timestamp": item.get('timestamp')
            }
            export_records.append(record)
        else:
            print(f" -> [{i+1}/{count}] SKIPPED: Record {doc_id} missing 'word' field.")

    # Save to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_records, f, cls=DecimalEncoder, indent=2)
        print(f"\nSuccessfully exported {len(export_records)} records to '{filename}'.")
    except IOError as e:
        print(f"\nError writing to file: {e}")

if __name__ == "__main__":
    args = parse_args()
    harvest(verbose=args.verbose, filename=args.output)
