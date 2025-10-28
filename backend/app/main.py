# ============================================================
# 🌐 IBM Workflow Healing Agent — Prototype-to-Profit (v4.0)
# Real-Time Monetization + FlowXO + PDF Slip Generation
# ============================================================

import os
import math
import random
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from io import BytesIO
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from dotenv import load_dotenv
from fpdf import FPDF

# ============================================================
# 🔹 Load Environment Variables
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

# ============================================================
# 📦 Internal Imports
# ============================================================
try:
    from .settings import settings
    from .healing.executor import HealingExecutor
    from .healing import policies
    from .telemetry.simulator import sim
    from .utils.metrics_logger import MetricsLogger
    from .integrations.paywalls_client import bill_healing_event
except ImportError:
    from settings import settings
    from healing.executor import HealingExecutor
    from healing import policies
    from telemetry.simulator import sim
    from utils.metrics_logger import MetricsLogger
    from integrations.paywalls_client import bill_healing_event

# ============================================================
# ⚙️ Initialize Core Components
# ============================================================
os.makedirs("data", exist_ok=True)
metrics_logger = MetricsLogger(Path(settings.METRICS_LOG_PATH))
executor = HealingExecutor()

use_groq = bool(os.getenv("GROQ_API_KEY"))
use_watsonx = bool(os.getenv("WATSONX_API_KEY")) and bool(os.getenv("WATSONX_PROJECT_ID"))
use_paywalls = bool(os.getenv("PAYWALLS_API_KEY") or os.getenv("PAYWALLS_KEY"))
use_flowxo = bool(os.getenv("FLOWXO_WEBHOOK_URL"))
FLOWXO_WEBHOOK = os.getenv("FLOWXO_WEBHOOK_URL")
PAYWALL_LOG = "data/healing_revenue.log"

# ============================================================
# 🚀 FastAPI App Initialization
# ============================================================
app = FastAPI(
    title="IBM Workflow Healing Agent — Monetization & FlowXO Edition",
    version="4.0"
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
# ⚡ Real-Time Webhook Integration (FlowXO / External Systems)
# ============================================================
@app.post("/webhook")
async def webhook_listener(request: Request):
    """Handles incoming webhook events and triggers auto-healing."""
    data = await request.json()
    workflow = data.get("workflow_id", "unknown_workflow")
    anomaly = data.get("anomaly", "unknown_anomaly")
    user_id = data.get("user_id", "demo_client")

    print(f"📡 [Webhook] {workflow} | {anomaly} | User: {user_id}")

    # 🔹 Execute Healing
    result = executor.heal(workflow, anomaly)
    healing_status = result.get("status", "unknown")
    recovery = result.get("recovery_pct", 0)
    reward = result.get("reward", 0)

    # 💰 Monetize Healing
    billing = bill_healing_event(user_id, anomaly, cost=0.05)

    # 🔁 Notify FlowXO
    if FLOWXO_WEBHOOK:
        payload = {
            "workflow_id": workflow,
            "anomaly": anomaly,
            "status": healing_status,
            "recovery_pct": recovery,
            "billing": billing,
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            r = requests.post(FLOWXO_WEBHOOK, json=payload, timeout=8)
            print(f"[FlowXO] Notification sent → {r.status_code}")
        except Exception as e:
            print(f"[FlowXO] ⚠️ Notification failed: {e}")

    metrics_logger.log_flowxo_event(workflow, anomaly, user_id)

    return {
        "workflow": workflow,
        "anomaly": anomaly,
        "status": healing_status,
        "recovery_pct": recovery,
        "reward": reward,
        "billing": billing,
    }

# ============================================================
# ⚙️ Manual Healing Simulation
# ============================================================
@app.post("/simulate")
def simulate(event: str = "workflow_delay"):
    """Simulate one healing cycle."""
    workflow = random.choice(["invoice_processing", "order_processing", "customer_support"])
    anomaly = event if event in policies.POLICY_MAP else random.choice(list(policies.POLICY_MAP.keys()))
    result = executor.heal(workflow, anomaly)
    billing = bill_healing_event("demo_client", anomaly, cost=0.05)

    return {
        "workflow": workflow,
        "anomaly": anomaly,
        "status": result.get("status"),
        "recovery_pct": result.get("recovery_pct"),
        "reward": result.get("reward"),
        "billing": billing,
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
    path = settings.HEALING_LOG_PATH
    if not os.path.exists(path):
        return {"logs": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        logs = [line.strip() for line in lines if line.strip()][-n:]
        logs.reverse()
        return {"logs": logs}
    except Exception as e:
        return {"logs": [f"⚠️ Error reading logs: {e}"]}

# ============================================================
# 📊 Metrics Summary & Download
# ============================================================
@app.get("/metrics/summary")
def metrics_summary():
    summary = metrics_logger.summary()
    clean = {}
    for k, v in summary.items():
        try:
            val = float(v)
            if math.isnan(val) or math.isinf(val):
                val = 0.0
            clean[k] = round(val, 2)
        except:
            clean[k] = v

    # Anomaly distribution
    try:
        if os.path.exists(settings.METRICS_LOG_PATH):
            df = pd.read_csv(settings.METRICS_LOG_PATH)
            clean["anomaly_mix"] = df["anomaly"].dropna().value_counts().to_dict()
    except Exception:
        clean["anomaly_mix"] = {}
    return clean

@app.get("/metrics/download")
def download_metrics():
    if not os.path.exists(settings.METRICS_LOG_PATH):
        raise HTTPException(status_code=404, detail="No metrics found.")
    return FileResponse(settings.METRICS_LOG_PATH, media_type="text/csv", filename="metrics_log.csv")

# ============================================================
# 💹 Monetization Data
# ============================================================
@app.get("/metrics/revenue")
def get_revenue():
    data = []
    total_rev = 0
    total_heals = 0
    if os.path.exists(PAYWALL_LOG):
        with open(PAYWALL_LOG, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.strip().split("|")]
                if len(parts) >= 4:
                    ts, wf, anom, cost = parts[:4]
                    try:
                        val = float(cost.replace("$", "").strip())
                    except:
                        val = 0.0
                    total_rev += val
                    total_heals += 1
                    data.append({
                        "Timestamp": ts,
                        "Workflow": wf,
                        "Anomaly": anom,
                        "Cost ($)": val
                    })
    return {
        "total_revenue": round(total_rev, 3),
        "total_heals": total_heals,
        "logs": data
    }

# ============================================================
# 🧾 Healing Slip PDF Generator
# ============================================================
def generate_pdf_slip(result: dict) -> BytesIO:
    """Generate a small PDF slip for healing events."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Workflow Healing Slip", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    billing = result.get("billing", {})
    lines = [
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"User: {billing.get('user', 'N/A')}",
        f"Workflow: {result.get('workflow')}",
        f"Anomaly: {result.get('anomaly')}",
        f"Status: {result.get('status')}",
        f"Recovery: {result.get('recovery_pct', 0)}%",
        f"Reward: {result.get('reward', 0)}",
        f"Amount Charged: ${billing.get('amount', 0.05):.2f}",
    ]
    pdf.ln(6)
    for l in lines:
        pdf.cell(0, 9, l, ln=True)

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return BytesIO(pdf_bytes)

@app.post("/generate-slip")
async def generate_slip(request: Request):
    """Endpoint to generate healing slip PDF from payload."""
    result = await request.json()
    pdf_bytes = generate_pdf_slip(result)
    filename = f"healing_slip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})

# ============================================================
# 🚀 Startup Log
# ============================================================
@app.on_event("startup")
def startup():
    print("\n🚀 IBM Workflow Healing Agent (v4.0) started successfully!")
    print(f"   ▪ App: {settings.APP_NAME}")
    print(f"   ▪ FlowXO Connected: {use_flowxo}")
    print(f"   ▪ Paywalls.ai Enabled: {use_paywalls}")
    print(f"   ▪ Mode: {'Watsonx.ai' if use_watsonx else ('Groq Local' if use_groq else 'Offline')}")
    print(f"   ▪ Metrics Path: {metrics_logger.flowxo_log_path.resolve()}")
    print(f"   ▪ Loaded Policies: {list(policies.POLICY_MAP.keys())}\n")
