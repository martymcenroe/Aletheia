import json
import os
import asyncio
import logging
import awslambda
from agent import graph
from compliance import analyze_context

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
ALETHEIA_ENV = os.environ.get("ALETHEIA_ENV", "prod")

async def run_agent_engine(input_text: str, thread_id: str, compliance_report: dict, metadata: dict, response_stream):
    """
    Async engine to drive the LangGraph agent and stream tokens back.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initial State Injection
    initial_state = {
        "messages": [("user", input_text)],
        "compliance_data": compliance_report,
        "url": metadata.get("url"),
        "title": metadata.get("title"),
        # [DEV MODE] Inject raw context if enabled
        "debug_raw_context": metadata.get("raw_context") if ALETHEIA_ENV == "dev" else None
    }

    async for event in graph.astream_events(initial_state, config, version="v1"):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                payload = json.dumps({"type": "token", "content": content})
                response_stream.write(f"data: {payload}\n\n".encode('utf-8'))
        elif kind == "on_tool_start":
            logger.info(f"Tool Triggered: {event['name']}")
            payload = json.dumps({"type": "status", "content": f"Analyzing with {event['name']}..."})
            response_stream.write(f"data: {payload}\n\n".encode('utf-8'))

@awslambda.streamify_response
def lambda_handler(event, context, response_stream):
    try:
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        user_input = body.get("word") or body.get("user_input")
        thread_id = body.get("thread_id", "default_thread")
        raw_context = body.get("context", "")
        
        # Capture metadata for State
        metadata = {
            "url": body.get("url", "N/A"),
            "title": body.get("title", "N/A"),
            "raw_context": raw_context
        }

        if not user_input:
            error_msg = json.dumps({"error": "No user_input provided"})
            response_stream.write(f"data: {error_msg}\n\n".encode('utf-8'))
            return

        # Compliance Check
        compliance_report = None
        if raw_context:
            logger.info("Context detected. Running Compliance Engine.")
            compliance_report = analyze_context(user_input, raw_context)
        
        asyncio.run(run_agent_engine(user_input, thread_id, compliance_report, metadata, response_stream))

        response_stream.write(b"data: [DONE]\n\n")

    except Exception as e:
        logger.error(f"Handler Error: {e}", exc_info=True)
        error_payload = json.dumps({"type": "error", "content": str(e)})
        response_stream.write(f"data: {error_payload}\n\n".encode('utf-8'))
