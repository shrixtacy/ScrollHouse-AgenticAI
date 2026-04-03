"""
Google Drive API Client

Provides helpers for creating folders and setting permissions
inside the "Scrollhouse Clients" parent folder.
"""

from __future__ import annotations

import os
from typing import Sequence

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared.logger import logger

SCOPES = ["https://www.googleapis.com/auth/drive"]


class DriveClientError(Exception):
    """Raised when a Drive API call fails."""


def _get_service():
    """Build and return an authenticated Drive v3 service instance."""
    creds_path = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    credentials = service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


# ── Folder creation ──────────────────────────────────────────────────────────

def create_folder(
    name: str,
    parent_id: str | None = None,
) -> dict:
    """
    Create a single folder in Drive.

    Returns
    -------
    dict
        ``{"id": str, "webViewLink": str}``
    """
    parent = parent_id or os.environ["DRIVE_PARENT_FOLDER_ID"]
    service = _get_service()

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent],
    }

    try:
        folder = (
            service.files()
            .create(body=metadata, fields="id, webViewLink")
            .execute()
        )
        logger.info("Drive folder created: %s (%s)", name, folder["id"])
        return {"id": folder["id"], "webViewLink": folder["webViewLink"]}
    except HttpError as exc:
        raise DriveClientError(f"Failed to create folder '{name}': {exc}") from exc


def create_client_folder_structure(
    brand_name: str,
    contract_start_date: str,
    subfolders: Sequence[str] = ("Briefs", "Scripts", "Approved", "Footage", "Reports"),
) -> dict:
    """
    Create the top-level client folder and all subfolders.

    Folder name format: ``{brand_name} — {contract_start_date}``

    Returns
    -------
    dict
        ``{"folder_id": str, "folder_link": str, "subfolder_ids": dict[str, str]}``
    """
    top_name = f"{brand_name} — {contract_start_date}"
    top = create_folder(top_name)

    subfolder_ids: dict[str, str] = {}
    for sub in subfolders:
        result = create_folder(sub, parent_id=top["id"])
        subfolder_ids[sub] = result["id"]

    logger.info(
        "Full folder structure created for '%s' with %d subfolders",
        brand_name,
        len(subfolder_ids),
    )
    return {
        "folder_id": top["id"],
        "folder_link": top["webViewLink"],
        "subfolder_ids": subfolder_ids,
    }


# ── Permissions ──────────────────────────────────────────────────────────────

def set_permission(
    file_id: str,
    email: str,
    role: str = "commenter",
) -> None:
    """
    Grant *role* permission on *file_id* to *email*.

    Parameters
    ----------
    file_id : str
        The Drive file/folder ID.
    email : str
        Recipient email address.
    role : str
        One of ``"reader"``, ``"commenter"``, ``"writer"``.
    """
    service = _get_service()
    body = {"type": "user", "role": role, "emailAddress": email}

    try:
        service.permissions().create(
            fileId=file_id,
            body=body,
            sendNotificationEmail=False,
        ).execute()
        logger.info("Permission set: %s → %s on %s", email, role, file_id)
    except HttpError as exc:
        raise DriveClientError(
            f"Failed to set {role} for {email} on {file_id}: {exc}"
        ) from exc
