# ============================================================
# 🌐 IBM Workflow Healing Agent — Prototype-to-Profit Edition
# Real-Time Integration: Paywalls.ai + FlowXO
# ============================================================

from dotenv import load_dotenv
import os
import math
import random
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from io import BytesIO

# ============================================================
# 🔹 Load Environment Variables and Imports
# ============================================================
load_dotenv()
print(
    "🔑 Loaded keys — Watsonx:",
    str(os.getenv("WATSONX_API_KEY"))[:10],
    "| Groq:",
    str(os.getenv("GROQ_API_KEY"))[:10],
    "| Paywalls:",
    str(os.getenv("PAYWALLS_API_KEY") or os.getenv("PAYWALLS_KEY"))[:10],
    "| FlowXO:",
    str(os.getenv("FLOWXO_WEBHOOK_URL"))[:25],
)

from .settings import settings
from .healing.executor import HealingExecutor
from .healing import policies
from .telemetry.simulator import sim
from .utils.metrics_logger import MetricsLogger
from .integrations.paywalls_client import bill_healing_event

# ============================================================
# ⚙️ Initialize Core Components
# ============================================================
metrics_logger = MetricsLogger(Path(settings.METRICS_LOG_PATH))
executor = HealingExecutor()

use_groq = bool(os.getenv("GROQ_API_KEY"))
use_watsonx = bool(os.getenv("WATSONX_API_KEY")) and bool(os.getenv("WATSONX_PROJECT_ID"))
use_paywalls = bool(os.getenv("PAYWALLS_API_KEY") or os.getenv("PAYWALLS_KEY"))
use_flowxo = bool(os.getenv("FLOWXO_WEBHOOK_URL"))
FLOWXO_WEBHOOK = os.getenv("FLOWXO_WEBHOOK_URL")

# ============================================================
# 🚀 Initialize FastAPI App
# ============================================================
app = FastAPI(
    title="IBM Workflow Healing Agent — Real-Time Monetization Edition",
    version="3.5"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 🩺 Health Check
# ============================================================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "watsonx_ready": use_watsonx,
        "groq_ready": use_groq,
        "paywalls_ready": use_paywalls,
        "flowxo_ready": use_flowxo,
        "mode": (
            "Watsonx.ai"
            if use_watsonx
            else ("Groq Local AI" if use_groq else "Offline Simulation")
        ),
    }

# ============================================================
# ⚡ Real-Time Webhook Endpoint (FlowXO / External Systems)
# ============================================================
@app.post("/webhook")
async def receive_event(request: Request):
    """
    Real-time listener for workflow anomalies.
    Can be triggered by FlowXO, Zapier, or custom APIs.
    """
    data = await request.json()
    workflow_id = data.get("workflow_id", "unknown_workflow")
    anomaly = data.get("anomaly", "unknown_anomaly")
    user_id = data.get("user_id", "demo_client")

    print(f"📡 [Webhook] Event → Workflow: {workflow_id}, Anomaly: {anomaly}, User: {user_id}")

    # 🔹 Execute Healing
    result = executor.heal(workflow_id, anomaly)
    healing_status = result.get("status", "unknown")
    recovery_pct = result.get("recovery_pct", 0)
    reward = result.get("reward", 0)

    # 💰 Monetization
    billing = bill_healing_event(user_id, anomaly, cost=0.05)

    # 🔁 Notify FlowXO of Healing Completion
    if FLOWXO_WEBHOOK:
        payload = {
            "workflow_id": workflow_id,
            "anomaly": anomaly,
            "user_id": user_id,
            "healing_status": healing_status,
            "recovery_pct": recovery_pct,
            "reward": reward,
            "billing": billing,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"✅ Healed {workflow_id} ({anomaly}) | Recovery: {recovery_pct}% | Charged: ${billing.get('amount', 0.05):.2f}"
        }
        try:
            response = requests.post(FLOWXO_WEBHOOK, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                print(f"[FlowXO] ✅ Notification sent for {workflow_id}")
            else:
                print(f"[FlowXO] ⚠️ FlowXO response {response.status_code}")
        except Exception as e:
            print(f"[FlowXO] ❌ Error sending FlowXO update: {e}")

    # Log event for metrics / dashboard
    metrics_logger.log_flowxo_event(workflow_id, anomaly, user_id)

    return {
        "workflow": workflow_id,
        "anomaly": anomaly,
        "status": healing_status,
        "recovery_pct": recovery_pct,
        "reward": reward,
        "billing": billing,
    }

# ============================================================
# ⚙️ Manual Healing Simulation
# ============================================================
@app.post("/simulate")
def simulate(event: str = "workflow_delay"):
    workflow = random.choice(["invoice_processing", "order_processing", "customer_support"])
    anomaly = event if event in policies.POLICY_MAP else random.choice(list(policies.POLICY_MAP.keys()))
    result = executor.heal(workflow, anomaly)

    billing_info = bill_healing_event(
        user_id="demo_client",
        heal_type=anomaly,
        cost=0.05,
    )

    return {
        "workflow": workflow,
        "anomaly": anomaly,
        "suggested_actions": result.get("actions", []),
        "status": result.get("status"),
        "recovery_pct": result.get("recovery_pct"),
        "reward": result.get("reward"),
        "engine": "Watsonx.ai" if use_watsonx else ("Groq Local" if use_groq else "Fallback"),
        "billing": billing_info,
    }

# ============================================================
# 🧪 Continuous Simulation Routes
# ============================================================
@app.post("/sim/start")
def start_simulation():
    print("🚀 Continuous simulation started.")
    return sim.start()

@app.post("/sim/stop")
def stop_simulation():
    print("🧊 Simulation stopped.")
    return sim.stop()

# ============================================================
# 📜 Healing Logs
# ============================================================
@app.get("/healing/logs")
def get_healing_logs(n: int = 50):
    log_path = settings.HEALING_LOG_PATH
    if not os.path.exists(log_path):
        return {"logs": []}
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        logs = [line.strip() for line in lines if line.strip()][-n:]
        logs.reverse()
        return {"logs": logs}
    except Exception as e:
        return {"logs": [f"⚠️ Error reading logs: {str(e)}"]}

# ============================================================
# 📊 Metrics Download
# ============================================================
@app.get("/metrics/download")
def metrics_download():
    if not os.path.exists(settings.METRICS_LOG_PATH):
        raise HTTPException(status_code=404, detail="No metrics file found.")
    return FileResponse(settings.METRICS_LOG_PATH, media_type="text/csv", filename="metrics_log.csv")

# ============================================================
# 📈 Metrics Summary for Dashboard
# ============================================================
@app.get("/metrics/summary")
def metrics_summary():
    summary = metrics_logger.summary()
    clean_summary = {}
    for k, v in summary.items():
        try:
            val = float(v)
            if math.isnan(val) or math.isinf(val):
                val = 0.0
            clean_summary[k] = round(val, 2)
        except Exception:
            clean_summary[k] = v

    anomaly_mix = {}
    try:
        if os.path.exists(settings.METRICS_LOG_PATH):
            df = pd.read_csv(settings.METRICS_LOG_PATH)
            if not df.empty and "anomaly" in df.columns:
                df = df.dropna(subset=["anomaly"])
                anomaly_mix = df["anomaly"].value_counts().to_dict()
    except Exception as e:
        print(f"[Metrics Summary] ⚠️ Failed to parse anomaly mix: {e}")
    clean_summary["anomaly_mix"] = anomaly_mix

    try:
        if os.path.exists(settings.METRICS_LOG_PATH):
            df = pd.read_csv(settings.METRICS_LOG_PATH)
            clean_summary["last_action"] = str(df["action"].iloc[-1]) if "action" in df.columns else "N/A"
    except Exception:
        clean_summary["last_action"] = "N/A"
    return clean_summary

# ============================================================
# 💹 Monetization Data for Dashboard
# ============================================================
PAYWALL_LOG = "data/healing_revenue.log"
os.makedirs("data", exist_ok=True)

@app.get("/metrics/revenue")
def get_revenue_data():
    data = []
    total_revenue = 0.0
    total_heals = 0
    restart_marker = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(PAYWALL_LOG):
        with open(PAYWALL_LOG, "r", encoding="utf-8") as f:
            for line in f.readlines():
                parts = line.strip().split("|")
                if len(parts) >= 4 and restart_marker in parts[0]:
                    ts, workflow, anomaly, cost, *_ = [p.strip() for p in parts]
                    try:
                        cost_val = float(cost.replace("$", "").strip())
                    except:
                        cost_val = 0.0
                    total_revenue += cost_val
                    total_heals += 1
                    data.append({
                        "Timestamp": ts,
                        "Workflow": workflow,
                        "Anomaly": anomaly,
                        "Cost ($)": cost_val
                    })

    return {
        "total_revenue": round(total_revenue, 4),
        "total_heals": total_heals,
        "logs": data
    }

# ============================================================
# 🚀 Startup Message
# ============================================================
@app.on_event("startup")
def startup_event():
    print("\n🚀 IBM Workflow Healing Agent (Prototype-to-Profit) started successfully!")
    print(f"   ▪ App: {settings.APP_NAME}")
    print(f"   ▪ Paywalls.ai Integrated: {use_paywalls}")
    print(f"   ▪ FlowXO Connected: {use_flowxo}")
    print(f"   ▪ Log Path: {metrics_logger.flowxo_log_path.resolve()}")
    if use_watsonx:
        print("   ▪ Mode: IBM Watsonx.ai 🧠")
    elif use_groq:
        print("   ▪ Mode: Groq Local Llama ⚡")
    else:
        print("   ▪ Mode: Offline Fallback (Static Policies)")
    print(f"   ▪ Loaded Policies: {list(policies.POLICY_MAP.keys())}\n")





# #################################################################

def generate_pdf_slip(result: dict) -> BytesIO:
    """Create a small PDF slip for a healing event."""
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

    # ✅ Correct way: output PDF as bytes in memory
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return BytesIO(pdf_bytes)

    """Create a small PDF slip for a healing event."""
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

    # ✅ Correct way to get PDF bytes in memory
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return BytesIO(pdf_bytes)
