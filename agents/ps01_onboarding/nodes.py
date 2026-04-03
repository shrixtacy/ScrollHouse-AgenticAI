"""
PS-01 Client Onboarding — LangGraph Node Functions

Each function receives the full OnboardingState and returns a partial-state
update dict.  Error handling follows the spec:

    - validate_input / duplicate_check → halt on failure
    - send_welcome_email → flag + continue on bounce
    - create_drive_folder / create_notion_hub / add_airtable_record → retry once, alert AM
    - set_drive_permissions → log + continue
    - send_completion_summary / log_onboarding → always continue
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

from agents.ps01_onboarding.prompts import (
    ALERT_AIRTABLE_PARTIAL,
    ALERT_DRIVE_FAILURE,
    ALERT_DUPLICATE_CLIENT,
    ALERT_EMAIL_BOUNCE,
    ALERT_NOTION_FAILURE,
    ALERT_PAST_CONTRACT_DATE,
    ALERT_UNKNOWN_AM,
    COMPLETION_SUMMARY_SYSTEM,
    COMPLETION_SUMMARY_USER,
    WELCOME_EMAIL_SYSTEM,
    WELCOME_EMAIL_USER,
)
from agents.ps01_onboarding.state import OnboardingState
from shared.logger import logger, traced_node
from shared.roster import TEAM_ROSTER, get_am_email
from shared.tools.airtable_client import (
    AirtableClientError,
    create_client_record,
    find_client_by_brand,
)
from shared.tools.drive_client import (
    DriveClientError,
    create_client_folder_structure,
    set_permission,
)
from shared.tools.email_client import EmailBounceError, EmailClientError, send_email
from shared.tools.notion_client import NotionClientError, create_client_hub


# ── Helpers ──────────────────────────────────────────────────────────────────

def _llm():
    """Return a configured Gemini instance (lazy import to avoid startup hang)."""
    from langchain_google_genai import ChatGoogleGenerativeAI  # noqa: PLC0415
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.4,
        max_tokens=512,
    )


def _messages(system: str, human: str):
    """Build LangChain message list (lazy import)."""
    from langchain_core.messages import HumanMessage, SystemMessage  # noqa: PLC0415
    return [SystemMessage(content=system), HumanMessage(content=human)]


def _send_alert(to_email: str, subject: str, body: str) -> None:
    """Best-effort alert email. Failures are logged but never propagated."""
    try:
        send_email(to_email, subject, f"<p>{body}</p>")
    except Exception as exc:
        logger.warning("Alert email to %s failed: %s", to_email, exc)


# ═════════════════════════════════════════════════════════════════════════════
# NODE 1 — Validate Input
# ═════════════════════════════════════════════════════════════════════════════

REQUIRED_INPUT_FIELDS = [
    "brand_name",
    "account_manager",
    "brand_category",
    "contract_start_date",
    "deliverable_count",
    "billing_contact_email",
    "invoice_cycle",
]


@traced_node("validate_input")
def validate_input(state: OnboardingState) -> dict:
    """
    Validate that all required fields are present and business rules are met.

    Halt conditions:
        - Missing / empty required fields
        - contract_start_date is in the past
        - account_manager not found in the team roster
    """
    errors: list[dict] = []
    flags: list[str] = []

    # ── Check required fields ────────────────────────────────────────────
    for field in REQUIRED_INPUT_FIELDS:
        value = state.get(field)  # type: ignore[arg-type]
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(
                {
                    "step": "validate_input",
                    "error": f"Missing required field: {field}",
                    "action_taken": "halted",
                }
            )
            flags.append("missing_field")

    if flags:
        return {"errors": errors, "flags": flags, "halt": True}

    # ── Contract date must not be in the past ────────────────────────────
    try:
        start_date = datetime.strptime(state["contract_start_date"], "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        if start_date < today:
            flags.append("past_contract_date")
            errors.append(
                {
                    "step": "validate_input",
                    "error": f"Contract start date {state['contract_start_date']} is in the past",
                    "action_taken": "halted",
                }
            )
            # Alert AM if we can resolve their email
            am_email = get_am_email(state["account_manager"])
            if am_email:
                _send_alert(
                    am_email,
                    f"Onboarding halted — {state['brand_name']}",
                    ALERT_PAST_CONTRACT_DATE.format(**state),
                )
            return {"errors": errors, "flags": flags, "halt": True}
    except ValueError:
        errors.append(
            {
                "step": "validate_input",
                "error": f"Invalid date format: {state['contract_start_date']}",
                "action_taken": "halted",
            }
        )
        return {"errors": errors, "flags": ["invalid_date"], "halt": True}

    # ── Account manager must be in roster ────────────────────────────────
    am_email = get_am_email(state["account_manager"])
    if am_email is None:
        flags.append("unknown_am")
        errors.append(
            {
                "step": "validate_input",
                "error": f"Account manager '{state['account_manager']}' not in roster",
                "action_taken": "halted",
            }
        )
        _send_alert(
            "ops@scrollhouse.com",
            f"Onboarding halted — unknown AM for {state['brand_name']}",
            ALERT_UNKNOWN_AM.format(**state),
        )
        return {
            "errors": errors,
            "flags": flags,
            "halt": True,
        }

    logger.info("Input validated for '%s'", state["brand_name"])
    return {
        "account_manager_email": am_email,
        "completed_steps": ["validate_input"],
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 2 — Duplicate Check
# ═════════════════════════════════════════════════════════════════════════════

@traced_node("duplicate_check")
def duplicate_check(state: OnboardingState) -> dict:
    """Query Airtable for an existing record with the same brand_name."""
    try:
        existing = find_client_by_brand(state["brand_name"])
    except AirtableClientError as exc:
        logger.error("Airtable lookup failed: %s", exc)
        # Can't confirm uniqueness — safe to continue but log the error
        return {
            "errors": [
                {
                    "step": "duplicate_check",
                    "error": str(exc),
                    "action_taken": "continued_with_warning",
                }
            ],
            "completed_steps": ["duplicate_check"],
        }

    if existing:
        existing_id = existing["id"]
        am_email = state.get("account_manager_email") or get_am_email(state["account_manager"])
        if am_email:
            _send_alert(
                am_email,
                f"Duplicate client — {state['brand_name']}",
                ALERT_DUPLICATE_CLIENT.format(
                    brand_name=state["brand_name"],
                    existing_id=existing_id,
                ),
            )
        return {
            "errors": [
                {
                    "step": "duplicate_check",
                    "error": f"Duplicate found: {existing_id}",
                    "action_taken": "halted",
                }
            ],
            "flags": ["duplicate_client"],
            "halt": True,
        }

    logger.info("No duplicate found for '%s'", state["brand_name"])
    return {"completed_steps": ["duplicate_check"]}


# ═════════════════════════════════════════════════════════════════════════════
# NODE 3 — Send Welcome Email
# ═════════════════════════════════════════════════════════════════════════════

@traced_node("send_welcome_email")
def send_welcome_email(state: OnboardingState) -> dict:
    """Generate a personalised welcome email via LLM and send it."""
    calendar_link = os.getenv("CALENDAR_LINK", "https://calendly.com/scrollhouse/kickoff")

    # ── Generate email body via Claude ───────────────────────────────────
    llm = _llm()
    response = llm.invoke(
        [
            SystemMessage(content=WELCOME_EMAIL_SYSTEM),
            HumanMessage(
                content=WELCOME_EMAIL_USER.format(
                    brand_name=state["brand_name"],
                    account_manager=state["account_manager"],
                    contract_start_date=state["contract_start_date"],
                    deliverable_count=state["deliverable_count"],
                    calendar_link=calendar_link,
                )
            ),
        ]
    )
    email_body = response.content
    # Convert newlines to HTML paragraphs for email rendering
    html_body = email_body.replace("\n\n", "</p><p>").replace("\n", "<br>")
    html_body = f"<p>{html_body}</p>"

    # ── Send email ───────────────────────────────────────────────────────
    try:
        send_email(
            to_email=state["billing_contact_email"],
            subject=f"Welcome to Scrollhouse — {state['brand_name']}",
            body_html=html_body,
        )
        logger.info("Welcome email sent to %s", state["billing_contact_email"])
        return {"completed_steps": ["send_welcome_email"]}

    except EmailBounceError:
        logger.warning("Welcome email bounced: %s", state["billing_contact_email"])
        am_email = state.get("account_manager_email")
        if am_email:
            _send_alert(
                am_email,
                f"Email bounce — {state['brand_name']}",
                ALERT_EMAIL_BOUNCE.format(
                    billing_contact_email=state["billing_contact_email"],
                    brand_name=state["brand_name"],
                ),
            )
        return {
            "errors": [
                {
                    "step": "send_welcome_email",
                    "error": f"Email to {state['billing_contact_email']} bounced",
                    "action_taken": "alerted_am_continuing",
                }
            ],
            "completed_steps": ["send_welcome_email_bounced"],
        }

    except EmailClientError as exc:
        logger.error("Welcome email failed: %s", exc)
        am_email = state.get("account_manager_email")
        if am_email:
            _send_alert(
                am_email,
                f"Email failure — {state['brand_name']}",
                ALERT_EMAIL_BOUNCE.format(
                    billing_contact_email=state["billing_contact_email"],
                    brand_name=state["brand_name"],
                ),
            )
        return {
            "errors": [
                {
                    "step": "send_welcome_email",
                    "error": str(exc),
                    "action_taken": "alerted_am_continuing",
                }
            ],
            "completed_steps": ["send_welcome_email_failed"],
        }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 4 — Create Google Drive Folder
# ═════════════════════════════════════════════════════════════════════════════

@traced_node("create_drive_folder")
def create_drive_folder(state: OnboardingState) -> dict:
    """Create the client folder structure. Retry once on failure."""
    for attempt in range(2):
        try:
            result = create_client_folder_structure(
                brand_name=state["brand_name"],
                contract_start_date=state["contract_start_date"],
            )
            return {
                "drive_folder_id": result["folder_id"],
                "drive_folder_link": result["folder_link"],
                "completed_steps": ["create_drive_folder"],
            }
        except DriveClientError as exc:
            logger.warning(
                "Drive attempt %d/2 failed: %s", attempt + 1, exc
            )
            if attempt == 0:
                time.sleep(3)  # wait before retry

    # Both attempts failed
    am_email = state.get("account_manager_email")
    if am_email:
        _send_alert(
            am_email,
            f"Drive folder failed — {state['brand_name']}",
            ALERT_DRIVE_FAILURE.format(brand_name=state["brand_name"]),
        )
    return {
        "errors": [
            {
                "step": "create_drive_folder",
                "error": "Drive API failed after 2 attempts",
                "action_taken": "alerted_am_manual_required",
            }
        ],
        "completed_steps": ["create_drive_folder_failed"],
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 5 — Set Drive Permissions
# ═════════════════════════════════════════════════════════════════════════════

@traced_node("set_drive_permissions")
def set_drive_permissions(state: OnboardingState) -> dict:
    """Grant commenter to billing contact, editor to AM."""
    folder_id = state.get("drive_folder_id")
    if not folder_id:
        logger.warning("Skipping permissions — no Drive folder ID")
        return {
            "errors": [
                {
                    "step": "set_drive_permissions",
                    "error": "No folder_id available (Drive step may have failed)",
                    "action_taken": "skipped",
                }
            ],
        }

    permission_errors: list[dict] = []

    # Billing contact → commenter
    try:
        set_permission(folder_id, state["billing_contact_email"], role="commenter")
    except DriveClientError as exc:
        logger.error("Permission for billing contact failed: %s", exc)
        permission_errors.append(
            {
                "step": "set_drive_permissions",
                "error": f"Billing contact permission failed: {exc}",
                "action_taken": "logged_continuing",
            }
        )

    # Account manager → editor
    am_email = state.get("account_manager_email")
    if am_email:
        try:
            set_permission(folder_id, am_email, role="writer")
        except DriveClientError as exc:
            logger.error("Permission for AM failed: %s", exc)
            permission_errors.append(
                {
                    "step": "set_drive_permissions",
                    "error": f"AM permission failed: {exc}",
                    "action_taken": "logged_continuing",
                }
            )

    result: dict = {"completed_steps": ["set_drive_permissions"]}
    if permission_errors:
        result["errors"] = permission_errors
    return result


# ═════════════════════════════════════════════════════════════════════════════
# NODE 6 — Create Notion Client Hub
# ═════════════════════════════════════════════════════════════════════════════

@traced_node("create_notion_hub")
def create_notion_hub(state: OnboardingState) -> dict:
    """Duplicate the Notion template and populate it. Retry once."""
    for attempt in range(2):
        try:
            result = create_client_hub(
                brand_name=state["brand_name"],
                account_manager=state["account_manager"],
                contract_start_date=state["contract_start_date"],
                deliverable_count=state["deliverable_count"],
            )
            return {
                "notion_page_id": result["page_id"],
                "notion_page_link": result["page_link"],
                "completed_steps": ["create_notion_hub"],
            }
        except NotionClientError as exc:
            logger.warning("Notion attempt %d/2 failed: %s", attempt + 1, exc)
            if attempt == 0:
                time.sleep(3)

    # Both attempts failed
    am_email = state.get("account_manager_email")
    if am_email:
        _send_alert(
            am_email,
            f"Notion hub failed — {state['brand_name']}",
            ALERT_NOTION_FAILURE.format(brand_name=state["brand_name"]),
        )
    return {
        "errors": [
            {
                "step": "create_notion_hub",
                "error": "Notion API failed after 2 attempts",
                "action_taken": "alerted_am_manual_required",
            }
        ],
        "completed_steps": ["create_notion_hub_failed"],
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 7 — Add Airtable Record
# ═════════════════════════════════════════════════════════════════════════════

@traced_node("add_airtable_record")
def add_airtable_record(state: OnboardingState) -> dict:
    """Write a complete client record to Airtable. Retry once."""
    # Compute invoice_date = contract_start_date + 30 days
    try:
        start = datetime.strptime(state["contract_start_date"], "%Y-%m-%d")
        invoice_date = (start + timedelta(days=30)).strftime("%Y-%m-%d")
    except ValueError:
        invoice_date = None

    fields = {
        "brand_name": state.get("brand_name"),
        "account_manager": state.get("account_manager"),
        "contract_start_date": state.get("contract_start_date"),
        "deliverable_count": state.get("deliverable_count"),
        "invoice_date": invoice_date,
        "billing_contact": state.get("billing_contact_email"),
        "google_drive_link": state.get("drive_folder_link"),
        "notion_page_link": state.get("notion_page_link"),
        "onboarding_status": "Complete",
    }

    # ── Partial-record prevention (check before even attempting) ─────────
    missing = [k for k, v in fields.items() if not v]
    if missing:
        logger.warning("Airtable write skipped — missing: %s", missing)
        am_email = state.get("account_manager_email")
        if am_email:
            _send_alert(
                am_email,
                f"Airtable record incomplete — {state['brand_name']}",
                ALERT_AIRTABLE_PARTIAL.format(
                    brand_name=state["brand_name"],
                    missing_fields=", ".join(missing),
                ),
            )
        return {
            "errors": [
                {
                    "step": "add_airtable_record",
                    "error": f"Missing fields: {', '.join(missing)}",
                    "action_taken": "skipped_alerted_am",
                }
            ],
            "completed_steps": ["add_airtable_record_skipped"],
        }

    # ── Attempt write (retry once) ──────────────────────────────────────
    for attempt in range(2):
        try:
            result = create_client_record(fields)
            return {
                "airtable_record_id": result["record_id"],
                "airtable_record_link": result["record_link"],
                "completed_steps": ["add_airtable_record"],
            }
        except AirtableClientError as exc:
            logger.warning("Airtable attempt %d/2 failed: %s", attempt + 1, exc)
            if attempt == 0:
                time.sleep(3)

    # Both attempts failed
    am_email = state.get("account_manager_email")
    if am_email:
        _send_alert(
            am_email,
            f"Airtable write failed — {state['brand_name']}",
            f"Airtable record creation failed for {state['brand_name']} after two attempts. "
            f"Please add the record manually.",
        )
    return {
        "errors": [
            {
                "step": "add_airtable_record",
                "error": "Airtable write failed after 2 attempts",
                "action_taken": "alerted_am_manual_required",
            }
        ],
        "completed_steps": ["add_airtable_record_failed"],
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 8 — Send Completion Summary
# ═════════════════════════════════════════════════════════════════════════════

@traced_node("send_completion_summary")
def send_completion_summary(state: OnboardingState) -> dict:
    """Generate and send the internal ops summary to the account manager."""
    am_email = state.get("account_manager_email")
    if not am_email:
        return {
            "errors": [
                {
                    "step": "send_completion_summary",
                    "error": "No AM email — cannot send summary",
                    "action_taken": "skipped",
                }
            ],
        }

    # ── Generate summary via LLM ─────────────────────────────────────────
    llm = _llm()
    response = llm.invoke(
        [
            SystemMessage(content=COMPLETION_SUMMARY_SYSTEM),
            HumanMessage(
                content=COMPLETION_SUMMARY_USER.format(
                    account_manager=state["account_manager"],
                    brand_name=state["brand_name"],
                    drive_link=state.get("drive_folder_link", "N/A"),
                    notion_link=state.get("notion_page_link", "N/A"),
                    airtable_link=state.get("airtable_record_link", "N/A"),
                    errors=state.get("errors", []),
                )
            ),
        ]
    )
    summary_body = response.content
    html_body = summary_body.replace("\n\n", "</p><p>").replace("\n", "<br>")
    html_body = f"<p>{html_body}</p>"

    try:
        send_email(
            to_email=am_email,
            subject=f"Onboarding Complete — {state['brand_name']}",
            body_html=html_body,
        )
        return {"completed_steps": ["send_completion_summary"]}
    except EmailClientError as exc:
        logger.error("Completion summary email failed: %s", exc)
        return {
            "errors": [
                {
                    "step": "send_completion_summary",
                    "error": str(exc),
                    "action_taken": "logged_continuing",
                }
            ],
            "completed_steps": ["send_completion_summary_failed"],
        }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 9 — Log Onboarding
# ═════════════════════════════════════════════════════════════════════════════

@traced_node("log_onboarding")
def log_onboarding(state: OnboardingState) -> dict:
    """
    Final node: log a structured onboarding summary.

    This is persisted via LangSmith tracing and standard logger output.
    """
    summary = {
        "brand_name": state["brand_name"],
        "account_manager": state["account_manager"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "completed_steps": state.get("completed_steps", []),
        "errors": state.get("errors", []),
        "flags": state.get("flags", []),
        "halt": state.get("halt", False),
        "drive_folder_link": state.get("drive_folder_link"),
        "notion_page_link": state.get("notion_page_link"),
        "airtable_record_link": state.get("airtable_record_link"),
    }

    logger.info(
        "═══ ONBOARDING LOG ═══\n%s",
        "\n".join(f"  {k}: {v}" for k, v in summary.items()),
    )
    return {"completed_steps": ["log_onboarding"]}
