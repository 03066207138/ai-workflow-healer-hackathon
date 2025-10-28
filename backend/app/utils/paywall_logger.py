from pathlib import Path
from datetime import datetime
import os

# Always resolve to backend/data/
BASE_DIR = Path(__file__).resolve().parents[2]  # go from /app/utils → /backend
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
PAYWALL_LOG_PATH = DATA_DIR / "healing_revenue.log"

def log_revenue(workflow: str, anomaly: str, recovery_pct: float, success: bool):
    """Simulate Paywalls.ai monetization per healing event."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base_price = 0.05
        multiplier = 1 + (recovery_pct / 100)
        cost = round(base_price * multiplier, 4)
        status = "success" if success else "partial"

        with open(PAYWALL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | {workflow} | {anomaly} | ${cost:.4f} | {status}\n")

        print(f"[Paywalls.ai] 💰 Logged ${cost:.4f} for {workflow}:{anomaly}")

    except Exception as e:
        print(f"[Paywalls.ai] ⚠️ Failed to log revenue: {e}")
