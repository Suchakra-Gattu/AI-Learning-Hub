"""A three-node LangGraph with a reducer, a checkpointer, and a human pause. No model, no API key.

Install: pip install langgraph
Run:     python graph_demo.py

Tested here with langgraph 1.2.19. APIs change, so check the LangGraph docs if it fails.
"""
from operator import add
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver  # shortcut: loses data on restart. Use a Postgres saver in production.
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    steps: Annotated[list[str], add]  # reducer: updates are appended, not replaced
    approved: bool


def plan(state):
    return {"steps": ["plan: delete old files"]}


def ask_human(state):
    # Pauses here and saves state. The value passed to Command(resume=...) comes back.
    return {"approved": interrupt("Delete old files?")}


def act(state):
    return {"steps": ["act: deleted" if state["approved"] else "act: skipped"]}


builder = StateGraph(State)
builder.add_node(plan)
builder.add_node(ask_human)
builder.add_node(act)
builder.add_edge(START, "plan")
builder.add_edge("plan", "ask_human")
builder.add_edge("ask_human", "act")
builder.add_edge("act", END)
graph = builder.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "demo-1"}}
    paused = graph.invoke({"steps": [], "approved": False}, config)
    print("paused:", paused["__interrupt__"][0].value)
    done = graph.invoke(Command(resume=False), config)  # a human says no
    print("steps:", done["steps"])
    assert done["steps"] == ["plan: delete old files", "act: skipped"]
