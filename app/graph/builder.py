from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.state import AgentState
from app.graph.nodes.setup import setup
from app.graph.nodes.generate import generate, TOOLS
from app.graph.nodes.save_message import save_message


def build_graph(checkpointer=None):
    """Build and compile the VIAD Bot LangGraph workflow."""

    tool_node = ToolNode(TOOLS)

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("setup", setup)
    graph.add_node("generate", generate)
    graph.add_node("tools", tool_node)
    graph.add_node("save_message", save_message)

    # Entry point
    graph.set_entry_point("setup")

    # Edges
    graph.add_edge("setup", "generate")

    # After generate: tools_condition checks if the LLM made tool calls
    # If yes → execute tools → back to generate
    # If no → save and end
    graph.add_conditional_edges(
        "generate",
        tools_condition,
        {
            "tools": "tools",
            END: "save_message",
        }
    )
    graph.add_edge("tools", "generate")
    graph.add_edge("save_message", END)

    return graph.compile(checkpointer=checkpointer)
