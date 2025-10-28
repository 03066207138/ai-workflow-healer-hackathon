# ============================================================
# 🧠 Healing Policy Action Map
# ============================================================

from typing import List

POLICY_MAP = {
    "queue_pressure": ["reroute_to_low_queue", "restart_queue_worker"],
    "data_error": ["rollback_last_step", "open_ticket", "revalidate_data_source"],
    "workflow_delay": ["scale_workers", "restart_node", "optimize_scheduler"],
    "api_failure": ["switch_to_backup_endpoint", "retry_request", "refresh_token"],
}

def actions_for(anomaly_kind: str) -> List[str]:
    """Return list of healing actions for the anomaly type."""
    return POLICY_MAP.get(anomaly_kind, ["notify_ops"])
