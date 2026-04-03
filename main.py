"""
Scrollhouse Agentic AI — FastAPI Application

Exposes:
    POST /webhook/onboard   → triggers the PS-01 client onboarding agent
    GET  /health             → simple healthcheck
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

from agents.ps01_onboarding.graph import build_onboarding_graph
from shared.logger import logger

# ── Load environment variables ───────────────────────────────────────────────
load_dotenv()


# ── Pydantic request model ──────────────────────────────────────────────────

class OnboardingRequest(BaseModel):
    """Incoming webhook payload from the client onboarding form."""

    brand_name: str = Field(..., min_length=1, description="Client brand name")
    account_manager: str = Field(..., min_length=1, description="Assigned account manager")
    brand_category: str = Field(..., min_length=1, description="e.g. Skincare, Tech, F&B")
    contract_start_date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO-8601 date (YYYY-MM-DD)",
    )
    deliverable_count: int = Field(..., gt=0, description="Monthly deliverables")
    billing_contact_email: EmailStr = Field(..., description="Client billing email")
    invoice_cycle: str = Field(..., min_length=1, description="e.g. monthly, quarterly")


# ── App lifecycle ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Compile the LangGraph once at startup."""
    logger.info("Compiling PS-01 onboarding graph …")
    app.state.onboarding_graph = build_onboarding_graph()
    logger.info("PS-01 graph ready ✔")
    yield


app = FastAPI(
    title="Scrollhouse Agentic AI",
    description="Multi-agent system for Scrollhouse content operations",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Simple healthcheck."""
    return {"status": "ok", "agent": "PS-01 Client Onboarding"}


@app.post("/webhook/onboard")
async def onboard_client(payload: OnboardingRequest):
    """
    Receive a client onboarding form submission and run the full pipeline.

    Returns the final state dict including completed_steps, errors, and flags.
    """
    logger.info(
        "═══ Onboarding triggered for '%s' by %s ═══",
        payload.brand_name,
        payload.account_manager,
    )

    # Build initial state
    initial_state = {
        "brand_name": payload.brand_name,
        "account_manager": payload.account_manager,
        "brand_category": payload.brand_category,
        "contract_start_date": payload.contract_start_date,
        "deliverable_count": payload.deliverable_count,
        "billing_contact_email": payload.billing_contact_email,
        "invoice_cycle": payload.invoice_cycle,
        # Initialise control-flow fields
        "account_manager_email": None,
        "drive_folder_id": None,
        "drive_folder_link": None,
        "notion_page_id": None,
        "notion_page_link": None,
        "airtable_record_id": None,
        "airtable_record_link": None,
        "errors": [],
        "flags": [],
        "completed_steps": [],
        "halt": False,
    }

    # Run the graph
    try:
        graph = app.state.onboarding_graph
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Unhandled error during onboarding pipeline")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Determine HTTP status based on outcome
    halted = final_state.get("halt", False)
    has_errors = bool(final_state.get("errors"))

    if halted:
        status_message = "halted"
    elif has_errors:
        status_message = "completed_with_errors"
    else:
        status_message = "completed"

    logger.info(
        "═══ Onboarding finished for '%s' — %s ═══",
        payload.brand_name,
        status_message,
    )

    return {
        "status": status_message,
        "brand_name": final_state["brand_name"],
        "completed_steps": final_state.get("completed_steps", []),
        "errors": final_state.get("errors", []),
        "flags": final_state.get("flags", []),
        "drive_folder_link": final_state.get("drive_folder_link"),
        "notion_page_link": final_state.get("notion_page_link"),
        "airtable_record_link": final_state.get("airtable_record_link"),
    }


# ── Entrypoint (for direct execution) ───────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
