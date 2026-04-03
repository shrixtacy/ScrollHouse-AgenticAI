"""
PS-01 Client Onboarding — LLM Prompt Templates

All prompts used by the onboarding agent are centralised here.
Prompt variables are injected at call-time via str.format().
"""

# ─────────────────────────────────────────────────────────────────────────────
# WELCOME EMAIL
# ─────────────────────────────────────────────────────────────────────────────

WELCOME_EMAIL_SYSTEM = (
    "You are writing a professional client welcome email for Scrollhouse, "
    "a short-form video content agency."
)

WELCOME_EMAIL_USER = """Write a welcome email to the client at {brand_name}.
- Account manager handling this account: {account_manager}
- Contract start date: {contract_start_date}
- Monthly deliverables committed: {deliverable_count} pieces of content
- Kickoff calendar link: {calendar_link}

Tone: warm, professional, organized. Max 180 words.
Structure:
1. Welcome + team intro (2 sentences, do NOT use the phrase "excited to have you aboard")
2. What to expect in the first two weeks (3 bullet points, specific to content workflow)
3. Kickoff call CTA with the calendar link
4. Sign-off from {account_manager}"""


# ─────────────────────────────────────────────────────────────────────────────
# COMPLETION SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

COMPLETION_SUMMARY_SYSTEM = (
    "You are writing an internal ops summary email for a Scrollhouse account manager."
)

COMPLETION_SUMMARY_USER = """Write a short completion summary to {account_manager} confirming that \
{brand_name} has been fully onboarded.

Include:
- Confirmation that all 4 systems are set up (Drive, Notion, Airtable, welcome email)
- Google Drive link: {drive_link}
- Notion page link: {notion_link}
- Airtable record link: {airtable_link}
- Any steps that encountered issues (from errors list: {errors})

Tone: concise ops update. Max 120 words. No fluff."""


# ─────────────────────────────────────────────────────────────────────────────
# ALERT TEMPLATES (plain text — no LLM call needed)
# ─────────────────────────────────────────────────────────────────────────────

ALERT_PAST_CONTRACT_DATE = (
    "⚠️ Onboarding halted for {brand_name}: contract start date {contract_start_date} "
    "appears to be in the past. Please verify and resubmit."
)

ALERT_UNKNOWN_AM = (
    "⚠️ Onboarding halted for {brand_name}: account manager '{account_manager}' "
    "was not found in the team roster. Please verify and resubmit."
)

ALERT_DUPLICATE_CLIENT = (
    "⚠️ Onboarding halted for {brand_name}: a record for this brand already exists "
    "in Airtable (record ID: {existing_id}). Duplicate onboarding has been prevented."
)

ALERT_EMAIL_BOUNCE = (
    "⚠️ Welcome email to {billing_contact_email} for {brand_name} bounced. "
    "Please verify the address and resend manually."
)

ALERT_DRIVE_FAILURE = (
    "⚠️ Google Drive folder creation failed for {brand_name} after two attempts. "
    "Please create the folder manually under 'Scrollhouse Clients' with subfolders: "
    "Briefs, Scripts, Approved, Footage, Reports."
)

ALERT_NOTION_FAILURE = (
    "⚠️ Notion client hub creation failed for {brand_name}. "
    "Template ID may be invalid or missing. Please create the page manually."
)

ALERT_AIRTABLE_PARTIAL = (
    "⚠️ Airtable record write skipped for {brand_name}: the following fields are "
    "missing — {missing_fields}. Please add the record manually."
)
