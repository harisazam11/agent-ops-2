"""
app.py — OpsAgent Dashboard
Run: streamlit run src/app.py
"""

import sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
import streamlit as st
from agents.signal_detector import load_emails, detect_signals
from agents.access_mapper import map_access, execute_actions, EMPLOYEE_DB, SAAS_REGISTRY
from agents.report_generator import generate_report, generate_stakeholder_emails

st.set_page_config(
    page_title="OpsAgent — TechHub Pvt Ltd",
    layout="wide",
    page_icon="🛡️",
)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    color: #111827 !important;
}
.stApp { background: #F3F4F6; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem; max-width: 1100px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1E293B !important;
}
[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] .stMetric label {
    font-size: 0.72rem !important;
    color: #94A3B8 !important;
}
[data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 800 !important;
    color: #F8FAFC !important;
}
[data-testid="stSidebar"] hr {
    border-color: #334155 !important;
}

/* ── Spinner fix ── */
[data-testid="stSpinner"] {
    background: #FFFFFF !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    border: 1px solid #E5E7EB !important;
}
[data-testid="stSpinner"] * {
    color: #374151 !important;
}
[data-testid="stSpinner"] > div {
    background: #FFFFFF !important;
}
.stSpinner > div {
    border-top-color: #2563EB !important;
}

/* ── Top bar ── */
.top-bar {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.brand-name { font-size: 1.1rem; font-weight: 800; color: #111827; letter-spacing: -0.3px; }
.brand-sub  { font-size: 0.73rem; color: #6B7280; margin-top: 2px; }
.live-pill  {
    display: inline-flex; align-items: center; gap: 6px;
    background: #ECFDF5; color: #065F46;
    border: 1px solid #6EE7B7; border-radius: 20px;
    padding: 5px 14px; font-size: 0.78rem; font-weight: 600;
}
.live-dot {
    width: 7px; height: 7px; background: #10B981; border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── KPI cards ── */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.kpi-label {
    font-size: 0.7rem; font-weight: 600; color: #6B7280;
    text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 8px;
}
.kpi-val { font-size: 2rem; font-weight: 800; letter-spacing: -1px; line-height: 1; }
.kpi-neutral { color: #111827; }
.kpi-danger  { color: #DC2626; }
.kpi-success { color: #059669; }
.kpi-info    { color: #2563EB; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="primary"] {
    background: #2563EB !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 2px 6px rgba(37,99,235,0.3) !important;
}
.stButton > button[kind="primary"]:hover { background: #1D4ED8 !important; }
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #374151 !important;
    border: 1px solid #D1D5DB !important;
}

/* ── Banners ── */
.banner-info {
    background: #EFF6FF; border: 1px solid #BFDBFE;
    border-left: 4px solid #2563EB; border-radius: 8px;
    padding: 0.75rem 1rem; margin-bottom: 0.75rem;
    font-size: 0.85rem; color: #1E40AF;
}
.banner-alert {
    background: #FEF2F2; border: 1px solid #FECACA;
    border-left: 4px solid #EF4444; border-radius: 8px;
    padding: 0.8rem 1rem; margin-bottom: 0.5rem;
    font-size: 0.875rem; font-weight: 600; color: #991B1B;
}
.banner-ok {
    background: #F0FDF4; border: 1px solid #BBF7D0;
    border-left: 4px solid #16A34A; border-radius: 8px;
    padding: 0.8rem 1rem; margin-bottom: 0.75rem;
    font-size: 0.875rem; font-weight: 500; color: #166534;
}

/* ── Section heading ── */
.sec-head {
    font-size: 0.95rem; font-weight: 700; color: #111827;
    margin: 1rem 0 0.6rem 0;
}

/* ── Summary grid ── */
.sum-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 0.75rem; margin: 1rem 0; }
.sum-box {
    background: #FFFFFF; border: 1px solid #E5E7EB;
    border-radius: 10px; padding: 1rem 1.25rem; text-align: center;
}
.sum-label { font-size: 0.68rem; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
.sum-val   { font-size: 1.5rem; font-weight: 800; margin-top: 4px; }

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    margin-bottom: 0.5rem !important;
}
[data-testid="stExpander"] > div {
    background: #FFFFFF !important;
}
[data-testid="stExpander"] details {
    background: #FFFFFF !important;
}
[data-testid="stExpander"] summary {
    color: #111827 !important;
    font-weight: 600 !important;
    background: #FFFFFF !important;
}
[data-testid="stExpander"] summary:hover {
    background: #F9FAFB !important;
}
div[data-testid="stExpander"] div[role="button"] {
    background: #FFFFFF !important;
    color: #111827 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #F3F4F6; border-radius: 8px; padding: 3px; gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px; font-size: 0.84rem;
    font-weight: 500; color: #6B7280 !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #111827 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #E5E7EB !important;
    background: #FFFFFF !important;
}
[data-testid="stDataFrame"] * {
    color: #111827 !important;
}
[data-testid="stDataFrame"] th {
    background: #F9FAFB !important;
    color: #6B7280 !important;
    font-weight: 600 !important;
}
[data-testid="stDataFrame"] td {
    background: #FFFFFF !important;
    color: #111827 !important;
}
[data-testid="stDataFrame"] canvas {
    filter: invert(0) !important;
}
.dvn-scroller { background: #FFFFFF !important; }
.dvn-scroller * { color: #111827 !important; }
iframe[title="st_aggrid"] { background: #FFFFFF !important; }

/* ── Status steps ── */
.step-box {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 0.65rem 1rem;
    margin-bottom: 0.4rem;
    font-size: 0.85rem;
    color: #374151;
    display: flex;
    align-items: center;
    gap: 8px;
}
.step-box.running {
    border-left: 3px solid #2563EB;
    color: #1D4ED8;
    background: #EFF6FF;
}
.step-box.done {
    border-left: 3px solid #16A34A;
    color: #166534;
    background: #F0FDF4;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _resolve_email(signal):
    e = signal.get("employee_email")
    if e and isinstance(e, str) and e in EMPLOYEE_DB:
        return e
    name = signal.get("employee_name", "")
    for db_email in EMPLOYEE_DB:
        db_name = db_email.split("@")[0].replace(".", " ").title()
        if name.strip().lower() == db_name.strip().lower():
            return db_email
    if name:
        return name.lower().replace(" ", ".") + "@techhub.pk"
    return e or "unknown@techhub.pk"

def _name_from_email(email):
    return email.split("@")[0].replace(".", " ").title()

def _dedup_signals(signals):
    seen, deduped = set(), []
    for sig in signals:
        email = _resolve_email(sig)
        if email not in seen:
            seen.add(email)
            deduped.append(sig)
    return deduped


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("sig_count", 0), ("pkr_saved", 0), ("act_count", 0)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ OpsAgent")
    st.markdown("<span style='color:#94A3B8;font-size:0.8rem'>Autonomous Operations Monitor</span>", unsafe_allow_html=True)
    st.markdown("<span style='color:#CBD5E1;font-weight:600'>TechHub Pvt Ltd</span>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<span style='color:#34D399'>● System Active</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#94A3B8;font-size:0.78rem'>{datetime.now().strftime('%d %B %Y · %H:%M')}</span>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<span style='color:#94A3B8;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em'>COVERAGE</span>", unsafe_allow_html=True)
    st.metric("Emails Monitored", 5)
    st.metric("Employees", 4)
    st.metric("SaaS Tools", 8)
    st.divider()
    st.markdown("<span style='color:#64748B;font-size:0.75rem'>Powered by Groq · Llama 3.1</span>", unsafe_allow_html=True)


# ── Top bar ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
  <div>
    <div class="brand-name">🛡️ OpsAgent</div>
    <div class="brand-sub">Autonomous Operations Monitor &nbsp;·&nbsp; TechHub Pvt Ltd</div>
  </div>
  <div class="live-pill"><div class="live-dot"></div> System Active</div>
</div>
""", unsafe_allow_html=True)


# ── KPI cards ─────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3 = st.columns(3)
sig_ph  = kpi1.empty()
save_ph = kpi2.empty()
act_ph  = kpi3.empty()

def render_kpis(s, p, a):
    sc = "kpi-danger"  if s > 0 else "kpi-neutral"
    pc = "kpi-success" if p > 0 else "kpi-neutral"
    ac = "kpi-info"    if a > 0 else "kpi-neutral"
    sig_ph.markdown(f'<div class="kpi-card"><div class="kpi-label">Signals Detected</div><div class="kpi-val {sc}">{s}</div></div>', unsafe_allow_html=True)
    save_ph.markdown(f'<div class="kpi-card"><div class="kpi-label">PKR Saved Monthly</div><div class="kpi-val {pc}">₨{p:,}</div></div>', unsafe_allow_html=True)
    act_ph.markdown(f'<div class="kpi-card"><div class="kpi-label">Actions Taken</div><div class="kpi-val {ac}">{a}</div></div>', unsafe_allow_html=True)

render_kpis(st.session_state.sig_count, st.session_state.pkr_saved, st.session_state.act_count)
st.write("")


# ── Scan + Reset ──────────────────────────────────────────────────────────────
st.markdown('<div class="banner-info">ℹ️ &nbsp; Click <b>Scan</b> to analyse HR emails, detect offboarding signals, and execute security actions automatically.</div>', unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])
with col1:
    scan_clicked = st.button("🔍  Scan for Offboarding Signals", type="primary", use_container_width=True)
with col2:
    reset_clicked = st.button("↺  Reset", type="secondary", use_container_width=True)

if reset_clicked:
    st.session_state.sig_count = 0
    st.session_state.pkr_saved = 0
    st.session_state.act_count = 0
    st.rerun()

st.divider()


# ── Pipeline ──────────────────────────────────────────────────────────────────
if scan_clicked:
    try:
        # Step indicators instead of spinners
        st.markdown('<div class="step-box running">📬 &nbsp; Connecting to email monitor...</div>', unsafe_allow_html=True)
        emails = load_emails()
        st.markdown(f'<div class="step-box done">✓ &nbsp; Loaded {len(emails)} emails from inbox</div>', unsafe_allow_html=True)

        st.markdown('<div class="step-box running">🔍 &nbsp; Analysing emails for HR signals...</div>', unsafe_allow_html=True)
        signals = detect_signals(emails)
        signals = _dedup_signals(signals)
        st.markdown(f'<div class="step-box done">✓ &nbsp; Analysis complete — {len(signals)} offboarding signal(s) detected</div>', unsafe_allow_html=True)

        st.session_state.sig_count = len(signals)
        render_kpis(len(signals), st.session_state.pkr_saved, st.session_state.act_count)

        if not signals:
            st.markdown('<div class="banner-ok">✅ &nbsp; No offboarding signals detected. All employees are active.</div>', unsafe_allow_html=True)
        else:
            st.write("")
            for sig in signals:
                st.markdown(f'<div class="banner-alert">🚨 &nbsp; Offboarding detected — <b>{sig["employee_name"]}</b> &nbsp;·&nbsp; {_resolve_email(sig)}</div>', unsafe_allow_html=True)

            total_saved = 0
            total_acts  = 0

            for sig in signals:
                name  = sig.get("employee_name", "Unknown")
                email = _resolve_email(sig)

                st.markdown(f'<div class="sec-head">👤 Processing: {name}</div>', unsafe_allow_html=True)

                # Map access
                try:
                    st.markdown(f'<div class="step-box running">🗺️ &nbsp; Mapping SaaS access for {name}...</div>', unsafe_allow_html=True)
                    access = map_access(email)
                    st.markdown(f'<div class="step-box done">✓ &nbsp; {len(access["tools"])} tools mapped — ₨{access["total_monthly_cost_pkr"]:,} at risk</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not map access for {name}: {e}")
                    continue

                with st.expander(f"🔧  {len(access['tools'])} tools at risk — {name}", expanded=True):
                    risk_df = pd.DataFrame([
                        {"Tool": d["tool_name"], "Monthly Cost": f"₨ {d['monthly_cost_pkr']:,}", "Status": "⚠️ Active"}
                        for d in access["tool_details"]
                    ])
                    st.dataframe(risk_df, use_container_width=True, hide_index=True)
                    st.markdown(f"**Total exposure: ₨ {access['total_monthly_cost_pkr']:,} / month**")

                # Execute actions
                try:
                    st.markdown(f'<div class="step-box running">⚡ &nbsp; Revoking access and cancelling licenses for {name}...</div>', unsafe_allow_html=True)
                    actions = execute_actions(access)
                    st.markdown(f'<div class="step-box done">✓ &nbsp; {len(actions["actions_taken"])} actions executed — ₨{actions["total_saved_pkr"]:,}/month saved</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not execute actions for {name}: {e}")
                    continue

                with st.expander(f"✅  {len(actions['actions_taken'])} actions completed — {name}", expanded=False):
                    done_df = pd.DataFrame([
                        {
                            "Tool": a["tool"],
                            "Action": "Access revoked · License cancelled",
                            "Saving / Month": f"₨ {a['monthly_saving_pkr']:,}"
                        }
                        for a in actions["actions_taken"]
                    ])
                    st.dataframe(done_df, use_container_width=True, hide_index=True)
                    st.markdown(f"**Total saved: ₨ {actions['total_saved_pkr']:,} / month**")

                total_saved += actions["total_saved_pkr"]
                total_acts  += len(actions["actions_taken"])

                # Audit report
                try:
                    st.markdown('<div class="step-box running">📄 &nbsp; Generating compliance audit report...</div>', unsafe_allow_html=True)
                    report = generate_report(sig, access, actions)
                    os.makedirs(REPORTS_DIR, exist_ok=True)
                    rpath = os.path.join(REPORTS_DIR, f"{name.replace(' ','_')}_audit_report.txt")
                    with open(rpath, "w", encoding="utf-8") as f:
                        f.write(report)
                    st.markdown('<div class="step-box done">✓ &nbsp; Audit report generated and saved</div>', unsafe_allow_html=True)
                    with st.expander("📄  Compliance Audit Report", expanded=False):
                        st.code(report, language=None)
                except Exception as e:
                    st.error(f"Audit report failed for {name}: {e}")

                # Stakeholder emails
                try:
                    st.markdown('<div class="step-box running">📧 &nbsp; Drafting stakeholder notifications...</div>', unsafe_allow_html=True)
                    s_emails = generate_stakeholder_emails(sig, actions)
                    st.markdown('<div class="step-box done">✓ &nbsp; Notifications drafted for IT, Finance and HR teams</div>', unsafe_allow_html=True)
                    with st.expander("📧  Stakeholder Notifications", expanded=False):
                        t1, t2, t3 = st.tabs(["IT Team", "Finance Team", "HR Team"])
                        with t1: st.code(s_emails["it_email"], language=None)
                        with t2: st.code(s_emails["finance_email"], language=None)
                        with t3: st.code(s_emails["hr_email"], language=None)
                except Exception as e:
                    st.error(f"Stakeholder emails failed for {name}: {e}")

                st.divider()

            # Update KPIs
            st.session_state.pkr_saved += total_saved
            st.session_state.act_count += total_acts
            render_kpis(len(signals), st.session_state.pkr_saved, st.session_state.act_count)

            # Final summary
            st.markdown(f"""
            <div class="sum-grid">
              <div class="sum-box">
                <div class="sum-label">Employees Processed</div>
                <div class="sum-val" style="color:#DC2626">{len(signals)}</div>
              </div>
              <div class="sum-box">
                <div class="sum-label">Monthly Savings</div>
                <div class="sum-val" style="color:#059669">₨{total_saved:,}</div>
              </div>
              <div class="sum-box">
                <div class="sum-label">Actions Executed</div>
                <div class="sum-val" style="color:#2563EB">{total_acts}</div>
              </div>
            </div>
            <div class="banner-ok">✅ &nbsp; Pipeline complete — all offboarding actions executed and compliance reports saved.</div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Pipeline failed: {e}. Check that your GROQ_API_KEY is set in Streamlit secrets.")


# ── Employee Registry ─────────────────────────────────────────────────────────
st.markdown('<div class="sec-head" style="margin-top:1.5rem">👥 Active Employee Registry</div>', unsafe_allow_html=True)
st.caption("All employees currently monitored by OpsAgent with SaaS tool exposure and monthly cost.")

try:
    rows = []
    for emp_email, tools in EMPLOYEE_DB.items():
        cost = sum(SAAS_REGISTRY[t] for t in tools)
        rows.append({
            "Name": _name_from_email(emp_email),
            "Email": emp_email,
            "Tools": ", ".join(tools),
            "Monthly Cost": f"₨ {cost:,}",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Could not load registry: {e}")

st.markdown("<br>", unsafe_allow_html=True)
st.caption("OpsAgent · Groq Llama 3.1 · TechHub Pvt Ltd · Hackathon 2026")
