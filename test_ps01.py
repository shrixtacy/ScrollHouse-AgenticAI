"""
PS-01 Onboarding Agent — Integration Test Script

Sends a mock onboarding payload to the local webhook endpoint
and prints the full execution log.

Usage:
    1. Start the FastAPI server:  python main.py
    2. In another terminal:       python test_ps01.py

The script tests multiple scenarios:
    - Happy path (valid payload)
    - Past contract date (should halt)
    - Unknown account manager (should halt)
    - Duplicate brand name (if record exists in Airtable)
"""

from __future__ import annotations

import json
import sys

import httpx

BASE_URL = "http://localhost:8000"

# ─────────────────────────────────────────────────────────────────────────────
# Test payloads
# ─────────────────────────────────────────────────────────────────────────────

HAPPY_PATH = {
    "brand_name": "Luminos Skincare",
    "account_manager": "Priya Sharma",
    "brand_category": "Skincare",
    "contract_start_date": "2026-05-10",
    "deliverable_count": 8,
    "billing_contact_email": "accounts@luminos.com",
    "invoice_cycle": "monthly",
}

PAST_DATE = {
    **HAPPY_PATH,
    "brand_name": "RetroFit Gear",
    "contract_start_date": "2024-01-01",
}

UNKNOWN_AM = {
    **HAPPY_PATH,
    "brand_name": "NovaTech Labs",
    "account_manager": "Nonexistent Person",
}

DUPLICATE_TEST = {
    **HAPPY_PATH,
    "brand_name": "Luminos Skincare",  # send twice to trigger duplicate
}


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_test(name: str, payload: dict) -> None:
    """POST payload to the webhook and print the result."""
    print(f"\n{'═' * 72}")
    print(f"  TEST: {name}")
    print(f"{'═' * 72}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    print(f"{'─' * 72}")

    try:
        resp = httpx.post(
            f"{BASE_URL}/webhook/onboard",
            json=payload,
            timeout=120.0,
        )
    except httpx.ConnectError:
        print("  ❌ Connection refused — is the server running on port 8000?")
        return

    print(f"  HTTP {resp.status_code}")

    try:
        body = resp.json()
        print(f"  Response:\n{json.dumps(body, indent=4)}")
    except Exception:
        print(f"  Raw response: {resp.text[:500]}")

    # Quick status interpretation
    status = body.get("status", "unknown") if isinstance(body, dict) else "error"
    if status == "completed":
        print("  ✅ PASSED — full onboarding completed")
    elif status == "halted":
        print(f"  🛑 HALTED — flags: {body.get('flags', [])}")
    elif status == "completed_with_errors":
        print(f"  ⚠️  COMPLETED WITH ERRORS — {len(body.get('errors', []))} error(s)")
    else:
        print(f"  ❓ Unexpected status: {status}")


def main() -> None:
    # ── Healthcheck ──────────────────────────────────────────────────────
    print("Checking server health …")
    try:
        health = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        print(f"  Server: {health.json()}")
    except httpx.ConnectError:
        print("  ❌ Server not reachable at", BASE_URL)
        print("  Start it with:  python main.py")
        sys.exit(1)

    # ── Run test scenarios ───────────────────────────────────────────────
    scenarios = [
        ("Happy Path — valid onboarding", HAPPY_PATH),
        ("Edge Case — past contract date", PAST_DATE),
        ("Edge Case — unknown account manager", UNKNOWN_AM),
    ]

    # Optionally add the duplicate test (runs the happy path brand twice)
    if "--with-duplicate" in sys.argv:
        scenarios.append(("Edge Case — duplicate client", DUPLICATE_TEST))

    for name, payload in scenarios:
        run_test(name, payload)

    print(f"\n{'═' * 72}")
    print("  All tests completed.")
    print(f"{'═' * 72}\n")


if __name__ == "__main__":
    main()
