# ============================================================
# 🧠 IBM Workflow Healing Agent — Unified Metrics Logger v4.1
# Real-Time Safe Logging + Monetization + FlowXO Traceability
# ============================================================

import csv
import os
import threading
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# 📊 Unified Metrics Logger Class
# ============================================================
class MetricsLogger:
    """
    🧩 Unified Metrics + Monetization + FlowXO Logger
    ------------------------------------------------------------
    • Logs workflow healing metrics for dashboards
    • Logs Paywalls.ai monetization events
    • Logs FlowXO webhook-triggered events
    • Ensures file integrity and thread-safe operations
    """

    def __init__(self, path: Path):
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

        # Thread-safety lock
        self.lock = threading.Lock()

        # Duplicate-protection cache
        self._last_flowxo = {}

        # Ensure all log files exist
        for file_path in [self.path, self.paywall_log_path, self.flowxo_log_path]:
            if not file_path.exists():
                open(file_path, "w", encoding="utf-8").close()
                self._print(f"🆕 Created new log file: {file_path}", "yellow")

        # Ensure CSV integrity
        self._ensure_file_integrity()

    # ============================================================
    # 🎨 Helper: Colored Console Output
    # ============================================================
    def _print(self, msg, color="white"):
        colors = {
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "blue": "\033[94m",
            "reset": "\033[0m",
        }
        print(f"{colors.get(color, '')}{msg}{colors['reset']}")

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
                self._print("⚠️ Header mismatch detected — rebuilding file...", "yellow")
                df = pd.read_csv(self.path, header=None)
                df.to_csv(self.path, index=False, header=self.headers)
                self._print("✅ Header structure repaired successfully.", "green")
        except Exception as e:
            self._print(f"❌ Error validating CSV. Rebuilding file: {e}", "red")
            self._create_new_file()

    # ============================================================
    # 🆕 Create a New CSV File
    # ============================================================
    def _create_new_file(self):
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writeheader()
        self._print(f"🆕 Created new metrics file at: {self.path}", "blue")

    # ============================================================
    # 🧠 Log Healing Event
    # ============================================================
    def log(self, row: dict):
        """Logs a single healing event + parallel monetization."""
        self._ensure_file_integrity()
        row["ts"] = datetime.now(timezone.utc).isoformat()

        defaults = {
            "workflow": "unknown",
            "anomaly": "unspecified",
            "action": "none",
            "status": "unknown",
            "latency_ms": 0,
            "recovery_pct": 0.0,
            "reward": 0.0,
        }
        for key, val in defaults.items():
            row.setdefault(key, val)

        try:
            with self.lock:
                with open(self.path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=self.headers)
                    writer.writerow(row)
                    f.flush()

            self._print(
                f"✅ Logged healing: {row['workflow']} | {row['anomaly']} ({row['status']})",
                "green",
            )

            # 💰 Monetization Log
            self.log_revenue(
                workflow=row["workflow"],
                anomaly=row["anomaly"],
                recovery_pct=row["recovery_pct"],
                success=row["status"] == "success",
            )

        except Exception as e:
            self._print(f"❌ Error writing healing log: {e}", "red")
            self._create_new_file()

    # ============================================================
    # 💰 Paywalls.ai Monetization Logger
    # ============================================================
    def log_revenue(self, workflow: str, anomaly: str, recovery_pct: float, success: bool):
        """Simulate Paywalls.ai monetization for each healing event."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            base_price = 0.05  # $0.05 per healing
            multiplier = 1 + (recovery_pct / 100)
            cost = round(base_price * multiplier, 4)
            status = "success" if success else "partial"

            with self.lock:
                with open(self.paywall_log_path, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp} | {workflow} | {anomaly} | ${cost:.4f} | {status}\n")
                    f.flush()

            self._print(
                f"[Paywalls.ai] 💰 Logged ${cost:.4f} for {workflow}:{anomaly}",
                "blue",
            )
        except Exception as e:
            self._print(f"[Paywalls.ai] ⚠️ Failed to log revenue: {e}", "yellow")

    # ============================================================
    # 🔁 FlowXO Event Logger (Duplicate-Safe)
    # ============================================================
    def log_flowxo_event(self, workflow: str, anomaly: str, user_id: str):
        """Record FlowXO webhook events safely with duplicate prevention."""
        try:
            now = datetime.now()
            key = f"{workflow}_{anomaly}_{user_id}"

            # Avoid duplicate logs within 2 seconds
            if key in self._last_flowxo and (now - self._last_flowxo[key]).total_seconds() < 2:
                return
            self._last_flowxo[key] = now

            abs_path = self.flowxo_log_path.resolve()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with self.lock:
                with open(abs_path, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp} | {workflow} | {anomaly} | {user_id}\n")
                    f.flush()

            self._print(
                f"[FlowXO] 🌐 Logged webhook: {workflow}:{anomaly} (user: {user_id})",
                "yellow",
            )
        except Exception as e:
            self._print(f"[FlowXO] ⚠️ Failed to log FlowXO event: {e}", "red")

    # ============================================================
    # 📊 Generate Summary for Dashboard
    # ============================================================
    def summary(self):
        """Compute average healing metrics + total revenue for dashboard."""
        self._ensure_file_integrity()

        try:
            df = pd.read_csv(self.path)
            if df.empty:
                return self._empty_summary()

            # Clean numeric data
            df = df.dropna(subset=["latency_ms", "recovery_pct", "reward"])
            df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce").fillna(0)
            df["recovery_pct"] = pd.to_numeric(df["recovery_pct"], errors="coerce").fillna(0)
            df["reward"] = pd.to_numeric(df["reward"], errors="coerce").fillna(0)
            df["queue_minutes"] = df["latency_ms"] / 60000.0

            summary_data = {
                "avg_queue_minutes": round(df["queue_minutes"].mean(), 2),
                "avg_recovery_pct": round(df["recovery_pct"].mean(), 2),
                "avg_reward": round(df["reward"].mean(), 2),
                "healings": len(df),
            }

            # 💰 Include total revenue
            summary_data["total_revenue"] = self._compute_total_revenue()

            self._print(f"📊 Summary updated: {summary_data}", "green")
            return summary_data
        except Exception as e:
            self._print(f"⚠️ Error computing summary: {e}", "red")
            return self._empty_summary()

    # ============================================================
    # 💵 Compute Total Revenue
    # ============================================================
    def _compute_total_revenue(self) -> float:
        """Aggregate all revenue entries from Paywalls log."""
        total = 0.0
        if os.path.exists(self.paywall_log_path):
            with open(self.paywall_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) >= 4:
                        try:
                            total += float(parts[3].replace("$", "").strip())
                        except:
                            continue
        return round(total, 3)

    # ============================================================
    # 🪶 Default Summary Helper
    # ============================================================
    def _empty_summary(self):
        """Fallback for missing or invalid data."""
        return {
            "avg_queue_minutes": 0.0,
            "avg_recovery_pct": 0.0,
            "avg_reward": 0.0,
            "healings": 0,
            "total_revenue": 0.0,
        }


# ============================================================
# ✅ Example Local Test
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
        "latency_ms": 3500,
        "recovery_pct": 92.5,
        "reward": 0.25,
    })

    # Example FlowXO webhook
    logger.log_flowxo_event("order_processing", "workflow_delay", "client_001")

    # Show summary
    print(logger.summary())
