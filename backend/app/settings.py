# ============================================================
# ✅ SINGLE-ENTRY SYNCHRONIZED SETTINGS MODULE
# Ensures exactly one log entry per healing cycle (no duplicates)
# ============================================================

from pydantic_settings import BaseSettings
from pathlib import Path
from datetime import datetime
import pandas as pd
import os
import hashlib

# ------------------------------------------------------------
# 🌐 Paths Setup
# ------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

METRICS_LOG = DATA_DIR / "metrics_log.csv"
HEALING_LOG = DATA_DIR / "healing_log.txt"
REVENUE_LOG = DATA_DIR / "healing_revenue.log"
LOCK_FILE = DATA_DIR / ".healing_lock"

# ------------------------------------------------------------
# ⚙️ Settings
# ------------------------------------------------------------
class Settings(BaseSettings):
    APP_NAME: str = "IBM Workflow Healing Agent"
    DEBUG: bool = True

    IBM_ORCH_BASE_URL: str = "https://api.ibm.com/orchestrate/v1"
    IBM_ORCH_API_KEY: str = ""
    IBM_ORCH_SLACK_SKILL: str = "/skills/postToSlack"

    GROQ_API_KEY: str = ""
    MODEL: str = "llama-3.1-70b-versatile"

    METRICS_LOG_PATH: Path = METRICS_LOG
    HEALING_LOG_PATH: Path = HEALING_LOG
    REVENUE_LOG_PATH: Path = REVENUE_LOG
    WORKFLOWS_PATH: Path = DATA_DIR / "workflows.json"

    class Config:
        env_file = Path(__file__).resolve().parents[1] / ".env"


settings = Settings()

# ------------------------------------------------------------
# 🧩 Initialization
# ------------------------------------------------------------
def ensure_logs_exist():
    """Ensure all log files exist with headers."""
    if not METRICS_LOG.exists():
        pd.DataFrame(columns=[
            "timestamp", "workflow", "anomaly", "action", "status", "recovery_pct", "reward"
        ]).to_csv(METRICS_LOG, index=False)
        print(f"[Init] Created {METRICS_LOG.name}")

    if not HEALING_LOG.exists():
        with open(HEALING_LOG, "w", encoding="utf-8") as f:
            f.write("timestamp | workflow | anomaly | action | status | recovery_pct\n")
        print(f"[Init] Created {HEALING_LOG.name}")

    if not REVENUE_LOG.exists():
        with open(REVENUE_LOG, "w", encoding="utf-8") as f:
            f.write("timestamp | workflow | anomaly | cost($) | status\n")
        print(f"[Init] Created {REVENUE_LOG.name}")

ensure_logs_exist()

# ------------------------------------------------------------
# 🔒 Lock-based Duplicate Guard
# ------------------------------------------------------------
def _generate_event_hash(workflow: str, anomaly: str, status: str) -> str:
    """Generates a short unique hash per healing event."""
    key = f"{workflow}:{anomaly}:{status}"
    return hashlib.md5(key.encode()).hexdigest()

def _is_recent_duplicate(event_hash: str) -> bool:
    """Checks if the last healing event matches this hash."""
    if LOCK_FILE.exists():
        with open(LOCK_FILE, "r") as f:
            last = f.read().strip()
            if last == event_hash:
                return True
    return False

def _update_lock(event_hash: str):
    """Saves current hash to lock file to prevent same-cycle writes."""
    with open(LOCK_FILE, "w") as f:
        f.write(event_hash)

# ------------------------------------------------------------
# 💰 Unified Healing Logger (Single Write per Event)
# ------------------------------------------------------------
def log_healing_event(workflow: str, anomaly: str, action: str,
                      status: str, recovery_pct: float, reward: float):
    """
    Writes exactly ONE synchronized log entry per unique healing event.
    Uses lock-file hashing to prevent multiple writes in the same cycle.
    """
    ensure_logs_exist()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Check for duplicate
    event_hash = _generate_event_hash(workflow, anomaly, status)
    if _is_recent_duplicate(event_hash):
        print(f"[Skip] Duplicate log ignored for {workflow}:{anomaly}")
        return
    _update_lock(event_hash)

    # ✅ Single synchronized writes
    df_entry = pd.DataFrame([{
        "timestamp": timestamp,
        "workflow": workflow,
        "anomaly": anomaly,
        "action": action,
        "status": status,
        "recovery_pct": round(recovery_pct, 2),
        "reward": round(reward, 2),
    }])
    df_entry.to_csv(METRICS_LOG, mode="a", index=False, header=False)

    with open(HEALING_LOG, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {workflow} | {anomaly} | {action} | {status} | {recovery_pct:.2f}\n")

    base_price = 0.05
    cost = round(base_price * (1 + recovery_pct / 100), 4)
    with open(REVENUE_LOG, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {workflow} | {anomaly} | ${cost:.4f} | {status}\n")

    print(f"[Sync] Logged once: {workflow}:{anomaly} ({status}, {recovery_pct:.1f}%) 💰${cost:.4f}")
