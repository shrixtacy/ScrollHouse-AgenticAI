"""
PS-01 Client Onboarding — LangGraph Graph Definition

Defines the state machine that orchestrates all onboarding steps.
Conditional edges after validate_input and duplicate_check check the
``halt`` flag to decide whether to stop or continue.
"""

from __future__ import annotations

import operator
from typing import Annotated

from langgraph.graph import END, StateGraph

from agents.ps01_onboarding.nodes import (
    add_airtable_record,
    create_drive_folder,
    create_notion_hub,
    duplicate_check,
    log_onboarding,
    send_completion_summary,
    send_welcome_email,
    set_drive_permissions,
    validate_input,
)
from agents.ps01_onboarding.state import OnboardingState


# ─────────────────────────────────────────────────────────────────────────────
# Reducer-aware state: list fields are merged via operator.add so that
# each node can return *new* items without overwriting previous ones.
# ─────────────────────────────────────────────────────────────────────────────

class ReducerState(OnboardingState, total=False):
    errors: Annotated[list[dict], operator.add]
    flags: Annotated[list[str], operator.add]
    completed_steps: Annotated[list[str], operator.add]


# ─────────────────────────────────────────────────────────────────────────────
# Conditional edge helpers
# ─────────────────────────────────────────────────────────────────────────────

def _should_halt(state: ReducerState) -> str:
    """Return 'halt' if pipeline should stop, otherwise 'continue'."""
    if state.get("halt"):
        return "halt"
    return "continue"


# ─────────────────────────────────────────────────────────────────────────────
# Build graph
# ─────────────────────────────────────────────────────────────────────────────

def build_onboarding_graph() -> StateGraph:
    """
    Construct and compile the PS-01 onboarding LangGraph.

    Node order:
        validate_input → duplicate_check → send_welcome_email →
        create_drive_folder → set_drive_permissions → create_notion_hub →
        add_airtable_record → send_completion_summary → log_onboarding → END
    """
    graph = StateGraph(ReducerState)

    # ── Register nodes ───────────────────────────────────────────────────
    graph.add_node("validate_input", validate_input)
    graph.add_node("duplicate_check", duplicate_check)
    graph.add_node("send_welcome_email", send_welcome_email)
    graph.add_node("create_drive_folder", create_drive_folder)
    graph.add_node("set_drive_permissions", set_drive_permissions)
    graph.add_node("create_notion_hub", create_notion_hub)
    graph.add_node("add_airtable_record", add_airtable_record)
    graph.add_node("send_completion_summary", send_completion_summary)
    graph.add_node("log_onboarding", log_onboarding)

    # ── Entry point ──────────────────────────────────────────────────────
    graph.set_entry_point("validate_input")

    # ── Conditional edges (halt gates) ───────────────────────────────────
    graph.add_conditional_edges(
        "validate_input",
        _should_halt,
        {"halt": "log_onboarding", "continue": "duplicate_check"},
    )

    graph.add_conditional_edges(
        "duplicate_check",
        _should_halt,
        {"halt": "log_onboarding", "continue": "send_welcome_email"},
    )

    # ── Linear edges (always continue) ───────────────────────────────────
    graph.add_edge("send_welcome_email", "create_drive_folder")
    graph.add_edge("create_drive_folder", "set_drive_permissions")
    graph.add_edge("set_drive_permissions", "create_notion_hub")
    graph.add_edge("create_notion_hub", "add_airtable_record")
    graph.add_edge("add_airtable_record", "send_completion_summary")
    graph.add_edge("send_completion_summary", "log_onboarding")

    # ── Terminal ─────────────────────────────────────────────────────────
    graph.add_edge("log_onboarding", END)

    return graph.compile()

# Compile the graph for LangGraph Cloud / Studio deployment
graph = build_onboarding_graph()
