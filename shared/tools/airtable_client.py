"""
Airtable API Client

Provides helpers for querying and creating records in the
Scrollhouse "Clients" table.
"""

from __future__ import annotations

import os

from pyairtable import Api
from pyairtable.formulas import match

from shared.logger import logger


class AirtableClientError(Exception):
    """Raised when an Airtable API call fails."""


def _get_table():
    """Return an authenticated pyairtable Table handle."""
    api = Api(os.environ["AIRTABLE_API_KEY"])
    base_id = os.environ["AIRTABLE_BASE_ID"]
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "Clients")
    return api.table(base_id, table_name)


# ── Duplicate check ──────────────────────────────────────────────────────────

def find_client_by_brand(brand_name: str) -> dict | None:
    """
    Search for an existing Airtable record matching *brand_name*.

    Returns
    -------
    dict | None
        The first matching record dict, or ``None`` if no match.
    """
    table = _get_table()
    try:
        formula = match({"brand_name": brand_name})
        records = table.all(formula=formula)
        if records:
            record = records[0]
            logger.info(
                "Airtable duplicate found for '%s': %s",
                brand_name,
                record["id"],
            )
            return record
        return None
    except Exception as exc:
        raise AirtableClientError(
            f"Airtable search failed for '{brand_name}': {exc}"
        ) from exc


# ── Record creation ──────────────────────────────────────────────────────────

REQUIRED_FIELDS = [
    "brand_name",
    "account_manager",
    "contract_start_date",
    "deliverable_count",
    "invoice_date",
    "billing_contact",
    "google_drive_link",
    "notion_page_link",
    "onboarding_status",
]


def create_client_record(fields: dict) -> dict:
    """
    Create a new record in the Clients table.

    Parameters
    ----------
    fields : dict
        Must contain ALL keys listed in ``REQUIRED_FIELDS``.

    Returns
    -------
    dict
        ``{"record_id": str, "record_link": str}``

    Raises
    ------
    AirtableClientError
        If any required field is missing/None, or if the API call fails.
    """
    # ── Partial-record prevention ────────────────────────────────────────
    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    if missing:
        raise AirtableClientError(
            f"Cannot write partial record — missing fields: {', '.join(missing)}"
        )

    # ── Map internal field names to Airtable column names ────────────────
    airtable_fields = {
        "brand_name": fields["brand_name"],
        "account_manager": fields["account_manager"],
        "contract_start_date": fields["contract_start_date"],
        "deliverable_count": int(fields["deliverable_count"]),
        "invoice_date": fields["invoice_date"],
        "billing_contact": fields["billing_contact"],
        "google_drive_link": fields["google_drive_link"],
        "notion_page_link": fields["notion_page_link"],
        "onboarding_status": fields["onboarding_status"],
    }

    table = _get_table()
    try:
        record = table.create(airtable_fields)
        record_id = record["id"]
        base_id = os.environ["AIRTABLE_BASE_ID"]
        table_id = os.environ.get("AIRTABLE_TABLE_NAME", "Clients")
        # Build a direct Airtable record URL
        record_link = (
            f"https://airtable.com/{base_id}/{table_id}/{record_id}"
        )
        logger.info("Airtable record created: %s", record_id)
        return {"record_id": record_id, "record_link": record_link}
    except Exception as exc:
        raise AirtableClientError(
            f"Airtable record creation failed: {exc}"
        ) from exc
