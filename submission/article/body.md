# AgentX: Adding a Safety Decision Layer to Tool-Calling AI Agents
By Kanishka K.
AI agents can call tools, but a plausible tool call is not necessarily a safe or authorized one. AgentX explores a separate decision layer that checks a proposed call before it proceeds, asking for clarification when needed and denying unsafe operations.
## The project
AgentX is a safety-focused tool-calling agent for developers building agents that can change data or perform consequential operations.
The current prototype uses Strands Agents and three simulated tools:
- `inspect_action` inspects a known demo action.
- `request_confirmation` records that confirmation is needed.
- `record_safety_decision` records a simulated Proceed, Ask First, or Deny outcome.
The tools use in-memory demo data. They do not connect to production systems or execute real-world operations.
The goal is to make the decision behind a tool call explicit and inspectable rather than relying only on the agent's generated explanation.
## How I built it
The agent is implemented with Strands Agents. The safety questions and intervention logic live in `agent/decision.py`, while the simulated tools live in `agent/tools.py`.
Before a guarded tool call proceeds, the intervention constructs a decision context from the conversation and proposed call, then asks Strands Decider 2B typed questions. The resulting probabilities are mapped to an intervention outcome.
Local development has used the configured AWS User Group Madurai hosted Decider endpoint. The current project has not been deployed to Amazon Bedrock AgentCore, and this article does not claim that an AWS deployment is complete.
## The decision I handed to Strands Decider 2B
The central question is:
Should this specific proposed tool call proceed, wait for clarification or confirmation, or be denied?
AgentX evaluates four dimensions:
1. **Argument grounding (`args_grounded`)** - Are the proposed arguments supported by the conversation, verified tool results, or valid values supplied by the user?
2. **Explicit request (`explicit_request`)** - Did the user actually request this operation, rather than ask a question or discuss a possibility?
3. **Premature action (`premature`)** - Would the call skip a necessary clarification, authorization, or confirmation?
4. **Safety (`unsafe`)** - Is the proposed call itself unsafe or unauthorized?
The distinction between the proposed call and the action mentioned in the conversation matters. For example, recording a simulated denial of a dangerous operation is not the same as executing that dangerous operation.
AgentX uses three intervention outcomes:
- **Proceed:** the configured checks allow the proposed call to continue.
- **Guide / Ask First:** the agent should obtain missing information or confirmation before proceeding.
- **Deny:** the proposed call must not proceed.
The thresholds are policy choices, not guarantees. They need evaluation against representative cases before the pattern is used with real tools.
## Evaluation and limitations
A benchmark snapshot in the generated kit facts records a 12-case test split with 25 decisions. It reports 60% accuracy for Strands Decider 2B and 48% for the `qwen3.5-4b` baseline. Median decision latency was approximately 2.59 seconds for the Decider and 14.36 seconds for the baseline.
These figures are a limited benchmark snapshot, not a validated performance claim for the current AgentX implementation. The decision questions and agent code have changed since earlier benchmark runs, so the results should be rerun with explicit approval before being presented as a current AgentX comparison.
The snapshot also reports 0% accuracy for the `unsafe` question. That is a significant weakness, not a detail to hide. A safety layer must be tested on more representative examples, particularly unsafe and unauthorized calls, before it can be trusted with consequential operations.
The prototype is a demonstration, not a production security boundary. Real deployments would also need authorization checks independent of the model, careful tool design, logging, failure handling, and human confirmation where appropriate.
## The reusable decision pattern
The reusable pattern is in `agent/decision.py`. It defines the typed questions, the tools subject to intervention, the decision thresholds, and the mapping from model answers to Proceed, Guide, or Deny.
To adapt the pattern, a builder should replace the demo tool names with their own guarded tools, rewrite the questions to reflect their authorization policy, and evaluate the thresholds on labelled examples from their use case. The current thresholds are illustrative and should not be copied into production without testing.
## What I learned and what is next
This project highlights that safe tool use depends on more than whether a user request sounds reasonable. The system must examine the exact proposed call, check whether its arguments are grounded, distinguish a question from an instruction, and identify missing authorization or confirmation.
The next steps are to evaluate the revised questions on a held-out set, improve performance on unsafe-call detection, record a demonstration of the current AgentX tools, and assess deployment requirements separately.
## Project status
AgentX currently demonstrates a local safety-decision workflow with simulated tools. AWS deployment and a public demonstration link are not yet verified.
Built with the AWS User Group Madurai Strands Decider hackathon kit.

