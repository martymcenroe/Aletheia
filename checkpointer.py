import pickle
import base64
import boto3
from boto3.dynamodb.conditions import Key
from typing import Optional, Iterator
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple

class DynamoDBSaver(BaseCheckpointSaver):
    def __init__(self, table_name: str = "AletheiaAgentState", region_name: str = "us-east-1"):
        super().__init__()
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Load the latest checkpoint for a thread."""
        thread_id = config["configurable"]["thread_id"]
        try:
            # Query for latest checkpoint (ScanIndexForward=False sorts DESC by SK)
            response = self.table.query(
                KeyConditionExpression=Key("thread_id").eq(thread_id),
                ScanIndexForward=False, 
                Limit=1
            )
            items = response.get("Items", [])
            if not items:
                return None
            
            item = items[0]
            checkpoint = pickle.loads(base64.b64decode(item["checkpoint"]))
            metadata = pickle.loads(base64.b64decode(item["metadata"]))
            # parent_config is set to None for MVP simplicity
            return CheckpointTuple(config, checkpoint, metadata, None)
        except Exception as e:
            # Log error but don't crash; return None to start fresh
            print(f"Error getting checkpoint: {e}")
            return None

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> RunnableConfig:
        """Save the current checkpoint."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]
        try:
            self.table.put_item(
                Item={
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id,
                    "checkpoint": base64.b64encode(pickle.dumps(checkpoint)).decode("utf-8"),
                    "metadata": base64.b64encode(pickle.dumps(metadata)).decode("utf-8")
                }
            )
        except Exception as e:
            print(f"Error putting checkpoint: {e}")
        
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id
            }
        }

    def list(self, config: Optional[RunnableConfig], *, filter: Optional[dict] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> Iterator[CheckpointTuple]:
        """Required abstract method. Not used in this MVP."""
        yield from []
