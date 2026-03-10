# Self-Healing Developer Agent

> An AI-powered developer assistant that **observes** command failures, **reasons** about errors using an LLM, and **acts** by applying fixes automatically — all in a beautiful CLI or Streamlit dashboard.
>
> Powered by **LangChain + Groq** (free, ultra-fast LLM inference).

---

## 📌 Project Overview

The Self-Healing Developer Agent implements the **Observe → Reason → Act** agentic AI pattern:

| Stage | What happens |
|-------|-------------|
| **Observe** | Runs your command and captures stdout/stderr |
| **Reason** | Parses the error, checks memory cache, calls LLM if needed |
| **Act** | Presents the fix, waits for your approval, applies it |
| **Verify** | Re-runs the original command to confirm the fix works |

---

## ✨ Features

- 🚀 **Run any developer command** through the agent
- 🔍 **Smart error classification** (ModuleNotFoundError, SyntaxError, etc.)
- 🧠 **LLM-powered fix generation** via LangChain + OpenAI
- ⚡ **Memory cache** — instant fixes for known errors (no LLM cost)
- ✅ **User approval gate** before any fix is applied
- 🔁 **Auto-retry loop** (up to 3 attempts)
- 🎨 **Rich terminal UI** with coloured panels and progress
- 🌐 **Streamlit dashboard** for a browser-based experience
- 📝 **Structured logging** to `agent.log`
- 🗄️ **SQLite memory DB** (`fixes_memory.db`) stores all past fixes

---

## 🏗️ Architecture

```
self-healing-agent/
├── main.py            # CLI entry point
├── app_ui.py          # Streamlit dashboard (bonus)
├── agent.py           # Orchestrator — Observe→Reason→Act loop
├── command_runner.py  # subprocess wrapper
├── error_parser.py    # regex-based error classifier
├── fix_generator.py   # LangChain + OpenAI fix generation
├── fix_applier.py     # executes the fix command
├── tools.py           # LangChain Tool definitions
├── memory_db.py       # SQLite error memory (bonus)
├── logger.py          # Rich + file logging (bonus)
├── requirements.txt
├── .env.example
└── README.md
```

```
Flow diagram:

User → main.py → SelfHealingAgent.run()
                         │
                    run_command()        ← command_runner.py
                         │
                   [failed?] ──No──→ Done ✓
                         │Yes
                   parse_error()        ← error_parser.py
                         │
                  memory.lookup()       ← memory_db.py
                         │
               [cache hit?] ──Yes──→ show cached fix
                         │No
                  generate_fix()        ← fix_generator.py (LLM)
                         │
                  [user approves?]
                         │Yes
                   apply_fix()          ← fix_applier.py
                         │
                  memory.store()        ← memory_db.py
                         │
                  run_command()  ← verify
                         │
                  [success?] → Done ✓ / retry
```

---

## ⚙️ Installation

### 1. Clone / download this project
```bash
cd self-healing-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
# Windows
copy .env.example .env
notepad .env

# Mac / Linux
cp .env.example .env
nano .env
```

> [!IMPORTANT]
> You need a **free Groq API key** — get one at [console.groq.com](https://console.groq.com).

Edit `.env` and add your Groq API key:
```
GROQ_API_KEY=gsk_your-key-here
MODEL_NAME=llama3-8b-8192
MAX_RETRIES=3
```

---

## 🚀 How to Run

### CLI — Interactive mode
```bash
python main.py
```
When prompted, type a command (e.g. `python app.py`) and watch the agent work.

### CLI — Single command
```bash
python main.py "python app.py"
```

### CLI — Auto-apply mode (no approval prompt)
```bash
python main.py --auto "python app.py"
```

### CLI — Show fix memory
```bash
python main.py --memory
```

### Global Installation (Use `agent` in any folder!)

To use the agent from *any* directory on your PC:
1. Hit Windows Key and search for **Environment Variables**.
2. Click **Edit the system environment variables**.
3. Click the **Environment Variables...** button.
4. Under User variables, select **Path** and click **Edit**.
5. Click **New** and paste the full path to your `self-healing-agent` folder (e.g., `C:\Users\yoges\OneDrive\Documents\cohort2\self-healing-agent`).
6. Click **OK** on all windows.
7. Restart your terminal (PowerShell or VSCode).

Now you can open a new terminal in *any* project folder and just type:
```bash
agent
```
or 
```bash
agent "python script.py"
```

### Streamlit Dashboard
You can now also launch the web-based UI from anywhere using:
```bash
agent-ui
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🎬 Example Output

```
╔═══════════════════════════════════════════╗
║     🤖  Self-Healing Developer Agent       ║
║   Observe  →  Reason  →  Act  →  Verify   ║
╚═══════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━ Self-Healing Agent ━━━━━━━━━━━━━━━━━━
▶  Running:  python app.py

  Status : FAILED  |  Exit : 1  |  Time : 0.312s
╭─────────────────── stderr ──────────────────────╮
│ Traceback (most recent call last):              │
│   File "app.py", line 1, in <module>            │
│     import pandas as pd                         │
│ ModuleNotFoundError: No module named 'pandas'   │
╰─────────────────────────────────────────────────╯

━━━━━━━━━━━━━━━━━━ Attempt 1/3 ━━━━━━━━━━━━━━━━━━

╭──────────── Error Detected ─────────────────────╮
│ Error Type : ModuleNotFoundError                │
│ Message    : ModuleNotFoundError: No module ... │
│ Module     : pandas                             │
╰─────────────────────────────────────────────────╯

Consulting the LLM…

╭──────────── Suggested Fix ──────────────────────╮
│ Fix Command : pip install pandas                │
│ Confidence  : high                              │
│ Source      : LLM 🧠                           │
│                                                 │
│ The 'pandas' package is not installed...        │
╰─────────────────────────────────────────────────╯

Apply this fix? [Y/n]: Y

Applying fix: pip install pandas
Fix applied successfully.

▶  Re-running: python app.py

  Status : SUCCESS  |  Exit : 0  |  Time : 1.105s

✓ Command succeeded after 1 fix attempt(s)!

╭──────────── Session Summary ────────────────────╮
│ Command  : python app.py                        │
│ Status   : ✓  FIXED & PASSING                  │
│ Attempts : 1                                    │
│ Fix Used : pip install pandas                   │
╰─────────────────────────────────────────────────╯
```

---

## 🔮 Future Improvements

| Idea | Description |
|------|-------------|
| **Code Patch Generator** | Auto-edit source files for logic/syntax errors |
| **Git Auto-Commit** | Commit the fix with a descriptive message |
| **StackOverflow Search** | Search SO for error context before LLM call |
| **Multi-Model Support** | Fallback to Claude / Gemini if OpenAI fails |
| **Slack / Email Alerts** | Notify team when a fix is applied |
| **Web Scraper** | Pull latest docs for dependency errors |
| **Docker Support** | Containerised environment for isolated execution |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.9+ |
| Agent Framework | LangChain |
| LLM | Groq — `llama3-8b-8192` (configurable) |
| CLI UI | Rich |
| Web UI | Streamlit |
| Memory | SQLite via `sqlite3` |
| Logging | Python logging + Rich handler |
| Env Management | python-dotenv |

---

## 📄 License

MIT — free to use, modify, and distribute.
#   s e l f _ h e a l i n g _ a g e n t  
 