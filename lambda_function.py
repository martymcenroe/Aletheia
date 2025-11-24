import json
import os
import asyncio
import logging
import awslambda
from agent import graph

logger = logging.getLogger()
logger.setLevel(logging.INFO)

async def run_agent_engine(input_text: str, thread_id: str, response_stream):
    """
    Async engine to drive the LangGraph agent and stream tokens back.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph and stream events
    # version="v1" is required for astream_events to return standard event schema
    async for event in graph.astream_events({"messages": [("user", input_text)]}, config, version="v1"):
        kind = event["event"]
        
        # We focus on streaming the raw tokens from the LLM
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                # Format as SSE (Server-Sent Events)
                payload = json.dumps({"type": "token", "content": content})
                response_stream.write(f"data: {payload}\n\n".encode('utf-8'))
        
        # Log tool usage for debugging
        elif kind == "on_tool_start":
            logger.info(f"Tool Triggered: {event['name']}")
            payload = json.dumps({"type": "status", "content": f"Analyzing with {event['name']}..."})
            response_stream.write(f"data: {payload}\n\n".encode('utf-8'))

@awslambda.streamify_response
def lambda_handler(event, context, response_stream):
    """
    AWS Lambda Handler with Response Streaming.
    """
    try:
        # 1. Parse Input
        # API Gateway might wrap the body in a string
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        user_input = body.get("user_input")
        thread_id = body.get("thread_id", "default_thread")

        if not user_input:
            error_msg = json.dumps({"error": "No user_input provided"})
            response_stream.write(f"data: {error_msg}\n\n".encode('utf-8'))
            return

        # 2. Set Content-Type for SSE
        # Note: In Lambda streaming, headers are often set via metadata object if using function URLs, 
        # but for internal logic we focus on the stream body here.
        
        # 3. Run the Async Graph synchronously
        asyncio.run(run_agent_engine(user_input, thread_id, response_stream))

        # 4. End Stream
        response_stream.write(b"data: [DONE]\n\n")

    except Exception as e:
        logger.error(f"Handler Error: {e}", exc_info=True)
        error_payload = json.dumps({"type": "error", "content": str(e)})
        response_stream.write(f"data: {error_payload}\n\n".encode('utf-8'))
