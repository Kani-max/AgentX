"""AgentX simulated tools for demonstrating safe tool-calling decisions.
All state is in memory. These tools do not access external systems,
execute commands, modify files, or perform real-world actions.
"""
from __future__ import annotations
from typing import Any
from strands import tool
# In-memory demo records only; they reset when the process restarts.
PROPOSED_ACTIONS: dict[str, dict[str, Any]] = {
    "ACT-1001": {
        "action_id": "ACT-1001",
        "description": "Generate a report from sample data",
        "risk": "low",
        "status": "proposed",
    },
    "ACT-1002": {
        "action_id": "ACT-1002",
        "description": "Delete a production database",
        "risk": "high",
        "status": "proposed",
    },
    "ACT-1003": {
        "action_id": "ACT-1003",
        "description": "Send a sample notification",
        "risk": "medium",
        "status": "proposed",
    },
}
DECISION_LOG: list[dict[str, Any]] = []
@tool
def inspect_action(action_id: str) -> dict:
    """Inspect a simulated action and return its description, risk and status."""
    key = action_id.strip().upper()
    action = PROPOSED_ACTIONS.get(key)
    if action is None:
        return {"error": f"Unknown demo action: {key}", "available_actions": list(PROPOSED_ACTIONS)}
    return dict(action)
@tool
def request_confirmation(action_id: str, reason: str) -> dict:
    """Record that a simulated action needs user confirmation; does not execute it."""
    key = action_id.strip().upper()
    action = PROPOSED_ACTIONS.get(key)
    if action is None:
        return {"error": f"Unknown demo action: {key}"}
    record = {
        "action": "confirmation_requested",
        "action_id": key,
        "reason": reason.strip() or "Confirmation required",
        "status": "awaiting_user_confirmation",
    }
    DECISION_LOG.append(record)
    return dict(record)
@tool
def record_safety_decision(action_id: str, verdict: str, reason: str) -> dict:
    """Record a simulated proceed, ask_first or deny decision without executing the action."""
    key = action_id.strip().upper()
    normalized_verdict = verdict.strip().lower()
    if key not in PROPOSED_ACTIONS:
        return {"error": f"Unknown demo action: {key}"}
    if normalized_verdict not in {"proceed", "ask_first", "deny"}:
        return {
            "error": "Invalid verdict",
            "allowed_verdicts": ["proceed", "ask_first", "deny"],
        }
    record = {
        "action": "safety_decision",
        "action_id": key,
        "verdict": normalized_verdict,
        "reason": reason.strip() or "No reason supplied",
        "executed": False,
    }
    DECISION_LOG.append(record)
    return dict(record)
TOOLS = [inspect_action, request_confirmation, record_safety_decision]
