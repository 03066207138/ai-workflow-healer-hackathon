import os
import random
from datetime import datetime, timezone
from ..settings import settings
from ..utils.metrics_logger import MetricsLogger

# ============================================================
# 🧠 IBM Watsonx.ai Integration
# ============================================================
try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import Model
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

    WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
    WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")

    if WATSONX_API_KEY and WATSONX_PROJECT_ID:
        credentials = Credentials(
            url="https://us-south.ml.cloud.ibm.com",
            api_key=WATSONX_API_KEY
        )
        watson_model = Model(
            model_id="meta-llama/llama-3-70b-instruct",
            credentials=credentials,
            params={
                GenParams.MAX_NEW_TOKENS: 100,
                GenParams.TEMPERATURE: 0.6
            },
            project_id=WATSONX_PROJECT_ID
        )
    else:
        watson_model = None
except Exception as e:
    print(f"[Watsonx.ai] ⚠️ Model initialization failed: {e}")
    watson_model = None


class HealingExecutor:
    """
    Executes healing actions using IBM Watsonx.ai reasoning
    for intelligent, adaptive workflow recovery.
    """

    def __init__(self, logger=None):
        self.logger = logger or MetricsLogger(settings.METRICS_LOG_PATH)
        self.log_path = settings.HEALING_LOG_PATH
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    # ------------------------------
    # 🔹 Internal logging helper
    # ------------------------------
    def _append_log(self, line: str):
        """Save log line to healing_log.txt with timestamp."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{ts}] {line}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(entry)
        print(entry.strip())

    # ------------------------------
    # ⚙️ Healing Process
    # ------------------------------
    def heal(self, workflow: str, anomaly: str, latency_ms: int = 0):
        """
        Perform a healing action for a detected anomaly.
        Uses IBM Watsonx.ai for reasoning; falls back to static logic.
        """
        try:
            # Step 1 — Log anomaly detection
            self._append_log(f"⚠️ {workflow} anomaly detected → {anomaly}")

            # Step 2 — Ask Watsonx.ai for recommended healing actions
            actions = []
            if watson_model:
                try:
                    prompt = (
                        f"You are an autonomous workflow-healing AI.\n"
                        f"A system reports anomaly '{anomaly}' in the '{workflow}' workflow.\n"
                        f"Suggest 2–3 concise healing actions to automatically restore stability. "
                        f"Return them as a simple comma-separated list."
                    )
                    response = watson_model.generate_text(prompt)
                    text = response["results"][0]["generated_text"]
                    actions = [a.strip() for a in text.split(",") if a.strip()]
                except Exception as e:
                    print(f"[Watsonx.ai] ⚠️ Reasoning fallback: {e}")
                    actions = []

            # Fallback if Watsonx.ai is offline or response invalid
            if not actions:
                default_actions = {
                    "workflow_delay": ["optimize_scheduler", "scale_up_workers"],
                    "queue_pressure": ["restart_queue", "increase_batching"],
                    "data_error": ["revalidate_pipeline", "notify_owner"],
                    "api_failure": ["switch_backup_endpoint", "retry_request"]
                }
                actions = default_actions.get(anomaly, ["retry_workflow", "notify_owner"])

            self._append_log(f"💡 Suggested healing actions: {actions}")

            # Step 3 — Execute suggested actions (simulated)
            for action in actions:
                if "restart" in action:
                    self._append_log(f"♻️ Restarting service for {workflow}")
                elif "scale" in action:
                    self._append_log(f"📈 Scaling up resources for {workflow}")
                elif "optimize" in action:
                    self._append_log(f"⚙️ Optimizing workflow scheduler for {workflow}")
                elif "retry" in action:
                    self._append_log(f"🔄 Retrying operation for {workflow}")
                elif "validate" in action or "revalidate" in action:
                    self._append_log(f"🧪 Revalidating data pipeline for {workflow}")
                else:
                    self._append_log(f"🛠️ Performing custom action: {action}")

            # Step 4 — Success log
            self._append_log(f"🟢 Healing executed successfully for {workflow} ({anomaly})")

            # Step 5 — Simulated performance metrics
            latency = latency_ms if latency_ms > 0 else random.randint(2000, 15000)
            recovery_pct = round(random.uniform(75, 98), 2)
            reward = round(random.uniform(-0.1, 0.5), 2)

            self.logger.log({
                "workflow": workflow,
                "anomaly": anomaly,
                "action": ", ".join(actions),
                "status": "healed",
                "latency_ms": latency,
                "recovery_pct": recovery_pct,
                "reward": reward
            })

            return {
                "status": "success",
                "actions": actions,
                "recovery_pct": recovery_pct,
                "reward": reward
            }

        except Exception as e:
            # ❌ Handle errors gracefully
            self._append_log(f"❌ Healing failed for {workflow}: {str(e)}")
            self.logger.log({
                "workflow": workflow,
                "anomaly": anomaly,
                "action": "none",
                "status": "failed",
                "latency_ms": latency_ms,
                "recovery_pct": 0.0,
                "reward": -1.0
            })
            return {"status": "failed", "error": str(e)}
