import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

REPORT_SYSTEM_PROMPT = (
    "You are a compliance and audit report writer for TechHub Pvt Ltd, "
    "a Pakistani tech company. Generate a professional, formal audit report in English. "
    "Use PKR for all costs. Be specific, structured, and professional."
)

EMAILS_SYSTEM_PROMPT = (
    "You are an operations agent for TechHub Pvt Ltd, a Pakistani tech company. "
    "Generate formal stakeholder notification emails. "
    "Return ONLY a raw JSON object with no markdown and no explanation with these exact keys:\n"
    "- it_email: a formal email to IT team about access revocation\n"
    "- finance_email: a formal email to Finance team about licence cancellations and PKR savings\n"
    "- hr_email: a formal email to HR confirming offboarding completion\n\n"
    "All emails must:\n"
    "- Be from ops-agent@techhub.pk\n"
    "- Reference the employee by their Pakistani name\n"
    "- Mention specific tools and PKR amounts\n"
    "- Be professional but concise\n"
    "- Reference TechHub Pvt Ltd throughout\n"
    "IMPORTANT: Return valid JSON only. Do not include any newlines or control characters inside string values."
)


def _strip_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _clean_json_string(text: str) -> str:
    # Remove control characters that break JSON parsing
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text


def _generate_content(prompt: str, max_retries: int = 5) -> str:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                time.sleep(35)
            else:
                raise


def generate_report(signal: dict, mapped_access: dict, actions: dict) -> str:
    tools_revoked = mapped_access.get("tools", [])
    licenses_cancelled = [
        action["tool"]
        for action in actions.get("actions_taken", [])
        if action.get("license_cancelled", True)
    ]
    timestamps = [
        action.get("timestamp", "N/A")
        for action in actions.get("actions_taken", [])
    ]
    total_savings = actions.get("total_saved_pkr", mapped_access.get("total_monthly_cost_pkr", 0))

    user_message = f"""Generate a full audit report for the following offboarding case at TechHub Pvt Ltd.

Employee Name: {signal.get("employee_name")}
Employee Email: {signal.get("employee_email")}
Offboarding Reason: {signal.get("reason")}

Tools Access Revoked From:
{chr(10).join(f"- {tool}" for tool in tools_revoked)}

Licenses Cancelled:
{chr(10).join(f"- {tool}" for tool in licenses_cancelled)}

Total Monthly Savings: PKR {total_savings}

Action Timestamps:
{chr(10).join(f"- {ts}" for ts in timestamps) if timestamps else "- Not recorded"}

Please generate a full audit report with these sections:
EXECUTIVE SUMMARY
EMPLOYEE DETAILS
SECURITY ACTIONS TAKEN
FINANCIAL IMPACT
COMPLIANCE STATUS
RECOMMENDATIONS"""

    prompt = f"{REPORT_SYSTEM_PROMPT}\n\n{user_message}"
    result = _generate_content(prompt)
    report = result.strip()
    employee_name = signal.get("employee_name", "Unknown")
    print(f"Audit report generated for {employee_name}")
    return report


def _normalize_email_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts = []
        if value.get("subject"):
            parts.append(f"Subject: {value['subject']}")
        if value.get("body"):
            parts.append(str(value["body"]))
        if not parts:
            parts = [f"{k}: {v}" for k, v in value.items()]
        return "\n\n".join(parts)
    return str(value)


def generate_stakeholder_emails(signal: dict, actions: dict) -> dict:
    tool_summary = [
        f"{action['tool']}: PKR {action['monthly_saving_pkr']}/month"
        for action in actions.get("actions_taken", [])
    ]

    user_message = f"""Generate stakeholder emails for this offboarding at TechHub Pvt Ltd.

Employee Name: {signal.get("employee_name")}
Employee Email: {signal.get("employee_email")}
Offboarding Reason: {signal.get("reason")}

Tools and Savings:
{chr(10).join(f"- {item}" for item in tool_summary)}

Total Monthly Savings: PKR {actions.get("total_saved_pkr", 0)}"""

    prompt = f"{EMAILS_SYSTEM_PROMPT}\n\n{user_message}"
    result = _generate_content(prompt)
    content = _strip_markdown(result)

    try:
        emails = json.loads(content)
    except json.JSONDecodeError:
        clean = _clean_json_string(content)
        try:
            emails = json.loads(clean)
        except json.JSONDecodeError:
            # Last resort — return safe fallback emails
            employee_name = signal.get("employee_name", "Unknown")
            total_saved = actions.get("total_saved_pkr", 0)
            emails = {
                "it_email": f"From: ops-agent@techhub.pk\nTo: it@techhub.pk\nSubject: Access Revocation - {employee_name}\n\nAll SaaS access for {employee_name} has been revoked by OpsAgent.",
                "finance_email": f"From: ops-agent@techhub.pk\nTo: finance@techhub.pk\nSubject: License Cancellation - {employee_name}\n\nAll licenses cancelled. Monthly saving: PKR {total_saved:,}.",
                "hr_email": f"From: ops-agent@techhub.pk\nTo: hr@techhub.pk\nSubject: Offboarding Complete - {employee_name}\n\nOffboarding for {employee_name} has been completed by OpsAgent.",
            }

    return {
        "it_email": _normalize_email_text(emails.get("it_email", "")),
        "finance_email": _normalize_email_text(emails.get("finance_email", "")),
        "hr_email": _normalize_email_text(emails.get("hr_email", "")),
    }


if __name__ == "__main__":
    mock_signal = {
        "employee_name": "Ahmed Raza",
        "employee_email": "ahmed.raza@techhub.pk",
        "reason": "Farewell email detected indicating last day of employment",
    }
    mock_access = {
        "tools": ["Google Workspace", "Slack", "GitHub", "Notion", "Zoom"],
        "total_monthly_cost_pkr": 10500,
    }
    mock_actions = {
        "actions_taken": [
            {"tool": "Google Workspace", "action": "access_revoked", "status": "completed", "monthly_saving_pkr": 2800},
            {"tool": "Slack", "action": "access_revoked", "status": "completed", "monthly_saving_pkr": 1900},
            {"tool": "GitHub", "action": "access_revoked", "status": "completed", "monthly_saving_pkr": 2200},
            {"tool": "Notion", "action": "access_revoked", "status": "completed", "monthly_saving_pkr": 1500},
            {"tool": "Zoom", "action": "access_revoked", "status": "completed", "monthly_saving_pkr": 2100},
        ],
        "total_saved_pkr": 10500,
    }
    report = generate_report(mock_signal, mock_access, mock_actions)
    print(report)
    emails = generate_stakeholder_emails(mock_signal, mock_actions)
    print("IT Email preview:", emails["it_email"][:200])
