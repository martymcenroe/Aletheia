import boto3
import json
import pickle
import base64

TABLE_NAME = "AletheiaAgentState"
REGION = "us-east-1"
OUTPUT_FILE = "test_holistic_data.json"

def harvest():
    print(f"Connecting to DynamoDB table: {TABLE_NAME}...")
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
    
    try:
        response = table.scan()
        items = response.get("Items", [])
    except Exception as e:
        print(f"Error scanning table: {e}")
        return

    harvested_data = []
    print(f"Found {len(items)} items. Processing...")
    
    for item in items:
        try:
            b64_checkpoint = item.get("checkpoint")
            if not b64_checkpoint:
                continue
                
            checkpoint = pickle.loads(base64.b64decode(b64_checkpoint))
            state = checkpoint.get("channel_values", {})
            
            # 1. Word
            messages = state.get("messages", [])
            word = "UNKNOWN"
            if messages:
                if isinstance(messages[0], tuple):
                    word = messages[0][1]
                elif hasattr(messages[0], 'content'):
                    word = messages[0].content

            # 2. Metadata
            url = state.get("url", "N/A")
            title = state.get("title", "N/A")
            
            # 3. Context (Priority: Debug Raw -> Summary -> Redacted)
            raw = state.get("debug_raw_context")
            compliance = state.get("compliance_data", {}) or {}
            summary = compliance.get("usage_summary")
            
            if raw:
                context_final = raw
            elif summary:
                context_final = f"[SUMMARY ONLY] {summary}"
            else:
                context_final = "[REDACTED]"

            entry = {
                "word": word,
                "url": url,
                "title": title,
                "context": context_final,
                "comment": "Harvested Data"
            }
            
            harvested_data.append(entry)
            
        except Exception as e:
            print(f"Failed to process item {item.get('thread_id', '?')}: {e}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(harvested_data, f, indent=2)
        
    print(f"Successfully exported {len(harvested_data)} records to {OUTPUT_FILE}")

if __name__ == "__main__":
    harvest()
