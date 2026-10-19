UNSAFE_KEYWORDS = [
    "delete all",
    "rm -rf",
    "drop table",
    "destroy everything",
    "terminate ec2",
]

CLARIFICATION_KEYWORDS = [
    "password",
    "secret",
    "database_url",
    "send email",
    "transfer money",
]
def evaluate_action(action):
    """Evaluate an action using AgentX's rule-based checks."""

    # Reject empty or invalid input.
    if not isinstance(action, str) or not action.strip():
        return (
            "NEEDS CLARIFICATION",
            "No action provided. Please enter a valid action.",
        )

    text = action.strip().lower()

    # Check potentially destructive actions first.
    if any(word in text for word in UNSAFE_KEYWORDS):
        return (
            "UNSAFE",
            "Potentially destructive pattern detected.",
        )

    # Check sensitive or consequential actions next.
    if any(word in text for word in CLARIFICATION_KEYWORDS):
        return (
            "NEEDS CLARIFICATION",
            "Sensitive or consequential action detected.",
        )

    # No configured risk pattern was detected.
    return (
        "SAFE TO SIMULATE",
        "No configured risk pattern was detected.",
    )
