"""
PS-01 Client Onboarding — LangGraph State Schema
"""

from __future__ import annotations

from typing import Optional, TypedDict


class OnboardingState(TypedDict):
    """
    Full state object carried through the LangGraph onboarding pipeline.

    Populated in two stages:
        1. Input fields — set from the incoming webhook payload.
        2. Derived fields — populated by individual graph nodes during execution.
    """

    # ── Input fields (from webhook payload) ──────────────────────────────
    brand_name: str
    account_manager: str
    brand_category: str
    contract_start_date: str          # ISO-8601 date string, e.g. "2025-04-10"
    deliverable_count: int
    billing_contact_email: str
    invoice_cycle: str

    # ── Derived / populated during execution ─────────────────────────────
    account_manager_email: Optional[str]

    drive_folder_id: Optional[str]
    drive_folder_link: Optional[str]

    notion_page_id: Optional[str]
    notion_page_link: Optional[str]

    airtable_record_id: Optional[str]
    airtable_record_link: Optional[str]

    # ── Control-flow metadata ────────────────────────────────────────────
    errors: list[dict]                # [{"step": str, "error": str, "action_taken": str}]
    flags: list[str]                  # halt-condition labels, e.g. "past_contract_date"
    completed_steps: list[str]        # names of successfully finished steps
    halt: bool                        # if True → stop pipeline execution
