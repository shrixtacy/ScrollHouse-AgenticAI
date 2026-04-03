# Scrollhouse Agentic AI — PS-01 Client Onboarding Agent

Automated client onboarding agent built with **LangGraph**, **LangChain**, **FastAPI**, and **LangSmith**. When a new client form is submitted, the agent executes a complete 8-step onboarding sequence end-to-end.

---

## Architecture

```
Trigger (n8n webhook / form submission)
    │
    ▼
POST /webhook/onboard  (FastAPI)
    │
    ▼
LangGraph State Machine
    ├─ 1. Validate Input         (halt if invalid)
    ├─ 2. Duplicate Check        (halt if duplicate in Airtable)
    ├─ 3. Send Welcome Email     (LLM-generated, flag on bounce)
    ├─ 4. Create Drive Folder    (retry once on failure)
    ├─ 5. Set Drive Permissions  (log + continue on failure)
    ├─ 6. Create Notion Hub      (retry once on failure)
    ├─ 7. Add Airtable Record    (assert complete before write)
    ├─ 8. Send Completion Email  (LLM-generated summary to AM)
    └─ 9. Log Onboarding         (structured audit log)
```

Every node is traced via **LangSmith** for full observability.

---

## Quick Start

### 1. Install dependencies

```bash
cd scrollhouse-agent
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env` and fill in all API keys (see [Manual Setup Checklist](#manual-setup-checklist) below).

### 3. Run the server

```bash
python main.py
```

Server starts at `http://localhost:8000`.

### 4. Test with mock payload

```bash
# In another terminal
python test_ps01.py
```

### 5. Send a real webhook

```bash
curl -X POST http://localhost:8000/webhook/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "Luminos Skincare",
    "account_manager": "Priya Sharma",
    "brand_category": "Skincare",
    "contract_start_date": "2026-05-10",
    "deliverable_count": 8,
    "billing_contact_email": "accounts@luminos.com",
    "invoice_cycle": "monthly"
  }'
```

---

## Project Structure

```
scrollhouse-agent/
├── main.py                              # FastAPI app, POST /webhook/onboard
├── agents/
│   └── ps01_onboarding/
│       ├── __init__.py
│       ├── graph.py                     # LangGraph graph definition
│       ├── nodes.py                     # All 9 node functions
│       ├── state.py                     # OnboardingState TypedDict
│       └── prompts.py                   # All LLM prompt templates
├── shared/
│   ├── tools/
│   │   ├── notion_client.py             # Notion API wrapper
│   │   ├── airtable_client.py           # Airtable API wrapper
│   │   ├── drive_client.py              # Google Drive API wrapper
│   │   └── email_client.py              # SendGrid email wrapper
│   ├── roster.py                        # Team member name → email mapping
│   └── logger.py                        # LangSmith tracing wrapper
├── test_ps01.py                         # Integration test script
├── .env                                 # API keys (fill in manually)
├── requirements.txt
└── README.md
```

---

## Edge Cases Handled

| # | Edge Case | Behaviour |
|---|-----------|-----------|
| 1 | Past contract date | Halt pipeline, alert AM |
| 2 | Unknown account manager | Halt pipeline, alert ops@scrollhouse.com |
| 3 | Duplicate client in Airtable | Halt pipeline, alert AM with existing record |
| 4 | Welcome email bounce | Flag AM, continue pipeline |
| 5 | Drive API failure | Retry once after 3s, alert AM if fails |
| 6 | Notion template not found | Alert AM, continue pipeline |
| 7 | Airtable partial record | Skip write, alert AM with missing fields |

---

## API Reference

### `POST /webhook/onboard`

**Request body:**
```json
{
  "brand_name": "string",
  "account_manager": "string",
  "brand_category": "string",
  "contract_start_date": "YYYY-MM-DD",
  "deliverable_count": 8,
  "billing_contact_email": "email@example.com",
  "invoice_cycle": "monthly"
}
```

**Response:**
```json
{
  "status": "completed | halted | completed_with_errors",
  "brand_name": "string",
  "completed_steps": ["validate_input", "duplicate_check", ...],
  "errors": [],
  "flags": [],
  "drive_folder_link": "https://...",
  "notion_page_link": "https://...",
  "airtable_record_link": "https://..."
}
```

### `GET /health`

Returns `{"status": "ok", "agent": "PS-01 Client Onboarding"}`.

---

## Manual Setup Checklist

Before the agent can run in production, complete these one-time setup steps:

### 1. Google Gemini API Key
- Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
- Create an API key
- Set `GEMINI_API_KEY` in `.env`

### 2. LangSmith
- Go to [smith.langchain.com](https://smith.langchain.com)
- Create a project named `scrollhouse-ps01`
- Copy your API key → `LANGSMITH_API_KEY`

### 3. Notion Setup
- Create a **Notion integration** at [notion.so/my-integrations](https://www.notion.so/my-integrations)
- Create a **master client hub template page** in your workspace
- Share the template page (and parent page) with your integration
- Copy the template page ID → `NOTION_TEMPLATE_ID`
- Copy the parent page ID → `NOTION_PARENT_PAGE_ID`
- Copy the integration token → `NOTION_API_KEY`

### 4. Airtable Setup
- Create a new base (or use existing)
- Create a table named **"Clients"** with these fields:
  | Field Name | Type |
  |------------|------|
  | brand_name | Single line text |
  | account_manager | Single line text |
  | contract_start_date | Date |
  | deliverable_count | Number |
  | invoice_date | Date |
  | billing_contact | Email |
  | google_drive_link | URL |
  | notion_page_link | URL |
  | onboarding_status | Single select (values: Complete, In Progress, Failed) |
- Generate a personal access token at [airtable.com/create/tokens](https://airtable.com/create/tokens)
- Set `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME=Clients`

### 5. Google Drive Setup
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create a project and enable the **Google Drive API**
- Create a **Service Account** and download the JSON credentials
- Save the JSON file in the project directory
- Set `GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json`
- Create a folder called **"Scrollhouse Clients"** in Google Drive
- Share the folder with the service account email (as Editor)
- Copy the folder ID from the URL → `DRIVE_PARENT_FOLDER_ID`

### 6. SendGrid Email Setup
- Create a SendGrid account at [sendgrid.com](https://sendgrid.com)
- Verify your sender identity for `ops@scrollhouse.com`
- Create an API key with Mail Send permissions
- Set `SENDGRID_API_KEY` and `EMAIL_FROM=ops@scrollhouse.com`

### 7. Team Roster
- Update `shared/roster.py` with your actual team members and their email addresses

### 8. n8n Webhook Integration (Optional)
- In your n8n workflow, add an **HTTP Request** node
- Set method to POST, URL to `http://your-server:8000/webhook/onboard`
- Map form fields to the JSON payload schema
- Connect your Google Form / Typeform trigger to this node

---

## License

Internal use — Scrollhouse Pvt. Ltd.
