# ============================================================
# ⚙️ FlowXO Client — Real-Time Integration (Prototype-to-Profit Edition)
# ============================================================
# This file connects your healing agent with FlowXO automation.
# It supports both incoming webhooks (FlowXO → Healer)
# and outgoing notifications (Healer → FlowXO).

import os
import json
import requests
from datetime import datetime
from fastapi import APIRouter, Request
from app.healing.executor import HealingExecutor
from app.integrations.paywalls_client import bill_healing_event

# Initialize router and healing executor
router = APIRouter()
executor = HealingExecutor()

# Local event log file
os.makedirs("data", exist_ok=True)
LOG_FILE = "data/flowxo_events.log"

# FlowXO webhook URL (for outbound notifications)
FLOWXO_WEBHOOK_URL = os.getenv("FLOWXO_WEBHOOK_URL")

# ============================================================
# 🧭 INCOMING: FlowXO → Healer
# ============================================================
@router.post("/flowxo/webhook")
async def flowxo_trigger(req: Request):
    """
    Called by FlowXO or any automation tool when an anomaly occurs.
    Example payload:
    {
        "workflow_id": "order_processing",
        "anomaly": "queue_pressure",
        "user_id": "client_001"
    }
    """
    data = await req.json()
    workflow_id = data.get("workflow_id", "unknown_workflow")
    anomaly = data.get("anomaly", "unknown_anomaly")
    user_id = data.get("user_id", "demo_client")

    print(f"[FlowXO] ⚡ Incoming anomaly: {workflow_id} / {anomaly} from {user_id}")

    # Run healing logic
    result = executor.heal(workflow_id, anomaly)
    healing_status = result.get("status", "unknown")
    recovery_pct = result.get("recovery_pct", 0)
    reward = result.get("reward", 0)

    # Monetize event
    billing_info = bill_healing_event(user_id, anomaly, cost=0.05)

    # Log the event locally
    _log_flowxo_event(workflow_id, anomaly, healing_status, user_id, recovery_pct, reward, billing_info)

    # Notify FlowXO automation of healing completion
    if FLOWXO_WEBHOOK_URL:
        _notify_flowxo_outbound(workflow_id, anomaly, user_id, healing_status, recovery_pct, reward, billing_info)

    return {
        "workflow": workflow_id,
        "anomaly": anomaly,
        "healing_status": healing_status,
        "recovery_pct": recovery_pct,
        "reward": reward,
        "billing": billing_info
    }


# ============================================================
# 🔁 OUTGOING: Healer → FlowXO
# ============================================================
def _notify_flowxo_outbound(workflow_id, anomaly, user_id, healing_status, recovery_pct, reward, billing_info):
    """
    Send notification back to FlowXO webhook after healing and billing.
    FlowXO can then post messages to Slack, Telegram, or email.
    """
    payload = {
        "workflow_id": workflow_id,
        "anomaly": anomaly,
        "user_id": user_id,
        "healing_status": healing_status,
        "recovery_pct": recovery_pct,
        "reward": reward,
        "amount_charged": billing_info.get("amount", 0),
        "billing_status": billing_info.get("status"),
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"✅ Healing complete for {workflow_id} (Anomaly: {anomaly}) | "
                   f"Recovery: {recovery_pct}% | Charged: ${billing_info.get('amount', 0):.2f}"
    }

    try:
        response = requests.post(FLOWXO_WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code in [200, 201]:
            print(f"[FlowXO] ✅ Outbound notification sent for {workflow_id}")
        else:
            print(f"[FlowXO] ⚠️ Outbound notification failed ({response.status_code})")
    except Exception as e:
        print(f"[FlowXO] ❌ Exception during outbound notification: {e}")


# ============================================================
# 🧾 Logging Utility
# ============================================================
def _log_flowxo_event(workflow_id, anomaly, healing_status, user_id, recovery_pct, reward, billing_info):
    """Log every FlowXO event locally for monitoring."""
    try:
        line = (f"{datetime.utcnow()} | {workflow_id} | {anomaly} | "
                f"{healing_status} | {user_id} | "
                f"Recovery={recovery_pct}% | Reward={reward} | "
                f"Charge=${billing_info.get('amount', 0):.4f}\n")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"[FlowXO] ⚠️ Log write error: {e}")
