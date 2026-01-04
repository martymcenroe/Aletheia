import json
import boto3
import uuid
from datetime import datetime, timezone

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = "AletheiaAgentState"
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        print("Harvester Event:", json.dumps(event))

        # 1. Parse Input
        body = json.loads(event["body"]) if "body" in event else event
        user_input = body.get("word")

        if not user_input:
            return {"statusCode": 400, "body": json.dumps({"error": "No word provided"})}

        # 2. Create Record
        record_id = str(uuid.uuid4())

        item = {
            "thread_id": record_id,
            "checkpoint_id": "raw_capture",
            "user_input": user_input,
            "url": body.get("url", "N/A"),
            "title": body.get("title", "N/A"),
            "raw_context": body.get("context", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "harvested"
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
