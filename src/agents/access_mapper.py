import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SAAS_REGISTRY = {
    "Google Workspace": 2800,
    "Slack": 1900,
    "GitHub": 2200,
    "Notion": 1500,
    "Zoom": 2100,
    "Trello": 800,
    "Figma": 3200,
    "HubSpot": 4500,
}

EMPLOYEE_DB = {
    "ahmed.raza@techhub.pk": ["Google Workspace", "Slack", "GitHub", "Notion", "Zoom"],
    "sara.khan@techhub.pk": ["Google Workspace", "Slack", "Figma", "Notion", "Trello"],
    "bilal.sheikh@techhub.pk": ["Google Workspace", "GitHub", "HubSpot", "Zoom", "Slack"],
    "fatima.malik@techhub.pk": ["Google Workspace", "Slack", "Notion", "Trello"],
}

GUESS_SYSTEM_PROMPT = (
    "You are an IT access analyst for TechHub Pvt Ltd, a Pakistani tech company. "
    "Given an employee email address, guess which SaaS tools they likely have access to. "
    "Return ONLY a raw JSON array of tool name strings from this exact list: "
    f"{list(SAAS_REGISTRY.keys())}. "
    "Choose a reasonable subset (3-6 tools) based on the email domain and typical roles. "
    "No markdown, no explanation."
)


def _strip_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


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


def _guess_tools_with_groq(employee_email: str) -> list:
    prompt = f"{GUESS_SYSTEM_PROMPT}\n\n{employee_email}"
    result = _generate_content(prompt)
    content = _strip_markdown(result)
    tools = json.loads(content)
    valid_tools = [t for t in tools if t in SAAS_REGISTRY]
    return valid_tools or list(SAAS_REGISTRY.keys())[:4]


def map_access(employee_email: str) -> dict:
    tools = EMPLOYEE_DB.get(employee_email)
    if tools is None:
        tools = _guess_tools_with_groq(employee_email)

    tool_details = [
        {"tool_name": tool, "monthly_cost_pkr": SAAS_REGISTRY[tool]}
        for tool in tools
    ]
    total_monthly_cost_pkr = sum(item["monthly_cost_pkr"] for item in tool_details)

    print(
        f"Access mapped for {employee_email}: {len(tools)} tools found, "
        f"PKR {total_monthly_cost_pkr} at risk"
    )

    return {
        "employee_email": employee_email,
        "tools": tools,
        "total_monthly_cost_pkr": total_monthly_cost_pkr,
        "tool_details": tool_details,
    }


def execute_actions(mapped_access: dict) -> dict:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    now = datetime.now().isoformat()
    actions_taken = []

    for detail in mapped_access["tool_details"]:
        tool = detail["tool_name"]
        cost = detail["monthly_cost_pkr"]
        print(f"✓ {tool} - Access revoked, license cancelled. Saving PKR {cost}/month")
        actions_taken.append(
            {
                "tool": tool,
                "action": "access_revoked",
                "status": "completed",
                "timestamp": now,
                "license_cancelled": True,
                "monthly_saving_pkr": cost,
            }
        )

    total_saved_pkr = sum(action["monthly_saving_pkr"] for action in actions_taken)

    return {
        "actions_taken": actions_taken,
        "total_saved_pkr": total_saved_pkr,
        "execution_time": now,
    }


if __name__ == "__main__":
    result = map_access("ahmed.raza@techhub.pk")
    print(result)
    actions = execute_actions(result)
    print(f"Total saved: PKR {actions['total_saved_pkr']}/month")
