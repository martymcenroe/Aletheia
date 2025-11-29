from typing import TypedDict, Annotated, Literal
from langchain_core.messages import AnyMessage, AIMessage
from langchain_core.tools import tool
from langchain_aws import ChatBedrockConverse
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from checkpointer import DynamoDBSaver
from guardrails import check_safety, SafetyAssessment

# 1. State Schema
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    safety_report: SafetyAssessment

# 2. Tools
@tool
def lookup_definition(word: str) -> str:
    """Look up the definition and cultural context of a word."""
    return f"Contextual analysis for '{word}': [Placeholder] This word implies specific nuance in this context."

tools = [lookup_definition]

# 3. Model
llm = ChatBedrockConverse(
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    temperature=0,
    region_name="us-east-1"
).bind_tools(tools)

# 4. Nodes
def agent_node(state: AgentState):
    return {"messages": [llm.invoke(state["messages"])]}

def guardrail_node(state: AgentState):
    """Classifies the last user message for safety."""
    last_message = state["messages"][-1]
    assessment = check_safety(last_message.content)
    return {"safety_report": assessment}

def block_node(state: AgentState):
    """Returns a refusal message if content is unsafe."""
    reason = state["safety_report"].reasoning
    status = state["safety_report"].status
    return {"messages": [AIMessage(content=f"I cannot fulfill this request. Detected {status} content: {reason}")]}

# 5. Conditional Logic
def safety_check(state: AgentState) -> Literal["agent", "block"]:
    if state["safety_report"].status == "SAFE":
        return "agent"
    return "block"

# 6. Graph Construction
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("block", block_node)

# Add Edges
workflow.add_edge(START, "guardrail")

# Conditional Edge: Guardrail -> (Agent OR Block)
workflow.add_conditional_edges(
    "guardrail",
    safety_check,
    {
        "agent": "agent",
        "block": "block"
    }
)

workflow.add_edge("block", END)
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# 7. Compilation
checkpointer = DynamoDBSaver()
graph = workflow.compile(checkpointer=checkpointer)