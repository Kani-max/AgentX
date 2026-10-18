
RULES = {
    "unsafe": [
        "delete all",
        "rm -rf",
        "drop table",
        "destroy everything",
        "terminate ec2",
    ],
    "clarify": [
        "password",
        "secret",
        "database_url",
        "send email",
        "transfer money",
    ],
}


def evaluate_action(action):
    text = action.lower().strip()

    if not text:
        return "NEEDS CLARIFICATION", "Please describe the action."

    for keyword in RULES["unsafe"]:
        if keyword in text:
            return "UNSAFE", f"Potentially destructive action: {keyword}"

    for keyword in RULES["clarify"]:
        if keyword in text:
            return "NEEDS CLARIFICATION", (
                f"Sensitive or consequential action: {keyword}"
            )

    return "SAFE TO SIMULATE", (
        "No listed risk pattern detected. This does not guarantee safety."
    )


print("=== AgentX: Smart Action Guardian ===")
print("Demo mode only: no real actions will be executed.")
print("Type 'exit' to quit.\n")

while True:
    action = input("Enter a requested action: ")

    if action.lower().strip() == "exit":
        print("AgentX closed.")
        break

    verdict, reason = evaluate_action(action)
    print(f"Decision: {verdict}")
    print(f"Reason:   {reason}\n")
