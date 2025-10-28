import csv
import os
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# 🧠 IBM Workflow Healing Agent — Unified Metrics, Monetization & FlowXO Logger
# ============================================================
class MetricsLogger:
    """
    🧩 Unified Metrics + Monetization + FlowXO Logger
    ------------------------------------------------------------
    Handles:
    • Logging workflow healing metrics for dashboards
    • Logging Paywalls.ai revenue data for monetized healing
    • Logging FlowXO webhook-triggered events
    • Self-healing file integrity and summary generation
    """

    def __init__(self, path: Path):
        # Setup paths
        self.path = Path(path).resolve()
        self.headers = [
            "ts", "workflow", "anomaly", "action",
            "status", "latency_ms", "recovery_pct", "reward"
        ]

        # Data directory setup
        self.data_dir = self.path.parent.resolve()
        self.paywall_log_path = (self.data_dir / "healing_revenue.log").resolve()
        self.flowxo_log_path = (self.data_dir / "flowxo_events.log").resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Ensure all log files exist
        for file_path in [self.path, self.paywall_log_path, self.flowxo_log_path]:
            if not file_path.exists():
                open(file_path, "w", encoding="utf-8").close()
                print(f"🆕 [MetricsLogger] Created new log file: {file_path}")

        # Ensure CSV integrity
        self._ensure_file_integrity()

    # ============================================================
    # 🩹 Ensure CSV File Integrity
    # ============================================================
    def _ensure_file_integrity(self):
        """Ensure the metrics CSV file exists and has correct headers."""
        if not self.path.exists() or os.path.getsize(self.path) == 0:
            self._create_new_file()
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip().split(",")
            if first_line != self.headers:
                print("⚠️ [MetricsLogger] Header mismatch detected — rebuilding file...")
                df = pd.read_csv(self.path, header=None)
                df.to_csv(self.path, index=False, header=self.headers)
                print("✅ [MetricsLogger] Header structure repaired successfully.")
        except Exception as e:
            print(f"❌ [MetricsLogger] Error validating CSV. Rebuilding file: {e}")
            self._create_new_file()

    # ============================================================
    # 🆕 Create a New CSV File
    # ============================================================
    def _create_new_file(self):
        """Creates a new metrics CSV file with correct structure."""
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writeheader()
        print(f"🆕 [MetricsLogger] Created new metrics file at: {self.path}")

    # ============================================================
    # 🧠 Log Healing Event
    # ============================================================
    def log(self, row: dict):
        """
        Logs a single healing event in metrics CSV.
        Also logs Paywalls.ai revenue in parallel.
        """
        self._ensure_file_integrity()
        row["ts"] = datetime.now(timezone.utc).isoformat()

        defaults = {
            "workflow": "unknown",
            "anomaly": "unspecified",
            "action": "none",
            "status": "unknown",
            "latency_ms": 0,
            "recovery_pct": 0.0,
            "reward": 0.0
        }
        for key, val in defaults.items():
            row.setdefault(key, val)

        try:
            with open(self.path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writerow(row)
                f.flush()

            print(f"✅ [MetricsLogger] Logged healing event: {row['workflow']} | {row['anomaly']} ({row['status']})")

            # 💰 Monetization Log
            self.log_revenue(
                workflow=row["workflow"],
                anomaly=row["anomaly"],
                recovery_pct=row["recovery_pct"],
                success=row["status"] == "success"
            )

        except Exception as e:
            print(f"❌ [MetricsLogger] Error writing row: {e}")
            self._create_new_file()

    # ============================================================
    # 💰 Paywalls.ai Monetization Logger
    # ============================================================
    def log_revenue(self, workflow: str, anomaly: str, recovery_pct: float, success: bool):
        """Simulate Paywalls.ai monetization for each healing event."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            base_price = 0.05  # Default $0.05 per healing
            multiplier = 1 + (recovery_pct / 100)
            cost = round(base_price * multiplier, 4)
            status = "success" if success else "partial"

            with open(self.paywall_log_path, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} | {workflow} | {anomaly} | ${cost:.4f} | {status}\n")
                f.flush()

            print(f"[Paywalls.ai] 💰 Logged ${cost:.4f} for {workflow}:{anomaly} → {self.paywall_log_path}")
        except Exception as e:
            print(f"[Paywalls.ai] ⚠️ Failed to log revenue: {e}")

    # ============================================================
    # 🔁 FlowXO Event Logger (Fixed: absolute + flush)
    # ============================================================
    def log_flowxo_event(self, workflow: str, anomaly: str, user_id: str):
        """Record FlowXO webhook events for traceability."""
        try:
            abs_path = self.flowxo_log_path.resolve()
            print(f"📂 [DEBUG] Writing to FlowXO log file at: {abs_path}")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(abs_path, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} | {workflow} | {anomaly} | {user_id}\n")
                f.flush()  # Force write immediately

            print(f"[FlowXO] 🌐 Logged webhook: {workflow}:{anomaly} (user: {user_id}) → {abs_path}")
        except Exception as e:
            print(f"[FlowXO] ⚠️ Failed to log FlowXO event: {e}")

    # ============================================================
    # 📊 Generate Summary for Dashboard
    # ============================================================
    def summary(self):
        """Compute average healing metrics for dashboard."""
        self._ensure_file_integrity()

        try:
            df = pd.read_csv(self.path)
            if df.empty:
                return self._empty_summary()

            # Data cleanup
            df = df.dropna(subset=["latency_ms", "recovery_pct", "reward"])
            df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce").fillna(0)
            df["recovery_pct"] = pd.to_numeric(df["recovery_pct"], errors="coerce").fillna(0)
            df["reward"] = pd.to_numeric(df["reward"], errors="coerce").fillna(0)
            df["queue_minutes"] = df["latency_ms"] / 60000.0

            summary_data = {
                "avg_queue_minutes": round(df["queue_minutes"].mean(), 2),
                "avg_recovery_pct": round(df["recovery_pct"].mean(), 2),
                "avg_reward": round(df["reward"].mean(), 2),
                "healings": len(df)
            }

            print(f"📊 [MetricsLogger] Summary updated: {summary_data}")
            return summary_data
        except Exception as e:
            print(f"⚠️ [MetricsLogger] Error computing summary: {e}")
            return self._empty_summary()

    # ============================================================
    # 🪶 Default Summary Helper
    # ============================================================
    def _empty_summary(self):
        """Fallback for missing or invalid data."""
        return {
            "avg_queue_minutes": 0.0,
            "avg_recovery_pct": 0.0,
            "avg_reward": 0.0,
            "healings": 0
        }

# ============================================================
# ✅ Example Test
# ============================================================
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[2]
    metrics_path = BASE_DIR / "data" / "metrics_log.csv"
    logger = MetricsLogger(metrics_path)

    # Example healing event
    logger.log({
        "workflow": "invoice_processing",
        "anomaly": "queue_pressure",
        "action": "restart_queue",
        "status": "success",
        "latency_ms": 3200,
        "recovery_pct": 87.5,
        "reward": 0.22
    })

    # Example FlowXO webhook
    logger.log_flowxo_event("order_processing", "workflow_delay", "client_001")

    print(logger.summary())
