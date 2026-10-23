
"""REUSABLE DECISION PATTERN: AgentX safe tool-call guardrails (#guardrails)

## What it does
AgentX inspects proposed consequential tool calls before they proceed.
It can allow a call, guide the agent to ask for clarification or confirmation,
or deny a call that is unsafe. It also tracks guided calls to prevent
unchanged retries from repeating the same intervention.

## Typed questions
The four typed Decider questions are:
- args_grounded: Are the proposed arguments supported by the conversation
  or verified results?
- explicit_request: Did the user explicitly request this operation?
- premature: Would the call skip necessary clarification, authorization,
  or confirmation?
- unsafe: Is the proposed call itself unsafe or unauthorized?

Each question is defined using Decider.noul with true/false explanations
in the QUESTIONS dictionary below.

## Wiring
OrderActionGuard implements Strands InterventionHandler hooks. It renders
the relevant conversation and proposed tool call, asks the configured
Decider questions, and maps the results to Proceed, Guide, or Deny.
The QUESTIONS definitions, guarded tool names, thresholds, and intervention
logic below are the executable wiring for this pattern.

## Reuse
Reuse this pattern when an agent can propose consequential tool calls.
Adapt the guarded tool names and safety questions to your own tools and
policy. Review the probability thresholds against representative evaluation
cases before production use. AgentX's tools are simulated and this pattern
is a demonstration, not a guarantee of safety.
"""

from __future__ import annotations
import json
import time
from typing import Any
from strands.interventions import Deny, Guide, InterventionHandler, Proceed
from decider_kit import Decider
from decider_kit.patterns.guardrails import render_messages
PATTERN_TAG = "#guardrails"
QUESTIONS: dict[str, dict[str, Any]] = {
    "args_grounded": Decider.noul(
        "Are the proposed tool arguments supported by the conversation, "
        "verified tool results, or valid values explicitly supplied by the user? "
        "Evaluate the arguments for this specific tool call, not whether the "
        "underlying real-world action is safe.",
        {
            "true": (
                "The arguments match the supplied conversation or verified "
                "results. A user-provided action ID is grounded when the "
                "proposed call uses that same ID."
            ),
            "false": (
                "An argument is missing, guessed, invented, contradicts the "
                "conversation, or uses a different action ID from the one "
                "the user specified."
            ),
        },
    ),
    "explicit_request": Decider.noul(
        "Did the user explicitly request the operation represented by this "
        "specific proposed tool call, rather than merely asking a question, "
        "discussing a hypothetical, or expressing interest?",
        {
            "true": (
                "The user clearly requested this operation, such as inspecting "
                "a specified action or recording a specified safety decision."
            ),
            "false": (
                "The user only asked for an explanation, asked what might "
                "happen, discussed a possibility, or omitted information "
                "needed to identify the requested operation."
            ),
        },
    ),
    "premature": Decider.noul(
        "Would carrying out the proposed tool call now skip a necessary "
        "clarification, authorization, or confirmation?",
        {
            "true": (
                "A required detail, authorization, or confirmation is still "
                "missing; the operation must wait."
            ),
            "false": (
                "The proposed operation has the required details and "
                "authorization, and no additional confirmation is needed "
                "for this operation."
            ),
        },
    ),
    "unsafe": Decider.noul(
        "Is the proposed tool call itself unsafe, unauthorized, or in "
        "violation of an explicit safety rule? Judge what the tool actually "
        "does, not merely the dangerous action mentioned in the conversation. "
        "Recording a simulated deny decision is not the same as executing "
        "the dangerous action being denied.",
        {
            "true": (
                "The proposed call would perform or authorize an unsafe "
                "operation, exceed the user's authorization, or violate "
                "an explicit safety rule."
            ),
            "false": (
                "The proposed call is a safe inspection or a simulated "
                "safety record, such as recording a deny decision, and does "
                "not itself perform the dangerous operation."
            ),
        },
    ),
}
# Consequential actions need stronger checks than read-only lookups.
GUARDED_TOOLS = {"refund_order", "cancel_order", "request_confirmation", "record_safety_decision"}
# Conservative probability thresholds.
YES = 0.5
UNSURE_LOW = 0.35
UNSURE_HIGH = 0.65
class OrderActionGuard(InterventionHandler):
    """Evaluate consequential tool calls and prevent unsafe retry loops."""
    name = "agentx-safe-tool-guard"
    def __init__(self, decider: Decider):
        self.decider = decider
        self.log: list[dict[str, Any]] = []
        self._guided: set[str] = set()
    @staticmethod
    def _signature(name: str, args: dict[str, Any]) -> str:
        return name + ":" + json.dumps(args, sort_keys=True, default=str)
    def before_invocation(self, event, **kwargs):
        # A new agent invocation starts a new intervention cycle.
        self._guided.clear()
        return Proceed()
    def before_tool_call(self, event, **kwargs):
        name = event.tool_use["name"]
        args = event.tool_use.get("input") or {}
        # Read-only or otherwise unguarded tools pass through this layer.
        if name not in GUARDED_TOOLS:
            return Proceed()
        signature = self._signature(name, args)
        # The same rejected call must not loop indefinitely.
        if signature in self._guided:
            self.log.append({
                "stage": "tool",
                "pattern": PATTERN_TAG,
                "tool": name,
                "args": args,
                "verdict": "deny",
                "reason": "unchanged_retry",
                "decider_ms": 0,
            })
            return Deny(
                reason=(
                    "This tool call was already rejected and retried without "
                    "changes. Stop retrying and ask the user for new information."
                )
            )
        messages = getattr(getattr(event, "agent", None), "messages", [])
        state = (
            "You are evaluating a proposed consequential tool call for AgentX, "
            "a safety layer for tool-using AI agents.\n"
            "Assess only the supplied conversation and proposed call. Do not "
            "assume that missing authorization or details exist.\n\n"
            f"--- CONVERSATION ---\n{render_messages(messages)}\n\n"
            f"--- PROPOSED TOOL CALL ---\n"
            f"Tool: {name}\n"
            f"Arguments: {json.dumps(args, sort_keys=True, default=str)}"
        )
        started = time.perf_counter()
        answers = self.decider.ask(state, QUESTIONS)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        def probability(key: str) -> float:
            answer = answers[key]
            value = getattr(answer, "p_yes", None)
            if value is None:
                return 0.0
            try:
                return max(0.0, min(1.0, float(value)))
            except (TypeError, ValueError):
                return 0.0
        grounded = probability("args_grounded")
        explicit = probability("explicit_request")
        premature = probability("premature")
        unsafe = probability("unsafe")
        record = {
            "stage": "tool",
            "pattern": PATTERN_TAG,
            "tool": name,
            "args": args,
            "args_grounded": round(grounded, 3),
            "explicit_request": round(explicit, 3),
            "premature": round(premature, 3),
            "unsafe": round(unsafe, 3),
            "decider_ms": elapsed_ms,
        }

        # Missing grounding must be clarified before other uncertain checks.
        if grounded < YES:
            self._guided.add(signature)
            record["verdict"] = "ask_first"
            record["reason"] = "missing_grounding"
            self.log.append(record)
            return Guide(
                feedback=(
                    "Do not execute this consequential action yet. Ask the user "
                    "for the missing details or explicit authorization. Never "
                    "guess values, assume consent, or claim the action succeeded."
                )
            )
        # A positive unsafe score is a reason to deny.
        if unsafe >= YES:
            record["verdict"] = "deny"
            record["reason"] = "unsafe_or_unauthorized"
            self.log.append(record)
            return Deny(
                reason=(
                    "AgentX blocked this tool call because it was judged unsafe "
                    "or unauthorized. Do not retry it; explain the limitation."
                )
            )
        # A consequential action must be explicitly requested.
        # Unclear cases are sent back to the agent to ask the user.
        lo, hi = UNSURE_LOW, UNSURE_HIGH
        if grounded < YES or explicit < YES or premature >= YES:
            self._guided.add(signature)
            record["verdict"] = "ask_first"
            record["reason"] = "missing_details_or_authorization"
            self.log.append(record)
            return Guide(
                feedback=(
                    "Do not execute this consequential action yet. Ask the user "
                    "for the missing details or explicit authorization. Never "
                    "guess values, assume consent, or claim the action succeeded."
                )
            )
        if any(lo <= p <= hi for p in (grounded, explicit, 1.0 - premature)):
            self._guided.add(signature)
            record["verdict"] = "ask_first"
            record["reason"] = "uncertain_decision"
            self.log.append(record)
            return Guide(
                feedback=(
                    "The safety decision is uncertain. Ask the user for "
                    "clarification or confirmation before proceeding."
                )
            )
        record["verdict"] = "proceed"
        record["reason"] = "checks_passed"
        self.log.append(record)
        return Proceed()
