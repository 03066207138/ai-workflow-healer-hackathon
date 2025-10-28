# ============================================================
# 🏆 Hackathon Dashboard — AI Workflow Healer (Streamlit app.py)
# Auto-Healing + Manual Healing + PDF Slips + Live Metrics
# ============================================================

import os
import time
import random
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
BACKEND_URL = os.environ.get("HEALER_BACKEND_URL", "http://127.0.0.1:8000")
AUTO_TRIGGER_SECONDS = 15
AUTO_REFRESH_MS = 5000

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
/* ===============================
   🎨 HACKATHON BRIGHT DARK THEME
   =============================== */

:root {
  --bg: #050912;
  --card: #0c1220;
  --ink: #f9fafb;
  --muted: #cbd5e1;
  --accent: #60a5fa;
  --accent-2: #34d399;
  --warn: #fbbf24;
}

/* ====== GLOBAL ====== */
html, body, .stApp {
  background: radial-gradient(circle at top left, var(--bg), #000814 90%);
  color: var(--ink);
  font-family: "Inter", ui-sans-serif;
}
h1, h2, h3, h4, h5 {
  color: var(--ink);
  font-weight: 700;
}
hr {
  border: none;
  height: 1px;
  background: rgba(255, 255, 255, .15);
  margin: 1rem 0;
}

/* ====== SIDEBAR ====== */
[data-testid="stSidebar"], .sidebar .sidebar-content {
  background: var(--card);
  color: var(--ink) !important;
}
[data-testid="stSidebar"] * {
  color: var(--ink) !important;
  font-weight: 600;
}
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
  color: var(--ink) !important;
}

/* Sidebar Buttons */
[data-testid="stSidebar"] button, 
.sidebar .stButton>button {
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  color: #000814 !important;
  border: none !important;
  font-weight: 700 !important;
  border-radius: 8px;
  margin-top: 5px;
  transition: all 0.2s ease-in-out;
}
[data-testid="stSidebar"] button:hover, 
.sidebar .stButton>button:hover {
  background: linear-gradient(90deg, var(--accent-2), var(--accent));
  transform: scale(1.03);
}

/* Sidebar Toggle Switch Labels */
.stToggleSwitch label {
  color: var(--ink) !important;
  font-weight: 600;
}

/* ====== MAIN BUTTONS ====== */
.stButton>button {
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  color: #000814 !important;
  font-weight: 700 !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 0.5rem 1rem !important;
  transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
  background: linear-gradient(90deg, var(--accent-2), var(--accent));
  transform: scale(1.03);
}

/* ====== DOWNLOAD BUTTONS ====== */
.stDownloadButton>button {
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  color: #000814 !important;
  font-weight: 800 !important;
  border-radius: 10px !important;
  padding: 0.6rem 1rem !important;
  border: none !important;
  box-shadow: 0 0 10px rgba(52, 211, 153, 0.4);
  transition: all 0.3s ease-in-out;
}
.stDownloadButton>button:hover {
  background: linear-gradient(90deg, var(--accent-2), var(--accent));
  transform: scale(1.05);
  box-shadow: 0 0 15px rgba(96, 165, 250, 0.7);
}

/* ====== KPI & CARDS ====== */
.kpi {
  text-align: center;
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
  border: 1px solid rgba(255,255,255,.12);
  box-shadow: 0 8px 28px rgba(0,0,0,.25);
}
.kpi .label { color: var(--muted); font-size: .9rem; }
.kpi .value { color: var(--ink); font-size: 1.8rem; font-weight: 800; }

/* ====== INVOICE BOX ====== */
.invoice {
  background: linear-gradient(180deg, rgba(52, 211, 153, .18), rgba(52, 211, 153, .08));
  border: 1px solid rgba(52, 211, 153, .35);
  border-radius: 14px;
  padding: 14px;
  margin-top: 10px;
  color: var(--ink);
}
/* Animated glow for active Auto-Healing toggle */
.stToggleSwitch [aria-checked="true"] + div label {
  animation: pulse 2s infinite;
  box-shadow: 0 0 12px 2px rgba(96,165,250,0.6);
}

@keyframes pulse {
  0% { box-shadow: 0 0 6px 2px rgba(96,165,250,0.4); }
  50% { box-shadow: 0 0 18px 5px rgba(96,165,250,0.8); }
  100% { box-shadow: 0 0 6px 2px rgba(96,165,250,0.4); }
}

</style>
""", unsafe_allow_html=True)

# ------------------------------
# 🔁 AUTO REFRESH
# ------------------------------
st_autorefresh(interval=AUTO_REFRESH_MS, key="auto_refresh")

# ------------------------------
# 🧰 HELPERS
# ------------------------------
def _post_json(path, payload, timeout=20):
    return requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=timeout)

def _get_json(path, timeout=20):
    return requests.get(f"{BACKEND_URL}{path}", timeout=timeout).json()

def generate_pdf_slip(result: dict) -> BytesIO:
    """✅ Fixed: Generate PDF slip (works with BytesIO)"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_author("AI Workflow Healer")
    pdf.set_title("Healing Billing Slip")

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Workflow Healing Billing Slip", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    billing = result.get("billing", {})
    lines = [
        f"Date: {now}",
        f"User ID: {billing.get('user', 'N/A')}",
        f"Workflow: {result.get('workflow')}",
        f"Anomaly: {result.get('anomaly')}",
        f"Heal Status: {result.get('status')}",
        f"Recovery: {result.get('recovery_pct')}%",
        f"Reward: {result.get('reward')}",
        f"Amount Charged: ${billing.get('amount', 0.05):.2f}",
        f"Mode: {billing.get('mode', 'local')} | Status: {billing.get('status', 'simulated')}",
    ]
    pdf.ln(6)
    for ln in lines:
        pdf.cell(0, 9, ln, ln=True)

    # ✅ Correct way to get PDF bytes
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

st.sidebar.subheader("Modes")
st.session_state.auto_enabled = st.sidebar.toggle("🤖 Auto-Healing", value=True)
manual_section = st.sidebar.toggle("🧩 Manual Healing", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Actions")
if st.sidebar.button("▶️ Single Auto Trigger Now"):
    st.session_state.last_auto = 0.0

if st.sidebar.button("🧪 Simulate Heal (/simulate)"):
    try:
        r = requests.post(f"{BACKEND_URL}/simulate")
        if r.ok:
            st.sidebar.success("Simulated one heal.")
        else:
            st.sidebar.error(f"Failed: {r.status_code}")
    except Exception as e:
        st.sidebar.error(e)

st.sidebar.markdown("---")
st.sidebar.subheader("Data")
try:
    csv = requests.get(f"{BACKEND_URL}/metrics/download").content
    st.sidebar.download_button(
        "⬇️ Download Metrics CSV",
        csv,
        "metrics_log.csv",
        "text/csv",
        use_container_width=True,
    )
except Exception:
    st.sidebar.info("Metrics not ready yet.")

st.sidebar.markdown("---")
st.sidebar.caption("✨ Neon Hackathon Theme — Bright Mode")

# ------------------------------
# 🏷️ HEADER
# ------------------------------
st.markdown(
    """
# 🩺 AI Workflow Healer — Hackathon Command Center  
<span class="badge">⚡ Real-Time Healing</span> 
<span class="badge">💰 Monetization</span> 
<span class="badge">🤖 Automation</span>
""",
    unsafe_allow_html=True,
)

# ============================================================
# 🤖 AUTO-HEALING LOOP
# ============================================================
now = time.time()
if st.session_state.auto_enabled and (now - st.session_state.last_auto > AUTO_TRIGGER_SECONDS):
    st.session_state.last_auto = now
    payload = {
        "workflow_id": random.choice(workflow_choices()),
        "anomaly": random.choice(anomaly_choices()),
        "user_id": random.choice(["client_001", "client_002", "client_003"]),
    }
    try:
        res = _post_json("/webhook", payload, timeout=15)
        if res.ok:
            st.session_state.latest_auto_result = res.json()
            st.toast(
                f"✅ Auto-Heal → {payload['workflow_id']} ({payload['anomaly']}) "
                f"• billed ${st.session_state.latest_auto_result.get('billing',{}).get('amount',0.05):.2f}"
            )
        else:
            st.toast(f"⚠️ Auto-heal failed ({res.status_code})", icon="⚠️")
    except Exception as e:
        st.toast(f"❌ Auto-heal error: {e}", icon="❌")

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
        try:
            res = _post_json("/webhook", payload)
            if res.ok:
                st.session_state.latest_manual_result = res.json()
                st.success("✅ Healing completed!")
            else:
                st.error(f"Failed: {res.status_code}")
        except Exception as e:
            st.error(f"Manual heal error: {e}")

# ============================================================
# 🧾 SLIPS SECTION
# ============================================================
def slip_block(title, result):
    if not result:
        return
    billing = result.get("billing", {})
    st.markdown(f"### 🧾 {title}")
    st.markdown(
        f"""
<div class="invoice">
<b>Workflow:</b> {result.get('workflow')}<br/>
<b>Anomaly:</b> {result.get('anomaly')}<br/>
<b>Status:</b> {result.get('status')}<br/>
<b>Recovery:</b> {result.get('recovery_pct')}%<br/>
<b>Reward:</b> {result.get('reward')}<br/>
<b>User:</b> {billing.get('user','N/A')}<br/>
<b>Amount:</b> ${billing.get('amount',0.05):.2f} | <b>Mode:</b> {billing.get('mode','local')}
</div>
""",
        unsafe_allow_html=True,
    )
    buf = generate_pdf_slip(result)
    st.download_button(
        "📥 Download PDF Slip",
        data=buf,
        file_name=f"healing_slip_{result.get('workflow')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
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

try:
    summary = _get_json("/metrics/summary")
    revenue = _get_json("/metrics/revenue")
except Exception as e:
    st.error(f"Backend not reachable: {e}")
    summary, revenue = {}, {"total_heals": 0, "total_revenue": 0.0, "logs": []}

k1, k2, k3, k4 = st.columns(4)
k1.markdown(f'<div class="kpi"><div class="label">Total Healings</div><div class="value">{revenue.get("total_heals",0)}</div></div>', unsafe_allow_html=True)
k2.markdown(f'<div class="kpi"><div class="label">Total Revenue ($)</div><div class="value">{revenue.get("total_revenue",0.0):.3f}</div></div>', unsafe_allow_html=True)
k3.markdown(f'<div class="kpi"><div class="label">Avg Recovery (%)</div><div class="value">{summary.get("avg_recovery_pct",0)}</div></div>', unsafe_allow_html=True)
k4.markdown(f'<div class="kpi"><div class="label">Avg Reward</div><div class="value">{summary.get("avg_reward",0)}</div></div>', unsafe_allow_html=True)

st.markdown("### ⚙️ Anomaly Distribution")
mix = summary.get("anomaly_mix", {})
if mix:
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
    rev = revenue.get("logs", [])
    if rev:
        df = pd.DataFrame(rev)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No revenue entries yet.")

with c2:
    st.markdown("### 📜 Healing Logs")
    try:
        logs = _get_json("/healing/logs?n=15").get("logs", [])
        if logs:
            for log in logs:
                st.code(log, language="bash")
        else:
            st.info("No logs yet.")
    except Exception as e:
        st.error(e)

st.markdown("---")
st.caption("💡 Built for Hackathons • Self-Healing Workflows • Paywalls Monetization • FlowXO Automation")
