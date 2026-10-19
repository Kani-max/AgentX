
from flask import Flask, request, render_template_string
from datetime import datetime
from pathlib import Path
import json

app = Flask(__name__)

# Persistent local decision history
HISTORY_FILE = Path(__file__).with_name("decision_history.json")
MAX_HISTORY = 50

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


def load_history():
    """Load valid saved decisions from the local JSON file."""
    if not HISTORY_FILE.exists():
        return []

    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))

        if not isinstance(data, list):
            return []

        valid_history = []

        for item in data:
            if not isinstance(item, dict):
                continue

            if not all(
                isinstance(item.get(key), str)
                for key in ("time", "action", "result", "css")
            ):
                continue

            if item["result"] not in (
                "UNSAFE",
                "NEEDS CLARIFICATION",
                "SAFE TO SIMULATE",
            ):
                continue

            if item["css"] not in ("unsafe", "clarify", "safe"):
                continue

            valid_history.append({
                "time": item["time"],
                "action": item["action"][:1000],
                "result": item["result"],
                "css": item["css"],
            })

            if len(valid_history) >= MAX_HISTORY:
                break

        return valid_history

    except (OSError, json.JSONDecodeError):
        print("Warning: Could not read decision_history.json.")
        return []


decision_history = load_history()


def save_history():
    """Save the latest decisions safely to a local JSON file."""
    temporary_file = HISTORY_FILE.with_suffix(".tmp")

    try:
        temporary_file.write_text(
            json.dumps(
                decision_history[:MAX_HISTORY],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        temporary_file.replace(HISTORY_FILE)

    except OSError as error:
        print(f"Warning: Could not save decision history: {error}")

        try:
            if temporary_file.exists():
                temporary_file.unlink()
        except OSError:
            pass



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

    return (
        "SAFE TO SIMULATE",
        "No configured risk pattern was detected.",
    )


HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgentX | Security Dashboard</title>
<style>
:root {
    --bg: #080e1b;
    --sidebar: #0b1425;
    --panel: #101c30;
    --panel-hover: #14243b;
    --border: #243550;
    --text: #e8eef8;
    --muted: #8da1bd;
    --blue: #3995ff;
    --blue-hover: #2378e5;
    --green: #38d9a9;
    --red: #ff7185;
    --yellow: #ffc96b;
}

* { box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: Inter, "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}

button, input, textarea, select { font: inherit; }
button, a { -webkit-tap-highlight-color: transparent; }
a { color: inherit; text-decoration: none; }

.app {
    min-height: 100vh;
    display: grid;
    grid-template-columns: 240px minmax(0, 1fr);
}

.sidebar {
    background: var(--sidebar);
    border-right: 1px solid var(--border);
    padding: 25px 16px;
    display: flex;
    flex-direction: column;
    gap: 28px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 8px;
}

.brand-icon {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 13px;
    background: linear-gradient(135deg, #174b91, #172e59);
    color: #8ed1ff;
    font-size: 22px;
    box-shadow: 0 0 25px #1c66a526;
}

.brand-name {
    font-size: 21px;
    font-weight: 750;
    letter-spacing: -.6px;
}

.brand-caption {
    color: var(--muted);
    font-size: 10px;
    margin-top: 4px;
}

.nav-label {
    color: #657b9b;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 0 12px;
    margin-bottom: 10px;
}

.nav { display: grid; gap: 7px; }

.nav a {
    padding: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-radius: 9px;
    color: #a5b6ce;
    transition: .2s;
}

.nav a:hover, .nav a.active {
    background: #18375c;
    color: #e6f3ff;
}

.nav a.active { box-shadow: inset 3px 0 var(--blue); }
.nav-icon { width: 20px; text-align: center; }

.sidebar-bottom {
    margin-top: auto;
    padding: 14px;
    border: 1px solid var(--border);
    background: #0e1b2d;
    border-radius: 12px;
}

.local-status {
    color: var(--green);
    font-size: 12px;
    font-weight: 700;
}

.sidebar-bottom p {
    color: var(--muted);
    font-size: 11px;
    line-height: 1.6;
    margin-bottom: 0;
}

main {
    padding: 30px;
    max-width: 1600px;
    width: 100%;
    margin: 0 auto;
    min-width: 0;
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
    margin-bottom: 30px;
}

.eyebrow {
    color: var(--blue);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.6px;
    margin-bottom: 9px;
}

h1 {
    margin: 0;
    font-size: clamp(25px, 3vw, 32px);
    letter-spacing: -1px;
}

.subtitle {
    color: var(--muted);
    margin: 9px 0 0;
    line-height: 1.6;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 8px 12px;
    border: 1px solid #22684f;
    background: #0d2a25;
    color: #64e6ba;
    border-radius: 30px;
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
}

.status-dot {
    width: 7px;
    height: 7px;
    background: var(--green);
    border-radius: 50%;
}

.stats {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    margin-bottom: 23px;
}

.stat-card, .panel {
    background: linear-gradient(145deg, #111f34, #0d1829);
    border: 1px solid var(--border);
    border-radius: 14px;
}

.stat-card {
    padding: 19px;
    min-width: 0;
}

.stat-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
}

.stat-label { color: var(--muted); font-size: 12px; }

.stat-icon {
    width: 34px;
    height: 34px;
    display: grid;
    place-items: center;
    border-radius: 10px;
    background: #19314e;
    font-size: 17px;
}

.stat-number {
    font-size: 30px;
    font-weight: 750;
    margin-top: 15px;
    letter-spacing: -1px;
}

.stat-foot {
    color: var(--muted);
    font-size: 11px;
    margin-top: 5px;
}

.blue { color: #69b7ff; }
.red { color: var(--red); }
.yellow { color: var(--yellow); }
.green { color: var(--green); }

.panel {
    padding: 24px;
    margin-bottom: 23px;
    min-width: 0;
}

.panel-heading {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 20px;
}

.panel-heading h2 { margin: 0; font-size: 17px; }

.panel-heading p {
    color: var(--muted);
    margin: 7px 0 0;
    font-size: 12px;
    line-height: 1.5;
}

.panel-tag {
    color: #8bbfff;
    border: 1px solid #2b4f79;
    background: #122b49;
    padding: 6px 9px;
    border-radius: 7px;
    font-size: 10px;
    white-space: nowrap;
}

textarea {
    width: 100%;
    min-height: 115px;
    resize: vertical;
    background: #091321;
    border: 1px solid #2b405d;
    border-radius: 10px;
    padding: 15px;
    color: var(--text);
    outline: none;
    line-height: 1.6;
}

textarea:focus, input:focus, select:focus {
    border-color: var(--blue);
    box-shadow: 0 0 0 3px #3995ff20;
}

textarea::placeholder, input::placeholder { color: #657b98; }

.form-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 13px;
}

.helper { color: var(--muted); font-size: 11px; }

.primary-btn {
    border: 0;
    border-radius: 9px;
    padding: 12px 17px;
    background: var(--blue);
    color: white;
    font-weight: 700;
    cursor: pointer;
    transition: .2s;
}

.primary-btn:hover { background: var(--blue-hover); }

.result {
    margin-top: 20px;
    padding: 17px;
    border: 1px solid var(--border);
    border-radius: 11px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
    overflow-wrap: anywhere;
}

.result.unsafe { background: #351b2a; border-color: #943e59; }
.result.clarify { background: #352b19; border-color: #86652c; }
.result.safe { background: #102e2a; border-color: #226c58; }
.result-icon { font-size: 23px; line-height: 1.2; }
.result h3 { margin: 0 0 7px; font-size: 14px; }

.result p {
    margin: 0;
    color: #c6d2e3;
    font-size: 12px;
    line-height: 1.6;
}

.history-panel { scroll-margin-top: 25px; }

.history-toolbar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 17px;
}

.search-box { flex: 1; min-width: 180px; }

.search-box input, .filter-select {
    width: 100%;
    height: 42px;
    background: #091321;
    border: 1px solid #2b405d;
    border-radius: 9px;
    padding: 0 12px;
    color: var(--text);
    outline: none;
}

.filter-select {
    width: auto;
    min-width: 175px;
    cursor: pointer;
}

.filter-select option { background: #101c30; color: white; }

.table-wrap { width: 100%; overflow-x: auto; }

table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    min-width: 530px;
}

th {
    color: #8da4c3;
    background: #0b1728;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .8px;
    text-transform: uppercase;
}

th, td {
    padding: 15px 13px;
    border-bottom: 1px solid #22324a;
}

td {
    color: #d5e0ef;
    font-size: 12px;
    overflow-wrap: anywhere;
}

tbody tr:hover { background: #15243a; }
tbody tr:last-child td { border-bottom: 0; }

.badge {
    display: inline-block;
    padding: 6px 9px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 750;
    white-space: nowrap;
}

.badge.unsafe { background: #512337; color: #ff9bae; }
.badge.clarify { background: #48391e; color: #ffdc91; }
.badge.safe { background: #153e35; color: #75edc7; }

.empty {
    color: var(--muted);
    text-align: center;
    padding: 30px 12px;
    line-height: 1.6;
}

.examples { display: flex; gap: 9px; flex-wrap: wrap; }

.example-btn {
    color: #b6cbe4;
    background: #122239;
    border: 1px solid #2b405d;
    border-radius: 8px;
    padding: 9px 11px;
    font-size: 11px;
    cursor: pointer;
}

.example-btn:hover { color: white; border-color: var(--blue); }

.disclaimer {
    color: #7489a5;
    font-size: 11px;
    text-align: center;
    line-height: 1.7;
    padding: 0 10px 18px;
}

.menu-toggle { display: none; }

@media (max-width: 1100px) {
    main { padding: 23px; }
    .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .sidebar { padding: 20px 12px; }
}

@media (max-width: 760px) {
    .app { display: block; }

    .sidebar {
        display: none;
        border-right: 0;
        border-bottom: 1px solid var(--border);
        padding: 16px;
        gap: 17px;
    }

    .sidebar.open { display: flex; }
    .sidebar-bottom { margin-top: 0; }
    main { padding: 20px 14px; }
    .topbar { margin-bottom: 23px; }

    .menu-toggle {
        display: inline-grid;
        place-items: center;
        width: 40px;
        height: 40px;
        background: var(--panel);
        border: 1px solid var(--border);
        color: white;
        border-radius: 9px;
        cursor: pointer;
        font-size: 20px;
        flex-shrink: 0;
    }

    .topbar-left {
        display: flex;
        align-items: flex-start;
        gap: 12px;
    }

    .status-pill { font-size: 10px; padding: 7px 9px; }
    .stat-card { padding: 15px; }
    .stat-number { font-size: 25px; }
    .stat-label { font-size: 11px; }
    .panel { padding: 17px; }
    .filter-select { flex: 1; min-width: 135px; }
}

@media (max-width: 420px) {
    .stats { gap: 9px; }
    .stat-card { padding: 12px; }
    .stat-icon { width: 28px; height: 28px; }
    .stat-number { font-size: 23px; }
    .topbar { align-items: flex-start; }
    .status-pill { margin-top: 3px; }
    .panel-heading { flex-direction: column; }
    .form-footer { align-items: stretch; }
    .primary-btn { width: 100%; }
}
</style>
</head>

<body>
<div class="app">

<aside class="sidebar" id="sidebar">
    <a class="brand" href="#dashboard">
        <div class="brand-icon">⬡</div>
        <div>
            <div class="brand-name">AgentX</div>
            <div class="brand-caption">AI ACTION SECURITY</div>
        </div>
    </a>

    <div>
        <div class="nav-label">WORKSPACE</div>
        <nav class="nav">
            <a class="active" href="#dashboard" onclick="closeMenu()">
                <span class="nav-icon">▦</span> Dashboard
            </a>
            <a href="#analyzer" onclick="closeMenu()">
                <span class="nav-icon">⌕</span> Evaluate Action
            </a>
            <a href="#history" onclick="closeMenu()">
                <span class="nav-icon">◷</span> Decision History
            </a>
        </nav>
    </div>

    <div>
        <div class="nav-label">ABOUT</div>
        <nav class="nav">
            <a href="#about" onclick="closeMenu()">
                <span class="nav-icon">ⓘ</span> About AgentX
            </a>
        </nav>
    </div>

    <div class="sidebar-bottom">
        <div class="local-status">● &nbsp; Local mode active</div>
        <p>Evaluations are saved locally in a JSON file. No cloud service is used.</p>
    </div>
</aside>

<main id="dashboard">
    <header class="topbar">
        <div class="topbar-left">
            <button class="menu-toggle" type="button"
                    onclick="toggleMenu()" aria-label="Toggle navigation">☰</button>
            <div>
                <div class="eyebrow">SECURITY OVERVIEW</div>
                <h1>Welcome to AgentX</h1>
                <p class="subtitle">Evaluate actions. Detect risk. Make informed decisions.</p>
            </div>
        </div>
        <div class="status-pill"><span class="status-dot"></span> LOCAL SYSTEM</div>
    </header>

    <section class="stats" aria-label="Evaluation statistics">
        <div class="stat-card">
            <div class="stat-top">
                <span class="stat-label">Total Evaluations</span>
                <span class="stat-icon blue">▤</span>
            </div>
            <div class="stat-number" id="totalCount">{{ stats.total }}</div>
            <div class="stat-foot">Latest saved decisions</div>
        </div>

        <div class="stat-card">
            <div class="stat-top">
                <span class="stat-label">Unsafe</span>
                <span class="stat-icon red">⚠</span>
            </div>
            <div class="stat-number red" id="unsafeCount">{{ stats.unsafe }}</div>
            <div class="stat-foot">Potentially destructive patterns</div>
        </div>

        <div class="stat-card">
            <div class="stat-top">
                <span class="stat-label">Needs Clarification</span>
                <span class="stat-icon yellow">?</span>
            </div>
            <div class="stat-number yellow" id="clarifyCount">{{ stats.clarify }}</div>
            <div class="stat-foot">Sensitive or consequential patterns</div>
        </div>

        <div class="stat-card">
            <div class="stat-top">
                <span class="stat-label">Safe to Simulate</span>
                <span class="stat-icon green">✓</span>
            </div>
            <div class="stat-number green" id="safeCount">{{ stats.safe }}</div>
            <div class="stat-foot">No configured risk pattern found</div>
        </div>
    </section>

    <section class="panel" id="analyzer">
        <div class="panel-heading">
            <div>
                <h2>Action Risk Analyzer</h2>
                <p>Describe the action you want AgentX to evaluate.</p>
            </div>
            <span class="panel-tag">RULE-BASED ANALYSIS</span>
        </div>

        <form method="POST" action="#analyzer">
            <textarea name="action" maxlength="1000" required
                placeholder="Example: Delete all files">{{ action }}</textarea>
            <div class="form-footer">
                <span class="helper">Maximum 1,000 characters · Text evaluation only</span>
                <button class="primary-btn" type="submit">Evaluate Action &nbsp; →</button>
            </div>
        </form>

        {% if result %}
        <div class="result {{ result_class }}" role="status">
            <div class="result-icon">
                {% if result_class == "unsafe" %}⚠
                {% elif result_class == "clarify" %}◈
                {% else %}✓{% endif %}
            </div>
            <div>
                <h3>{{ result }}</h3>
                <p>{{ reason }}</p>
            </div>
        </div>
        {% endif %}
    </section>

    <section class="panel history-panel" id="history">
        <div class="panel-heading">
            <div>
                <h2>Decision History</h2>
                <p>Search and filter your latest saved evaluations.</p>
            </div>
            <span class="panel-tag">LATEST 50</span>
        </div>

        <div class="history-toolbar">
            <div class="search-box">
                <input id="historySearch" type="search"
                    placeholder="⌕  Search actions..."
                    aria-label="Search decision history">
            </div>
            <select id="decisionFilter" class="filter-select"
                    aria-label="Filter by decision">
                <option value="all">All decisions</option>
                <option value="UNSAFE">Unsafe</option>
                <option value="NEEDS CLARIFICATION">Needs clarification</option>
                <option value="SAFE TO SIMULATE">Safe to simulate</option>
            </select>
        </div>

        <div class="table-wrap">
            <table>
                <thead>
                    <tr><th>Time</th><th>Action</th><th>Decision</th></tr>
                </thead>
                <tbody id="historyBody">
                {% for item in history %}
                    <tr data-action="{{ item.action|lower }}"
                        data-decision="{{ item.result }}">
                        <td>{{ item.time }}</td>
                        <td>{{ item.action }}</td>
                        <td><span class="badge {{ item.css }}">{{ item.result }}</span></td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
            <div id="emptyHistory" class="empty"
                 {% if history %}hidden{% endif %}>
                No evaluations yet. Evaluate an action to start your history.
            </div>
            <div id="noMatches" class="empty" hidden>
                No matching decisions. Try a different search or filter.
            </div>
        </div>
    </section>

    <section class="panel">
        <div class="panel-heading">
            <div>
                <h2>Quick Test Actions</h2>
                <p>Choose an example to fill the analyzer.</p>
            </div>
        </div>
        <div class="examples">
            <button class="example-btn" type="button"
                onclick="useExample('List files in my documents')">
                List files in my documents
            </button>
            <button class="example-btn" type="button"
                onclick="useExample('Delete all files')">
                Delete all files
            </button>
            <button class="example-btn" type="button"
                onclick="useExample('Read DATABASE_URL')">
                Read DATABASE_URL
            </button>
            <button class="example-btn" type="button"
                onclick="useExample('Create a new text file')">
                Create a new text file
            </button>
        </div>
    </section>

    <footer class="disclaimer" id="about">
        <strong>AgentX Demo</strong> · Built with Python and Flask · Runs locally<br>
        AgentX does not execute actions or access your files. A SAFE result only means
        no configured risk pattern was detected; it does not guarantee an action is safe.
    </footer>
</main>
</div>

<script>
const searchInput = document.getElementById("historySearch");
const decisionFilter = document.getElementById("decisionFilter");
const historyBody = document.getElementById("historyBody");
const emptyHistory = document.getElementById("emptyHistory");
const noMatches = document.getElementById("noMatches");

function filterHistory() {
    const query = searchInput.value.toLowerCase().trim();
    const selected = decisionFilter.value;
    const rows = Array.from(historyBody.querySelectorAll("tr"));
    let visible = 0;

    rows.forEach(row => {
        const action = row.dataset.action || "";
        const decision = row.dataset.decision || "";
        const matchesText = action.includes(query);
        const matchesDecision = selected === "all" || decision === selected;
        const show = matchesText && matchesDecision;

        row.hidden = !show;
        if (show) visible++;
    });

    const hasRows = rows.length > 0;
    emptyHistory.hidden = hasRows;
    noMatches.hidden = !hasRows || visible > 0;
}

searchInput.addEventListener("input", filterHistory);
decisionFilter.addEventListener("change", filterHistory);

function useExample(value) {
    document.querySelector('textarea[name="action"]').value = value;
    document.getElementById("analyzer").scrollIntoView({ behavior: "smooth" });
    document.querySelector('textarea[name="action"]').focus();
}

function toggleMenu() {
    document.getElementById("sidebar").classList.toggle("open");
}

function closeMenu() {
    if (window.innerWidth <= 760) {
        document.getElementById("sidebar").classList.remove("open");
    }
}

filterHistory();
</script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    action = ""
    result = ""
    reason = ""
    result_class = ""

    if request.method == "POST":
        action = request.form.get("action", "").strip()[:1000]

        if action:
            result, reason = evaluate_action(action)

            if result == "UNSAFE":
                result_class = "unsafe"
            elif result == "NEEDS CLARIFICATION":
                result_class = "clarify"
            else:
                result_class = "safe"

            decision_history.insert(0, {
                "time": datetime.now().strftime("%H:%M:%S"),
                "action": action,
                "result": result,
                "css": result_class,
            })

            del decision_history[MAX_HISTORY:]
            save_history()

    stats = {
        "total": len(decision_history),
        "unsafe": sum(
            item["result"] == "UNSAFE" for item in decision_history
        ),
        "clarify": sum(
            item["result"] == "NEEDS CLARIFICATION"
            for item in decision_history
        ),
        "safe": sum(
            item["result"] == "SAFE TO SIMULATE" for item in decision_history
        ),
    }

    return render_template_string(
        HTML,
        action=action,
        result=result,
        reason=reason,
        result_class=result_class,
        history=decision_history,
        stats=stats,
    )


if __name__ == "__main__":
    print("AgentX Professional Dashboard starting...")
    print("History file:", HISTORY_FILE)
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(host="127.0.0.1", port=5000, debug=False)
