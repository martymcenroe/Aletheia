import json
import time
import boto3
import uuid

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = "AletheiaAgentState"
table = dynamodb.Table(TABLE_NAME)

# TTL: 30 days in seconds
TTL_SECONDS = 2592000


def lambda_handler(event, context):
    try:
        print("Harvester Event:", json.dumps(event))

        # 1. Parse Input
        body = json.loads(event["body"]) if "body" in event else event
        user_input = body.get("word")

        if not user_input:
            return {"statusCode": 400, "body": json.dumps({"error": "No word provided"})}

        # 2. Create Record with current schema
        record_id = str(uuid.uuid4())
        now_ms = str(int(time.time() * 1000))  # Epoch milliseconds as string
        ttl_value = int(time.time()) + TTL_SECONDS

        item = {
            "thread_id": record_id,
            "checkpoint_id": now_ms,  # Sort key: epoch ms timestamp
            "input": user_input,      # Current schema field name
            "url": body.get("url", "N/A"),
            "title": body.get("title", "N/A"),
            "raw_context": body.get("context", ""),
            "status": "harvested",
            "ttl": ttl_value,         # 30-day auto-expiry
        }

        # 3. Save to DB
        table.put_item(Item=item)
        print(f"Success: Harvested {record_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Data harvested", "id": record_id})
        }

    except Exception as e:
        print(f"Harvester Error: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
