# ============================================================
# 💰 Paywalls.ai Client — Real-Time Integration (Prototype-to-Profit Edition)
# ============================================================
# This version fully integrates with Paywalls.ai for real monetization,
# while keeping local fallback logging if API key is missing or fails.

import os
import json
import requests
from datetime import datetime

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
LOG_FILE = "data/healing_revenue.log"

# ============================================================
# 🔧 Configuration
# ============================================================
PAYWALLS_KEY = os.getenv("PAYWALLS_API_KEY") or os.getenv("PAYWALLS_KEY")
PAYWALLS_URL = "https://api.paywalls.ai/v1/user/charge"

# ============================================================
# 💳 Main Billing Function
# ============================================================
def bill_healing_event(user_id: str, heal_type: str, cost: float = 0.05):
    """
    Charge or simulate a Paywalls.ai billing transaction.
    Used after each successful healing cycle.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Case 1: No API key → local simulated billing
    if not PAYWALLS_KEY:
        return _log_local_simulation(user_id, heal_type, cost, timestamp)

    # Case 2: Real Paywalls.ai API call
    try:
        payload = {
            "user": user_id,
            "amount": f"{cost:.2f}",
            "currency": "USD",
            "metadata": {"heal_type": heal_type, "timestamp": timestamp},
        }

        response = requests.post(
            PAYWALLS_URL,
            headers={
                "Authorization": f"Bearer {PAYWALLS_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )

        if response.status_code in [200, 201]:
            data = response.json()
            print(f"[Paywalls.ai] ✅ Real billing successful → ${cost:.2f} for {heal_type}")
            _log_billing_event(user_id, heal_type, cost, "success", "real")
            return {"status": "success", "mode": "real", "response": data}

        else:
            print(f"[Paywalls.ai] ⚠️ Billing failed ({response.status_code}), logging fallback.")
            _log_billing_event(user_id, heal_type, cost, "fallback", "real-failed")
            return {"status": "fallback_logged", "code": response.status_code}

    except Exception as e:
        print(f"[Paywalls.ai] ❌ Exception during real billing: {e}")
        _log_billing_event(user_id, heal_type, cost, "exception", "fallback")
        return {"status": "failed", "error": str(e), "mode": "fallback"}


# ============================================================
# 🧾 Local Logging Utilities
# ============================================================
def _log_local_simulation(user_id, heal_type, cost, timestamp):
    """Simulate billing when no API key is found."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | {user_id} | {heal_type} | ${cost:.4f} | simulated\n")
        print(f"[Paywalls.ai] 💰 Simulated billing for {heal_type} (${cost:.4f})")
        return {
            "timestamp": timestamp,
            "user": user_id,
            "heal_type": heal_type,
            "amount": cost,
            "status": "simulated",
            "mode": "local",
        }
    except Exception as e:
        print(f"[Paywalls.ai] ⚠️ Local log error: {e}")
        return {"status": "failed", "error": str(e)}


def _log_billing_event(user_id, heal_type, cost, status, mode):
    """Log all billing results (both real and simulated)."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | {user_id} | {heal_type} | ${cost:.4f} | {status} | {mode}\n")
    except Exception as e:
        print(f"[Paywalls.ai] ⚠️ Billing log write error: {e}")


def read_billing_history(limit: int = 100):
    """Read recent billing events."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        return [line.strip() for line in lines if line.strip()]
    except Exception as e:
        print(f"[Paywalls.ai] ⚠️ Read error: {e}")
        return []
