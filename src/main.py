import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise EnvironmentError("GROQ_API_KEY missing. Add it to your .env file.")

from agents.access_mapper import execute_actions, map_access
from agents.report_generator import generate_report, generate_stakeholder_emails
from agents.signal_detector import detect_signals, load_emails


def _resolve_employee_email(signal: dict) -> str:
    email = signal.get("employee_email")
    if email:
        return email
    name = signal.get("employee_name", "unknown")
    return name.lower().replace(" ", ".") + "@techhub.pk"


def _report_filename(employee_name: str) -> str:
    safe_name = employee_name.replace(" ", "_")
    return f"{safe_name}_audit_report.txt"


def run_pipeline() -> None:
    # STEP 1 - SCAN EMAILS
    emails = load_emails()
    signals = detect_signals(emails)

    print("=== SIGNALS DETECTED ===")
    print(len(signals))

    if not signals:
        print("No offboarding signals found.")
        return

    REPORTS_DIR.mkdir(exist_ok=True)
    total_savings = 0
    processed = 0

    for signal in signals:
        employee_name = signal.get("employee_name")
        if not employee_name:
            continue
        employee_email = _resolve_employee_email(signal)

        # STEP 2 - PROCESS EACH SIGNAL
        print(f"=== PROCESSING: {employee_name} ===")

        # STEP 3 - MAP ACCESS
        mapped_access = map_access(employee_email)
        print(f"Tools: {', '.join(mapped_access['tools'])}")
        print(f"Total PKR at risk: {mapped_access['total_monthly_cost_pkr']}")

        # STEP 4 - EXECUTE ACTIONS
        actions = execute_actions(mapped_access)
        for action in actions["actions_taken"]:
            print(
                f"  {action['tool']}: {action['action']} - "
                f"Saving PKR {action['monthly_saving_pkr']}/month"
            )
        print(f"Total PKR saved: {actions['total_saved_pkr']}")
        total_savings += actions["total_saved_pkr"]

        # STEP 5 - GENERATE REPORT
        report = generate_report(signal, mapped_access, actions)
        report_path = REPORTS_DIR / _report_filename(employee_name)
        report_path.write_text(report, encoding="utf-8")
        print(f"Report saved: {report_path}")

        # STEP 6 - GENERATE STAKEHOLDER EMAILS
        stakeholder_emails = generate_stakeholder_emails(signal, actions)
        print("IT Email preview:", stakeholder_emails["it_email"][:100])
        print("Finance Email preview:", stakeholder_emails["finance_email"][:100])
        print("HR Email preview:", stakeholder_emails["hr_email"][:100])

        processed += 1

    print("=== PIPELINE COMPLETE ===")
    print(f"Employees processed: {processed}")
    print(f"Total monthly savings: PKR {total_savings}")
    print("Reports saved to reports/ folder")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)
