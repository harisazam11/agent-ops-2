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
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "mock_emails.json"

SYSTEM_PROMPT = (
    "You are an HR signal detector for a Pakistani tech company called TechHub Pvt Ltd. "
    "Analyze this email and return ONLY a raw JSON object with no markdown and no explanation with these exact keys:\n"
    "- is_offboarding: true or false\n"
    "- employee_name: full name of employee leaving, or null\n"
    "- employee_email: email of employee leaving, or null\n"
    "- confidence: one of 'high', 'medium', 'low'\n"
    "- reason: one sentence explaining why this is or is not an offboarding signal"
)


def load_emails() -> list:
    with open(DATA_FILE, encoding="utf-8") as f:
        emails = json.load(f)
    print(f"Loaded {len(emails)} emails")
    return emails


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


def detect_signals(emails: list) -> list:
    results = []

    for email in emails:
        try:
            user_message = f"{email['subject']}\n\n{email['body']}"
            prompt = f"{SYSTEM_PROMPT}\n\n{user_message}"
            result = _generate_content(prompt)
            content = _strip_markdown(result)
            signal = json.loads(content)
            signal["id"] = email["id"]

            if signal.get("is_offboarding"):
                print(f"Signal detected: {signal.get('employee_name')}")
                results.append(signal)
        except Exception as e:
            print(f"Warning: Failed to parse email id {email.get('id')}: {e}")

    return results


if __name__ == "__main__":
    emails = load_emails()
    signals = detect_signals(emails)
    print(f"Total offboarding signals found: {len(signals)}")
