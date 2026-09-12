**OpsAgent — Autonomous IT/HR Operations Agent**

An autonomous backend agent that automates employee onboarding and offboarding operations for a company's SaaS/IT stack. It scans inbound HR emails, detects onboarding and offboarding signals using an LLM (Groq's `llama-3.1-8b-instant`), automatically provisions or revokes access to company tools, flags unused ("wasted") software licenses, and generates compliance reports and stakeholder notification emails — all through a FastAPI backend.

## Features

- **Email signal detection** — Scans a mock inbox and classifies each email as an onboarding signal, an offboarding signal, or neither, using an LLM prompt with a JSON-only response contract (with a keyword-based fallback if the LLM call fails).
- **Automatic access mapping** — Resolves a new hire's role to a recommended set of SaaS tools (e.g. Slack, GitHub, Figma, HubSpot) and calculates the monthly cost of provisioning them.
- **Offboarding & deprovisioning** — Revokes an employee's tool access in one action and reports the resulting monthly cost savings.
- **SaaS waste detection** — Flags licenses that haven't been used in 30+ days and totals the recoverable monthly spend.
- **Compliance reporting** — Generates a detailed IT compliance/audit report (security posture, risk mitigation, and cost savings) for each offboarding event.
- **Stakeholder notifications** — Drafts separate notification emails for IT, Finance, and HR teams following any access change.

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI + Uvicorn |
| LLM provider | Groq (`llama-3.1-8b-instant`) |
| Config | python-dotenv |
| Data | In-memory mock employee registry + JSON mock emails |
| Optional | Streamlit, Google API client libraries (for future integrations) |

## Project Structure

```
agent-ops-2/
├── server.py            # FastAPI app — all API routes and agent logic
├── test_groq.py          # Standalone script for testing the Groq API connection
├── requirements.txt       # Python dependencies
├── .env.example           # Template for required environment variables
├── src/
│   └── data/
│       └── mock_emails.json   # Sample inbox used by the /api/scan endpoint
└── reports/               # Generated compliance reports / output artifacts
```

## Getting Started

### Prerequisites
- Python 3.9+
- A [Groq API key](https://console.groq.com)

### Installation

```bash
git clone https://github.com/harisazam11/agent-ops-2.git
cd agent-ops-2
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and add your Groq API key:

```bash
cp .env.example .env
```

```env
GROQ_API_KEY=your_groq_api_key_here
```

> ⚠️ **Security note:** a `.env` file currently appears to be committed in this repository. Environment files containing real API keys should never be committed to version control — add `.env` to `.gitignore` and rotate any key that may have been exposed.

### Running the server

```bash
uvicorn server:app --reload
```

The API will be available at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/employees` | Returns the current employee registry and their tool access. |
| `POST` | `/api/scan` | Scans mock inbox emails and returns detected onboarding/offboarding signals. |
| `POST` | `/api/map-access` | Resolves and returns the SaaS tools (and cost) an employee should have, provisioning defaults for new hires. |
| `POST` | `/api/execute-actions` | Revokes tool access — either for a single offboarded employee or a batch of flagged waste cancellations. |
| `POST` | `/api/generate-report` | Generates an IT compliance/audit report for an offboarding event. |
| `POST` | `/api/stakeholder-emails` | Generates notification emails for IT, Finance, and HR stakeholders. |
| `POST` | `/api/waste-scan` | Flags SaaS licenses unused for 30+ days and totals the recoverable spend. |

### Example: scanning for HR signals

```bash
curl -X POST http://127.0.0.1:8000/api/scan
```

### Example: mapping access for an employee

```bash
curl -X POST http://127.0.0.1:8000/api/map-access \
  -H "Content-Type: application/json" \
  -d '{"email": "zara.ahmed@techhub.pk"}'
```

## Notes

- The employee registry, SaaS cost table, and tool-usage data are currently mocked in `server.py` for demonstration purposes. Replace these with real data sources (an HRIS, an identity provider, or a usage-analytics API) for production use.
- LLM-dependent endpoints (`/api/scan`, `/api/generate-report`, `/api/stakeholder-emails`) include a fallback path in case the Groq API call fails, so the agent degrades gracefully rather than erroring out.

## License

No license file is currently included in this repository. Add a `LICENSE` file to clarify usage terms for other contributors.
