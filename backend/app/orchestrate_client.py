import os
import requests
from groq import Groq

# ============================================================
# 🌐 Hybrid Healing Client
#  - IBM Orchestrate if API key present
#  - Groq (Llama-Versatile 7) fallback when local mode
# ============================================================

class HybridHealingClient:
    def __init__(self):
        # IBM config
        self.ibm_base = os.getenv("IBM_ORCH_BASE_URL", "").rstrip("/")
        self.ibm_key = os.getenv("IBM_ORCH_API_KEY", "")
        self.ibm_skill = os.getenv("IBM_ORCH_SLACK_SKILL", "/skills/postToSlack")

        # Groq config
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("MODEL", "llama-3.1-70b-versatile")

        self.mode = "groq" if not self.ibm_key else "ibm"

        if self.mode == "groq":
            print("🧠 Using Groq Llama model for local healing suggestions.")
            self.groq = Groq(api_key=self.groq_key)
        else:
            print("☁️ Using IBM Orchestrate API for healing actions.")

    # ---------- IBM Skill call ----------
    def post_to_slack_ibm(self, channel: str, message: str):
        url = f"{self.ibm_base}{self.ibm_skill}"
        headers = {"Authorization": f"Bearer {self.ibm_key}"}
        payload = {"channel": channel, "message": message}
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json() if r.text else {"ok": True}

    # ---------- Groq Llama fallback ----------
    def suggest_healing_groq(self, workflow: str, anomaly: str, latency_ms: int):
        prompt = f"""
        Workflow: {workflow}
        Anomaly: {anomaly}
        Latency: {latency_ms}ms

        Suggest 1–2 healing actions to auto-recover this workflow.
        Respond as a JSON list of actions, e.g. ["reroute_task","notify_ops"].
        """
        response = self.groq.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a self-healing workflow agent that suggests corrective actions."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=120,
            temperature=0.6,
        )
        return response.choices[0].message.content.strip()

    # ---------- Unified interface ----------
    def post_to_slack(self, channel: str, message: str):
        """Called by executor — routes to the proper backend."""
        if self.mode == "ibm":
            try:
                return self.post_to_slack_ibm(channel, message)
            except Exception as e:
                print(f"❌ IBM error: {e} → switching to Groq")
                self.mode = "groq"
        # Local AI fallback
        print(f"[LocalAI] {channel}: {message}")
        return {"ok": True}

    def suggest_healing(self, workflow: str, anomaly: str, latency_ms: int):
        """Generate or execute healing actions."""
        if self.mode == "ibm":
            # IBM mode: just return the actions normally handled by policy
            return {"ok": True, "actions": [f"Heal via IBM for {anomaly}"]}
        else:
            try:
                text = self.suggest_healing_groq(workflow, anomaly, latency_ms)
                print(f"[Groq-Llama] 💡 Suggested healing: {text}")
                return {"ok": True, "actions": text}
            except Exception as e:
                print(f"❌ Groq error: {e}")
                return {"ok": False, "actions": []}


# Shared instance
client = HybridHealingClient()
