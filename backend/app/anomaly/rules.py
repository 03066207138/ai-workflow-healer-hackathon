from typing import Optional, Dict
import random

SLA_OVERSHOOT_MS = {
    "order_processing": 5500,
    "customer_support": 3500,
    "invoice_approval": 4200,
}

ANOMALIES = [
    ("queue_pressure", 0.35),
    ("missing_approval", 0.25),
    ("data_error", 0.20),
    ("workflow_delay", 0.20),
]

def evaluate_rules(workflow: str, latency_ms: int) -> Optional[Dict]:
    overshoot = SLA_OVERSHOOT_MS.get(workflow, 4000)
    if latency_ms > overshoot or random.random() < 0.07:
        r = random.random()
        cumulative = 0.0
        for kind, p in ANOMALIES:
            cumulative += p
            if r < cumulative:
                return {"kind": kind, "severity": "high", "latency_ms": latency_ms}
    return None
