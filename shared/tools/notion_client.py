"""
Notion API Client

Provides helpers for duplicating a template page and populating
properties for the Scrollhouse client hub.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from math import ceil

from notion_client import Client as NotionSDKClient
from notion_client.errors import APIResponseError

from shared.logger import logger


class NotionClientError(Exception):
    """Raised when a Notion API call fails."""


def _get_client() -> NotionSDKClient:
    """Return an authenticated Notion SDK client."""
    return NotionSDKClient(auth=os.environ["NOTION_API_KEY"])


def _generate_content_calendar(
    start_date_str: str, deliverable_count: int
) -> list[dict]:
    """
    Generate evenly-spaced placeholder content slots for the first month.

    Returns a list of dicts:
        [{"title": "Deliverable 1", "date": "2025-04-13"}, ...]
    """
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    days_in_month = 30
    interval = days_in_month / max(deliverable_count, 1)

    calendar: list[dict] = []
    for i in range(deliverable_count):
        slot_date = start + timedelta(days=ceil(interval * (i + 1)))
        calendar.append(
            {
                "title": f"Deliverable {i + 1}",
                "date": slot_date.strftime("%Y-%m-%d"),
            }
        )
    return calendar


def create_client_hub(
    brand_name: str,
    account_manager: str,
    contract_start_date: str,
    deliverable_count: int,
) -> dict:
    """
    Duplicate the master Notion template and populate it for a new client.

    Environment variables required:
        NOTION_TEMPLATE_ID   — page ID of the master template
        NOTION_PARENT_PAGE_ID — parent page under which the new page is created

    Returns
    -------
    dict
        ``{"page_id": str, "page_link": str}``

    Raises
    ------
    NotionClientError
        If the template is missing or the API call fails.
    """
    template_id = os.getenv("NOTION_TEMPLATE_ID")
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")

    if not template_id:
        raise NotionClientError(
            "NOTION_TEMPLATE_ID environment variable is not set."
        )

    notion = _get_client()

    # ── Fetch template (always fresh, never cached) ──────────────────────
    try:
        template = notion.pages.retrieve(page_id=template_id)
    except APIResponseError as exc:
        raise NotionClientError(
            f"Notion template {template_id} not found (404 or auth error): {exc}"
        ) from exc

    # ── Build content calendar ───────────────────────────────────────────
    calendar = _generate_content_calendar(contract_start_date, deliverable_count)
    calendar_text = "\n".join(
        f"• {slot['title']} — {slot['date']}" for slot in calendar
    )

    # ── Create new page under parent ─────────────────────────────────────
    try:
        new_page = notion.pages.create(
            parent={"page_id": parent_page_id} if parent_page_id else {"page_id": template_id},
            properties={
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": f"{brand_name} — Client Hub",
                            }
                        }
                    ]
                },
            },
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Client Details"}}]
                    },
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"Brand: {brand_name}"}}
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"Account Manager: {account_manager}"}}
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"Contract Start: {contract_start_date}"}}
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"Deliverables/Month: {deliverable_count}"}}
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Content Calendar — Month 1"}}]
                    },
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": calendar_text}}
                        ]
                    },
                },
            ],
        )

        page_id = new_page["id"]
        page_url = new_page.get("url", f"https://notion.so/{page_id.replace('-', '')}")

        logger.info("Notion client hub created: %s → %s", brand_name, page_url)
        return {"page_id": page_id, "page_link": page_url}

    except APIResponseError as exc:
        raise NotionClientError(
            f"Failed to create Notion page for {brand_name}: {exc}"
        ) from exc
