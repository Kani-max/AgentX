"""AgentX: a safety-focused tool-calling agent using Strands and Decider."""
from __future__ import annotations
import os
import time
from typing import Any
from strands import Agent
from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, image_blocks, strip_thinking
from .decision import OrderActionGuard
from .tools import TOOLS
NAME = "AgentX: Safe Tool-Calling Agent"
SYSTEM_PROMPT = """You are AgentX, a safety-focused assistant that demonstrates
how consequential tool calls can be reviewed before execution.
Your available tools operate on simulated in-memory demo data only.
They do not execute real-world actions.
Follow these rules:
1. Understand the user's intent before proposing a tool call.
2. Never invent an action ID or claim that an action was executed when it was not.
3. Use inspect_action when you need to inspect a known demo action.
4. Use request_confirmation when the user must explicitly approve a proposed action.
5. Use record_safety_decision only to record a simulated verdict.
6. Explain decisions clearly and honestly.
7. Treat proceed, ask_first, and deny as distinct outcomes:
   - proceed: the safety checks allow the proposed tool call;
   - ask_first: clarification or confirmation is needed;
   - deny: the action must not proceed.
8. A decision record is not proof that a real action was executed.
9. Do not claim that the safety layer is infallible. Be transparent about uncertainty.
Keep responses concise and helpful."""
# Optional demo mode. This intentionally encourages premature proposals so
# the intervention layer can be demonstrated catching them. Use only with
# simulated tools and clearly label the behavior in a presentation.
EAGER_PROMPT = """You are AgentX in a controlled safety demonstration.
Propose a relevant simulated tool call quickly, even when the request is
underspecified, so the safety intervention can demonstrate its response.
Never invent an action ID. Never claim a real-world action occurred.
All available tools are simulated and affect in-memory demo records only."""
class HackathonAgent:
    """One Strands agent per session, with the AgentX decision layer attached."""
    def __init__(
        self,
        decider: Decider | None = None,
        model_id: str | None = None,
        eager: bool | None = None,
    ):
        self.decider = decider or Decider()
        self.eager = eager if eager is not None else os.environ.get("DEMO_EAGER") == "1"
        self.model_id = model_id or default_model_id()
        self.sessions: dict[str, tuple[Agent, OrderActionGuard]] = {}
    def _session(self, session_id: str) -> tuple[Agent, OrderActionGuard]:
        if session_id not in self.sessions:
            guard = OrderActionGuard(self.decider)
            agent = Agent(
                model=agent_model(self.model_id),
                system_prompt=EAGER_PROMPT if self.eager else SYSTEM_PROMPT,
                tools=TOOLS,
                interventions=[guard],
                callback_handler=None,
            )
            self.sessions[session_id] = (agent, guard)
        return self.sessions[session_id]
    def chat(
        self,
        message: str,
        session_id: str = "default",
        images: list[Any] | None = None,
    ) -> dict[str, Any]:
        """Run a message and return the reply, decisions, model ID and latency."""
        agent, guard = self._session(session_id)
        before = len(guard.log)
        started = time.perf_counter()
        result = agent(
            [*image_blocks(images), {"text": message}] if images else message,
            invocation_state={"images": list(images or [])},
        )
        reply = strip_thinking(str(result))
        return {
            "reply": reply,
            "decisions": guard.log[before:],
            "model_id": self.model_id,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "agent": NAME,
            "eager": self.eager,
        }
if __name__ == "__main__":
    import json
    import sys
    instance = HackathonAgent()
    prompts = sys.argv[1:] or [
        "What demo actions can AgentX inspect?",
        "Inspect action ACT-1002 and explain its risk.",
        "Why should a consequential action require confirmation?",
    ]
    for prompt in prompts:
        print(json.dumps(instance.chat(prompt), indent=2))
