import os
import json
from dotenv import load_dotenv
from groq import Groq
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

load_dotenv()

app = FastAPI(title="OpsAgent Backend", description="Autonomous Operations Agent Backend")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Mock database structures mirroring frontend definitions
EMPLOYEE_DB = {
  "ahmed.raza@techhub.pk": { "name": "Ahmed Raza", "role": "Senior Developer", "tools": ["Google Workspace", "Slack", "GitHub", "Notion", "Zoom"] },
  "sara.khan@techhub.pk": { "name": "Sara Khan", "role": "UI/UX Designer", "tools": ["Google Workspace", "Slack", "Figma", "Notion", "Trello"] },
  "bilal.sheikh@techhub.pk": { "name": "Bilal Sheikh", "role": "Sales Manager", "tools": ["Google Workspace", "GitHub", "HubSpot", "Zoom", "Slack"] },
  "fatima.malik@techhub.pk": { "name": "Fatima Malik", "role": "Project Manager", "tools": ["Google Workspace", "Slack", "Notion", "Trello"] },
  "zara.ahmed@techhub.pk": { "name": "Zara Ahmed", "role": "Frontend Developer", "tools": [] },
  "usman.ali@techhub.pk": { "name": "Usman Ali", "role": "Data Analyst", "tools": [] },
}

SAAS_COSTS = {
  "Google Workspace": 2800, "Slack": 1900, "GitHub": 2200,
  "Notion": 1500, "Zoom": 2100, "Trello": 800, "Figma": 3200,
  "HubSpot": 4500,
}

TOOL_ICONS = {
  "Google Workspace": "ti-brand-google", "Slack": "ti-brand-slack",
  "GitHub": "ti-brand-github", "Notion": "ti-notebook",
  "Zoom": "ti-video", "Trello": "ti-layout-kanban",
  "Figma": "ti-brand-figma", "HubSpot": "ti-chart-funnel",
}

ROLE_TOOL_MAP = {
  "Frontend Developer": ["Google Workspace", "Slack", "GitHub", "Figma", "Notion"],
  "Data Analyst": ["Google Workspace", "Slack", "Notion", "Zoom", "Trello"],
  "Senior Developer": ["Google Workspace", "Slack", "GitHub", "Notion", "Zoom"],
  "UI/UX Designer": ["Google Workspace", "Slack", "Figma", "Notion", "Trello"],
  "Sales Manager": ["Google Workspace", "HubSpot", "Zoom", "Slack", "Trello"],
  "Project Manager": ["Google Workspace", "Slack", "Notion", "Trello", "Zoom"],
  "default": ["Google Workspace", "Slack", "Notion"]
}

TOOL_USAGE_DATA = {
  "ahmed.raza@techhub.pk": {
    "Google Workspace": 2,
    "Slack": 1,
    "GitHub": 3,
    "Notion": 47,
    "Zoom": 52
  },
  "sara.khan@techhub.pk": {
    "Google Workspace": 1,
    "Slack": 2,
    "Figma": 4,
    "Notion": 3,
    "Trello": 61
  },
  "bilal.sheikh@techhub.pk": {
    "Google Workspace": 1,
    "GitHub": 55,
    "HubSpot": 2,
    "Zoom": 3,
    "Slack": 1
  },
  "fatima.malik@techhub.pk": {
    "Google Workspace": 2,
    "Slack": 1,
    "Notion": 2,
    "Trello": 44
  }
}

# Stateful employee registry
employees = json.loads(json.dumps(EMPLOYEE_DB))

@app.get("/api/employees")
def get_employees():
    """Retrieve the current state of the employee registry."""
    return employees

@app.post("/api/scan")
def scan_emails():
    """Scan inbox for HR events (Onboarding/Offboarding) using Groq llama-3.1-8b-instant."""
    emails_path = os.path.join(os.path.dirname(__file__), "src", "data", "mock_emails.json")
    if not os.path.exists(emails_path):
        raise HTTPException(status_code=404, detail=f"mock_emails.json not found at {emails_path}")
    
    with open(emails_path, "r", encoding="utf-8") as f:
        emails = json.load(f)
    
    offboarding_sigs = []
    onboarding_sigs = []
    
    for email in emails:
        prompt = f"""
        Analyze the following email. Determine if it contains:
        1. An offboarding signal (an employee resigning, leaving the company, or offboarding).
        2. An onboarding signal (a new hire joining, welcome message, or onboarding).
        3. None of these.
        
        Email Subject: {email.get('subject', '')}
        Email Body: {email.get('body', '')}
        
        Respond ONLY with a JSON object in the following format (do not include markdown block formatting, just the raw JSON):
        {{
          "signal_type": "offboarding" | "onboarding" | "none",
          "employee_name": "Full Name of the employee or null",
          "employee_email": "Email of the employee or null",
          "role": "Role of the employee or null",
          "date": "Effective date of arrival/departure or null"
        }}
        """
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            res_text = response.choices[0].message.content.strip()
            res_json = json.loads(res_text)
            
            sig_type = res_json.get("signal_type", "none")
            if sig_type == "offboarding":
                emp_email = res_json.get("employee_email")
                emp_name = res_json.get("employee_name")
                
                # Match with database to resolve correct email/role
                resolved = None
                for email_key, val in employees.items():
                    if emp_name and emp_name.lower() in val["name"].lower():
                        resolved = email_key
                        break
                    if emp_email and emp_email.lower() == email_key.lower():
                        resolved = email_key
                        break
                        
                offboarding_sigs.append({
                    "id": email.get("id"),
                    "from": email.get("from"),
                    "subject": email.get("subject"),
                    "body": email.get("body"),
                    "date": email.get("date"),
                    "employee_email": resolved if resolved else (emp_email or "")
                })
            elif sig_type == "onboarding":
                emp_email = res_json.get("employee_email")
                emp_name = res_json.get("employee_name")
                emp_role = res_json.get("role")
                
                # Match database to resolve correct email/role
                resolved = None
                for email_key, val in employees.items():
                    if emp_name and emp_name.lower() in val["name"].lower():
                        resolved = email_key
                        break
                
                onboarding_sigs.append({
                    "employee_name": emp_name or "New Hire",
                    "employee_email": resolved if resolved else (emp_email or ""),
                    "role": emp_role or (employees[resolved]["role"] if resolved else "Default Fallback"),
                    "date": res_json.get("date") or email.get("date")
                })
        except Exception as e:
            # Fallback manual keyword matching if API fails
            subject_body = (email.get('subject', '') + " " + email.get('body', '')).lower()
            if any(k in subject_body for k in ["last day", "farewell", "no longer", "offboarding", "resignation", "leaving"]):
                resolved_email = None
                for email_key, val in employees.items():
                    first_name = val["name"].split(" ")[0].lower()
                    if first_name in subject_body:
                        resolved_email = email_key
                        break
                if resolved_email:
                    offboarding_sigs.append({
                        "id": email.get("id"),
                        "from": email.get("from"),
                        "subject": email.get("subject"),
                        "body": email.get("body"),
                        "date": email.get("date"),
                        "employee_email": resolved_email
                    })
            elif any(k in subject_body for k in ["welcome", "joining", "new hire", "new developer", "new analyst", "please welcome", "onboarding"]):
                resolved_email = None
                for email_key, val in employees.items():
                    first_name = val["name"].split(" ")[0].lower()
                    if first_name in subject_body:
                        resolved_email = email_key
                        break
                if resolved_email:
                    onboarding_sigs.append({
                        "employee_name": employees[resolved_email]["name"],
                        "employee_email": resolved_email,
                        "role": employees[resolved_email]["role"],
                        "date": email.get("date")
                    })
                    
    return {
        "offboarding": offboarding_sigs,
        "onboarding": onboarding_sigs
    }

class MapAccessRequest(BaseModel):
    email: str

@app.post("/api/map-access")
def map_access(req: MapAccessRequest):
    """Retrieve SaaS access configuration from registry. Automatically provisions empty profiles."""
    email = req.email.strip()
    if email not in employees:
        raise HTTPException(status_code=404, detail=f"Employee {email} not found")
    
    emp = employees[email]
    # Dynamically provision recommended tools for new hires
    if not emp["tools"]:
        role = emp["role"]
        recommended = ROLE_TOOL_MAP.get(role, ROLE_TOOL_MAP["default"])
        emp["tools"] = list(recommended)
    
    mapped_tools = []
    total_cost = 0
    for t in emp["tools"]:
        cost = SAAS_COSTS.get(t, 0)
        icon = TOOL_ICONS.get(t, "ti-app")
        mapped_tools.append({
            "name": t,
            "cost": cost,
            "icon": icon
        })
        total_cost += cost
        
    return {
        "emp": {
            "name": emp["name"],
            "role": emp["role"],
            "email": email
        },
        "tools": mapped_tools,
        "totalCost": total_cost
    }

class CancellationItem(BaseModel):
    email: str
    tool: str

class ExecuteActionsRequest(BaseModel):
    email: Optional[str] = None
    tools: Optional[List[Any]] = None
    cancellations: Optional[List[CancellationItem]] = None

@app.post("/api/execute-actions")
def execute_actions(req: ExecuteActionsRequest):
    """Deprovision tools. Supports single employee offboarding or batch waste cancellations."""
    # Waste clean-up mode
    if req.cancellations:
        total_saved = 0
        actions_taken = []
        
        for item in req.cancellations:
            emp_email = item.email
            tool_name = item.tool
            
            if emp_email in employees and tool_name in employees[emp_email]["tools"]:
                employees[emp_email]["tools"].remove(tool_name)
                cost = SAAS_COSTS.get(tool_name, 0)
                total_saved += cost
                actions_taken.append({
                    "employee": emp_email,
                    "tool": tool_name,
                    "status": "revoked",
                    "ts": "Just now"
                })
        return {
            "actions": actions_taken,
            "saved": total_saved
        }
        
    # Standard employee offboarding mode
    email = req.email
    tools = req.tools or []
    
    if not email or email not in employees:
        raise HTTPException(status_code=400, detail="Invalid email or employee not found")
        
    employees[email]["tools"] = [] # Clear employee tools
    
    total_saved = 0
    actions_taken = []
    for t in tools:
        tool_name = t.get("name") if isinstance(t, dict) else t
        cost = SAAS_COSTS.get(tool_name, 0)
        total_saved += cost
        actions_taken.append({
            "name": tool_name,
            "status": "revoked",
            "ts": "Just now"
        })
        
    return {
        "actions": actions_taken,
        "saved": total_saved
    }

class GenerateReportRequest(BaseModel):
    signal: dict
    actions: List[dict]

@app.post("/api/generate-report")
def generate_report(req: GenerateReportRequest):
    """Generate a detailed compliance audit report using Groq llama-3.1-8b-instant."""
    subject = req.signal.get("subject", "Offboarding Notification")
    body = req.signal.get("body", "")
    actions_str = ", ".join([f"{a.get('name', a.get('tool', ''))} (revoked)" for a in req.actions])
    
    prompt = f"""
    Generate a professional, detailed IT Compliance Audit Report for TechHub Pvt Ltd.
    
    HR Event Signal:
    Subject: {subject}
    Content: {body}
    
    SaaS Deprovisioning Actions Taken:
    {actions_str}
    
    Ensure the report is highly detailed, highlighting security compliance, risk mitigation (preventing unauthorized access after departure), and the financial savings in PKR (PKR currency context). Format as clean plain text.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        report_text = response.choices[0].message.content
        return {"report": report_text}
    except Exception as e:
        return {
            "report": f"TECHHUB PVT LTD - COMPLIANCE AUDIT REPORT\n\nEvent: Access Revocation\nActions executed successfully: {actions_str}.\nAccess revoked in accordance with security policy.\nStatus: APPROVED"
        }

class StakeholderEmailsRequest(BaseModel):
    employee: dict
    actions: List[dict]

@app.post("/api/stakeholder-emails")
def stakeholder_emails(req: StakeholderEmailsRequest):
    """Generate stakeholder alert emails using Groq llama-3.1-8b-instant."""
    name = req.employee.get("name", "Employee")
    email = req.employee.get("email", "")
    role = req.employee.get("role", "")
    actions_str = ", ".join([f"{a.get('name', a.get('tool', ''))}" for a in req.actions])
    
    prompt = f"""
    Generate three professional notification emails for TechHub Pvt Ltd stakeholders regarding the access revocation of {name} ({email}, {role}).
    The actions taken were: Revoked access for {actions_str}.
    
    We need emails for these three stakeholders:
    1. IT Team (focus on system cleanup and hardware recovery)
    2. Finance Team (focus on monthly software subscription cost savings)
    3. HR Team (focus on compliance record and final clearance)
    
    Respond ONLY with a JSON object in the following format (do not wrap it in markdown block formatting, just the raw JSON):
    {{
      "it": "Subject and body of email to IT Team...",
      "finance": "Subject and body of email to Finance Team...",
      "hr": "Subject and body of email to HR Team..."
    }}
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        res_text = response.choices[0].message.content.strip()
        res_json = json.loads(res_text)
        return res_json
    except Exception as e:
        return {
            "it": f"Subject: IT Revocation: {name}\n\nHi IT Team,\n\nPlease verify access is cleared for {name}. Recover any company assets.",
            "finance": f"Subject: Finance Update: {name} Subscriptions Cancelled\n\nHi Finance,\n\nAll subscriptions revoked for {name}. Monthly spend updated.",
            "hr": f"Subject: HR Clearance: {name}\n\nHi HR Team,\n\nAccess deprovisioning complete. Final clearance is ready for processing."
        }

@app.post("/api/waste-scan")
def waste_scan():
    """Identify software waste where seats haven't logged in for 30+ days."""
    unused = []
    total_waste = 0
    
    for email, emp in employees.items():
        usage = TOOL_USAGE_DATA.get(email)
        if not usage:
            continue
        for tool_name in emp["tools"]:
            days = usage.get(tool_name)
            if days is not None and days >= 30:
                cost = SAAS_COSTS.get(tool_name, 0)
                unused.append({
                    "employee": {
                        "email": email,
                        "name": emp["name"],
                        "role": emp["role"]
                    },
                    "tool": tool_name,
                    "lastLogin": f"{days} days ago",
                    "daysSinceLogin": days,
                    "monthlyCost": cost
                })
                total_waste += cost
                
    return {
        "unused": unused,
        "totalWaste": total_waste
    }
