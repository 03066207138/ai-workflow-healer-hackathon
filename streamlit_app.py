# ============================================================
# 🏆 Hackathon Dashboard — AI Workflow Healer (Streamlit app.py)
# Auto-Healing + Manual Healing + PDF Slips + Live Metrics
# (hardened I/O + graceful fallbacks)
# ============================================================

import os
import time
import random
import json
import requests
import pandas as pd
import altair as alt
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ------------------------------
# 🔧 CONFIG — set your backend
# ------------------------------
BACKEND_URL = os.environ.get(
    "HEALER_BACKEND_URL",
    "https://ai-workflow-healer-hackathon-1.onrender.com"
).rstrip("/")

AUTO_TRIGGER_SECONDS = 15
AUTO_REFRESH_MS = 5000
HTTP_TIMEOUT = 15

# ------------------------------
# 🖼️ PAGE
# ------------------------------
st.set_page_config(
    page_title="AI Workflow Healer — Hackathon Dashboard",
    page_icon="🩺",
    layout="wide",
)

# ------------------------------
# 🎨 THEME / CSS (brighter neon)
# ------------------------------
st.markdown("""
<style>
:root {
  --bg: #050912;
  --card: #0c1220;
  --ink: #f9fafb;
  --muted: #cbd5e1;
  --accent: #60a5fa;
  --accent-2: #34d399;
  --warn: #fbbf24;
}
html, body, .stApp {
  background: radial-gradient(circle at top left, var(--bg), #000814 90%);
  color: var(--ink);
  font-family: "Inter", ui-sans-serif;
}
h1, h2, h3, h4, h5 { color: var(--ink); font-weight: 700; }
hr { border: none; height: 1px; background: rgba(255, 255, 255, .15); margin: 1rem 0; }
[data-testid="stSidebar"], .sidebar .sidebar-content { background: var(--card); color: var(--ink) !important; }
[data-testid="stSidebar"] * { color: var(--ink) !important; font-weight: 600; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: var(--ink) !important; }
[data-testid="stSidebar"] button, .sidebar .stButton>button {
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  color: #000814 !important; border: none !important; font-weight: 700 !important;
  border-radius: 8px; margin-top: 5px; transition: all 0.2s ease-in-out;
}
[data-testid="stSidebar"] button:hover, .sidebar .stButton>button:hover {
  background: linear-gradient(90deg, var(--accent-2), var(--accent)); transform: scale(1.03);
}
.stToggleSwitch label { color: var(--ink) !important; font-weight: 600; }
.stButton>button {
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  color: #000814 !important; font-weight: 700 !important; border: none !important;
  border-radius: 10px !important; padding: 0.5rem 1rem !important; transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
  background: linear-gradient(90deg, var(--accent-2), var(--accent)); transform: scale(1.03);
}
.stDownloadButton>button {
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  color: #000814 !important; font-weight: 800 !important; border-radius: 10px !important;
  padding: 0.6rem 1rem !important; border: none !important;
  box-shadow: 0 0 10px rgba(52, 211, 153, 0.4); transition: all 0.3s ease-in-out;
}
.stDownloadButton>button:hover {
  background: linear-gradient(90deg, var(--accent-2), var(--accent)); transform: scale(1.05);
  box-shadow: 0 0 15px rgba(96, 165, 250, 0.7);
}
.kpi {
  text-align: center; padding: 16px; border-radius: 16px;
  background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
  border: 1px solid rgba(255,255,255,.12); box-shadow: 0 8px 28px rgba(0,0,0,.25);
}
.kpi .label { color: var(--muted); font-size: .9rem; }
.kpi .value { color: var(--ink); font-size: 1.8rem; font-weight: 800; }
.invoice {
  background: linear-gradient(180deg, rgba(52, 211, 153, .18), rgba(52, 211, 153, .08));
  border: 1px solid rgba(52, 211, 153, .35); border-radius: 14px; padding: 14px; margin-top: 10px; color: var(--ink);
}
.stToggleSwitch [aria-checked="true"] + div label { animation: pulse 2s infinite; box-shadow: 0 0 12px 2px rgba(96,165,250,0.6); }
@keyframes pulse {
  0% { box-shadow: 0 0 6px 2px rgba(96,165,250,0.4); }
  50% { box-shadow: 0 0 18px 5px rgba(96,165,250,0.8); }
  100% { box-shadow: 0 0 6px 2px rgba(96,165,250,0.4); }
}
.badge {
  display:inline-block; padding:.25rem .5rem; margin-right:.35rem;
  border:1px solid rgba(255,255,255,.25); border-radius:999px; font-size:.85rem;
}
.health-ok { color:#10b981; }
.health-bad { color:#f87171; }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# 🔁 AUTO REFRESH
# ------------------------------
st_autorefresh(interval=AUTO_REFRESH_MS, key="auto_refresh")

# ------------------------------
# 🧰 HELPERS
# ------------------------------
def _url(path: str) -> str:
    return f"{BACKEND_URL}{path}"

def _post_json(path, payload, timeout=HTTP_TIMEOUT):
    try:
        r = requests.post(_url(path), json=payload, timeout=timeout, headers={"accept": "application/json"})
        r.raise_for_status()
        try:
            return True, r.json()
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON from server", "status": r.status_code, "text": r.text[:500]}
    except requests.RequestException as e:
        return False, {"error": str(e)}

def _get_json(path, timeout=HTTP_TIMEOUT):
    try:
        r = requests.get(_url(path), timeout=timeout, headers={"accept": "application/json"})
        r.raise_for_status()
        try:
            return True, r.json()
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON from server", "status": r.status_code, "text": r.text[:500]}
    except requests.RequestException as e:
        return False, {"error": str(e)}

def generate_pdf_slip(result: dict) -> BytesIO:
    """Generate PDF slip into BytesIO (FPDF needs latin-1)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_author("AI Workflow Healer")
    pdf.set_title("Healing Billing Slip")

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Workflow Healing Billing Slip", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    billing = (result or {}).get("billing", {}) or {}
    lines = [
        f"Date: {now}",
        f"User ID: {billing.get('user', 'N/A')}",
        f"Workflow: {(result or {}).get('workflow')}",
        f"Anomaly: {(result or {}).get('anomaly')}",
        f"Heal Status: {(result or {}).get('status')}",
        f"Recovery: {(result or {}).get('recovery_pct')}",
        f"Reward: {(result or {}).get('reward')}",
        f"Amount Charged: ${float(billing.get('amount', 0.05)):.2f}",
        f"Mode: {billing.get('mode', 'local')} | Status: {billing.get('status', 'simulated')}",
    ]
    pdf.ln(6)
    for ln in lines:
        pdf.cell(0, 9, str(ln), ln=True)

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return BytesIO(pdf_bytes)

def anomaly_choices():
    return ["queue_pressure", "data_error", "workflow_delay", "api_failure"]

def workflow_choices():
    return ["invoice_processing", "order_processing", "customer_support", "inventory_tracking"]

# ------------------------------
# 🧠 SIDEBAR
# ------------------------------
st.sidebar.title("🎛️ Controls")
st.sidebar.caption(f"Backend: `{BACKEND_URL}`")

if "auto_enabled" not in st.session_state:
    st.session_state.auto_enabled = True
if "last_auto" not in st.session_state:
    st.session_state.last_auto = 0.0
if "latest_auto_result" not in st.session_state:
    st.session_state.latest_auto_result = None
if "latest_manual_result" not in st.session_state:
    st.session_state.latest_manual_result = None
if "auto_inflight" not in st.session_state:
    st.session_state.auto_inflight = False

st.sidebar.subheader("Modes")
st.session_state.auto_enabled = st.sidebar.toggle("🤖 Auto-Healing", value=True)
manual_section = st.sidebar.toggle("🧩 Manual Healing", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Actions")
if st.sidebar.button("▶️ Single Auto Trigger Now"):
    # force an immediate auto tick
    st.session_state.last_auto = 0.0

if st.sidebar.button("🧪 Simulate Heal (/simulate)"):
    ok, res = _post_json("/simulate", {})
    if ok:
        st.sidebar.success("Simulated one heal.")
    else:
        st.sidebar.error(res.get("error", "simulate failed"))

st.sidebar.markdown("---")
st.sidebar.subheader("Data")
ok_dl, _ = _get_json("/health")  # preflight to avoid long error
try:
    r = requests.get(_url("/metrics/download"), timeout=HTTP_TIMEOUT)
    if r.ok and r.content:
        st.sidebar.download_button(
            "⬇️ Download Metrics CSV",
            r.content,
            "metrics_log.csv",
            "text/csv",
            use_container_width=True,
        )
    else:
        st.sidebar.info("Metrics not ready yet.")
except Exception:
    st.sidebar.info("Metrics not ready yet.")

st.sidebar.markdown("---")
st.sidebar.caption("✨ Neon Hackathon Theme — Bright Mode")

# ------------------------------
# 🏷️ HEADER + HEALTH BADGE
# ------------------------------
ok_health, health = _get_json("/health")
health_badge = "🟢 <span class='health-ok'>Healthy</span>" if ok_health and health.get("status") == "ok" else "🔴 <span class='health-bad'>Down</span>"

st.markdown(
    f"""
# 🩺 AI Workflow Healer — Hackathon Command Center  
<span class="badge">⚡ Real-Time Healing</span> 
<span class="badge">💰 Monetization</span> 
<span class="badge">🤖 Automation</span>
<span class="badge">Health: {health_badge}</span>
""",
    unsafe_allow_html=True,
)

# ============================================================
# 🤖 AUTO-HEALING LOOP
# ============================================================
now = time.time()
should_trigger = (
    st.session_state.auto_enabled
    and not st.session_state.auto_inflight
    and (now - st.session_state.last_auto > AUTO_TRIGGER_SECONDS)
)

if should_trigger:
    st.session_state.auto_inflight = True
    st.session_state.last_auto = now  # set early to avoid double-fire on slow net
    payload = {
        "workflow_id": random.choice(workflow_choices()),
        "anomaly": random.choice(anomaly_choices()),
        "user_id": random.choice(["client_001", "client_002", "client_003"]),
    }
    ok, res = _post_json("/webhook", payload, timeout=HTTP_TIMEOUT)
    st.session_state.auto_inflight = False
    if ok:
        st.session_state.latest_auto_result = res
        amount = ((res or {}).get("billing", {}) or {}).get("amount", 0.05)
        try:
            amount = float(amount)
        except Exception:
            amount = 0.05
        st.toast(
            f"✅ Auto-Heal → {payload['workflow_id']} ({payload['anomaly']}) • billed ${amount:.2f}"
        )
    else:
        st.toast(f"⚠️ Auto-heal failed: {res.get('error','unknown')}", icon="⚠️")

# ============================================================
# 🧩 MANUAL HEALING FORM
# ============================================================
if manual_section:
    st.markdown("## 🧩 Manual Healing")
    with st.form("manual_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        user_id = c1.text_input("User ID", "client_001")
        workflow = c2.selectbox("Workflow", workflow_choices())
        anomaly = c3.selectbox("Anomaly", anomaly_choices())
        note = st.text_area("Optional Note", "Queue pressure detected, SLA risk.", height=70)
        submitted = st.form_submit_button("🚀 Heal Now", use_container_width=True)

    if submitted:
        payload = {"workflow_id": workflow, "anomaly": anomaly, "user_id": user_id, "note": note}
        ok, res = _post_json("/webhook", payload, timeout=HTTP_TIMEOUT)
        if ok:
            st.session_state.latest_manual_result = res
            st.success("✅ Healing completed!")
        else:
            st.error(f"Manual heal error: {res.get('error','unknown')}")

# ============================================================
# 🧾 SLIPS SECTION
# ============================================================
def slip_block(title, result):
    if not result:
        return
    billing = (result.get("billing") or {}) if isinstance(result, dict) else {}
    st.markdown(f"### 🧾 {title}")
    st.markdown(
        f"""
<div class="invoice">
<b>Workflow:</b> {result.get('workflow','')}<br/>
<b>Anomaly:</b> {result.get('anomaly','')}<br/>
<b>Status:</b> {result.get('status','')}<br/>
<b>Recovery:</b> {result.get('recovery_pct','')}<br/>
<b>Reward:</b> {result.get('reward','')}<br/>
<b>User:</b> {billing.get('user','N/A')}<br/>
<b>Amount:</b> ${float(billing.get('amount',0.05)):.2f} | <b>Mode:</b> {billing.get('mode','local')}
</div>
""",
        unsafe_allow_html=True,
    )
    buf = generate_pdf_slip(result)
    st.download_button(
        "📥 Download PDF Slip",
        data=buf,
        file_name=f"healing_slip_{result.get('workflow','')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

col1, col2 = st.columns(2)
with col1:
    slip_block("Latest Auto-Healing Slip", st.session_state.latest_auto_result)
with col2:
    slip_block("Latest Manual Healing Slip", st.session_state.latest_manual_result)

st.markdown("---")

# ============================================================
# 📊 METRICS + CHART
# ============================================================
st.markdown("## 📊 Live Metrics & Anomaly Mix")

ok_sum, summary = _get_json("/metrics/summary")
ok_rev, revenue = _get_json("/metrics/revenue")
if not ok_sum:
    st.warning(f"/metrics/summary error: {summary.get('error','unknown')}")
if not ok_rev:
    st.warning(f"/metrics/revenue error: {revenue.get('error','unknown')}")

summary = summary if isinstance(summary, dict) else {}
revenue = revenue if isinstance(revenue, dict) else {}

k1, k2, k3, k4 = st.columns(4)
k1.markdown(
    f'<div class="kpi"><div class="label">Total Healings</div>'
    f'<div class="value">{int(revenue.get("total_heals", 0) or 0)}</div></div>',
    unsafe_allow_html=True
)
k2.markdown(
    f'<div class="kpi"><div class="label">Total Revenue ($)</div>'
    f'<div class="value">{float(revenue.get("total_revenue", 0.0) or 0.0):.3f}</div></div>',
    unsafe_allow_html=True
)
k3.markdown(
    f'<div class="kpi"><div class="label">Avg Recovery (%)</div>'
    f'<div class="value">{summary.get("avg_recovery_pct", 0)}</div></div>',
    unsafe_allow_html=True
)
k4.markdown(
    f'<div class="kpi"><div class="label">Avg Reward</div>'
    f'<div class="value">{summary.get("avg_reward", 0)}</div></div>',
    unsafe_allow_html=True
)

st.markdown("### ⚙️ Anomaly Distribution")
mix = summary.get("anomaly_mix") or {}
if isinstance(mix, dict) and len(mix) > 0:
    df_mix = pd.DataFrame(list(mix.items()), columns=["Anomaly", "Count"])
    bar = (
        alt.Chart(df_mix)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(x="Anomaly:N", y="Count:Q", tooltip=["Anomaly", "Count"])
        .properties(height=260)
    )
    st.altair_chart(bar, use_container_width=True)
else:
    st.info("Anomaly mix will appear after first healings.")

st.markdown("---")

# ============================================================
# 💰 REVENUE TABLE + LOGS
# ============================================================
c1, c2 = st.columns([1.3, 1])
with c1:
    st.markdown("### 💰 Revenue Records")
    rev_logs = revenue.get("logs") or []
    if isinstance(rev_logs, list) and rev_logs:
        # ensure it frames even if dicts have different keys
        df = pd.json_normalize(rev_logs)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No revenue entries yet.")

with c2:
    st.markdown("### 📜 Healing Logs")
    ok_logs, logs_payload = _get_json("/healing/logs?n=15")
    if ok_logs:
        logs = logs_payload.get("logs") or []
        if logs:
            for log in logs:
                st.code(str(log).rstrip(), language="bash")
        else:
            st.info("No logs yet.")
    else:
        st.error(logs_payload.get("error", "logs fetch failed"))

st.markdown("---")
st.caption("💡 Built for Hackathons • Self-Healing Workflows • Paywalls Monetization • FlowXO Automation")
