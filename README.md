# AgentX - Smart Action Guardian



A rule-based safety evaluation dashboard that classifies proposed actions by risk indicators and maintains a local history of evaluation results.



\## Overview



AgentX is a Python Flask web application designed to demonstrate how configurable safety rules can help identify potentially unsafe or sensitive actions before they are considered for execution.



The application evaluates submitted text, assigns a classification, explains the result, and displays recent evaluation history.



\*\*Note:\*\* AgentX evaluates text using configured keyword rules. It does not execute the submitted actions or guarantee detection of every unsafe request.



\## Features



\- \*\*Rule-based classification\*\* — Categorizes submitted actions using configurable keyword lists.

\- \*\*Three safety outcomes\*\* — `UNSAFE`, `NEEDS CLARIFICATION`, and `SAFE TO SIMULATE`.

\- \*\*Rule priority\*\* — Unsafe keyword matches take priority over clarification matches.

\- \*\*Decision history\*\* — Records recent evaluations in a local JSON file.

\- \*\*Dashboard interface\*\* — Provides a web interface for submitting actions and viewing results.

\- \*\*Automated tests\*\* — Uses Python's `unittest` framework to verify core classification behavior.



\## Technology Stack



\- Python

\- Flask

\- HTML and CSS

\- JSON for local decision-history storage

\- `unittest` for automated testing

\- Git and GitHub for version control



\## Project Structure



```text

AgentX/

├── app.py                  # Flask dashboard and safety rules

├── app\_backup.py           # Backup copy of the application

├── agentx.py               # Supporting AgentX module

├── test\_agentx.py          # Automated safety tests

├── README.md               # Project documentation

├── .gitignore              # Files excluded from Git

└── decision\_history.json   # Local decision history (not published)

```



\## Getting Started



\### 1. Requirements



\- Python installed on your computer

\- pip, Python's package installer



\### 2. Install Flask



Open a terminal in the project directory and run:



```bash

python -m pip install flask

```



\### 3. Start AgentX



Run:



```bash

python app.py

```



Open the following address in your browser:



http://127.0.0.1:5000



To stop the local server, press `Ctrl + C` in the terminal.



\## Run the Tests



From the project directory, run:



```bash

python -m unittest test\_agentx -v

```



The current test suite covers unsafe actions, actions requiring clarification, safe-to-simulate examples, case-insensitive matching, and unsafe-rule priority.



\## Safety Classifications



| Classification | Meaning |

|---|---|

| `UNSAFE` | A configured unsafe keyword was detected. |

| `NEEDS CLARIFICATION` | A configured sensitive-action keyword was detected, with no unsafe keyword match. |

| `SAFE TO SIMULATE` | No configured keyword pattern was detected. |



These classifications are based on the configured rules, not a complete security analysis. A result of `SAFE TO SIMULATE` does not mean an action is guaranteed to be safe.



\## Data and Privacy



\- Evaluation history is stored locally in `decision\_history.json`.

\- The history file is excluded from Git using `.gitignore`.

\- Do not submit real passwords, API keys, private information, or other secrets to the dashboard.

\- Review changes to `.gitignore` before committing files to the repository.



\## Current Limitations



\- Classification relies on predefined keyword matching.

\- Context and meaning may not be understood correctly.

\- The application is a local demonstration, not a production security enforcement system.

\- The current rules do not guarantee protection against every harmful action.



\## Future Improvements



\- Expand automated tests with additional edge cases.

\- Add configurable safety policies.

\- Improve decision explanations and audit reporting.

\- Add more robust input validation and security controls.

\- Explore integration with an AI agent for additional contextual analysis.



\## Author



\*\*Kanishka K\*\*



Student developer | Python | Web Development | AI Safety Projects



\## License



No license has been specified yet. All rights are reserved unless a license is added to this repository.



