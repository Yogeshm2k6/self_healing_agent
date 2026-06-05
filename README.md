# 🤖 Self-Healing Developer Agent

An AI-powered developer assistant that automatically detects, analyzes, and fixes development errors using Large Language Models.

Built with **LangChain + Groq**, the Self-Healing Developer Agent follows the **Observe → Reason → Act → Verify** workflow to reduce debugging time and improve developer productivity.

---

## 🚀 Overview

Debugging repetitive development errors can consume valuable time.

The Self-Healing Developer Agent acts as an intelligent troubleshooting assistant that:

* Executes developer commands
* Detects failures automatically
* Analyzes error messages
* Generates potential fixes using AI
* Requests user approval before making changes
* Applies fixes automatically
* Verifies that the issue has been resolved

Think of it as having an AI-powered DevOps assistant constantly monitoring and repairing common development problems.

---

## 🎯 Key Features

### 🔍 Intelligent Error Detection

Automatically identifies:

* ModuleNotFoundError
* ImportError
* SyntaxError
* FileNotFoundError
* PermissionError
* Dependency Issues
* Environment Configuration Problems
* Runtime Exceptions

### 🧠 AI-Powered Reasoning

Uses Groq-powered LLMs through LangChain to:

* Understand error context
* Determine root causes
* Suggest actionable fixes
* Explain reasoning in plain English

### ⚡ Memory-Based Learning

Stores successful fixes inside SQLite.

Benefits:

* Instant retrieval of previously solved issues
* Reduced API calls
* Faster response times
* Continuous improvement over time

### 🔐 Safe Approval Workflow

Before applying any fix, the agent:

1. Shows the proposed solution
2. Explains why it should work
3. Requests user approval

This prevents unwanted system modifications.

### 🔁 Self-Healing Retry Loop

The agent can:

* Attempt multiple fixes
* Verify results automatically
* Retry intelligently
* Stop when the issue is resolved

### 🎨 Rich Developer Experience

Includes:

* Rich CLI Interface
* Progress Indicators
* Colorized Output
* Detailed Session Reports
* Streamlit Web Dashboard

### 📝 Logging & Audit Trail

Every action is logged:

* Commands executed
* Errors encountered
* Fixes suggested
* Fixes applied
* Verification results

---

# 🏗️ Architecture

```text
self-healing-agent/
│
├── main.py
├── app_ui.py
├── agent.py
├── command_runner.py
├── error_parser.py
├── fix_generator.py
├── fix_applier.py
├── tools.py
├── memory_db.py
├── logger.py
│
├── fixes_memory.db
├── agent.log
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔄 Agent Workflow

```text
            ┌───────────────┐
            │ User Command  │
            └───────┬───────┘
                    │
                    ▼
         ┌─────────────────────┐
         │ Observe Phase       │
         │ Execute Command     │
         └─────────┬───────────┘
                   │
                   ▼
          Command Successful?
              │         │
             Yes       No
              │         ▼
              │  ┌──────────────┐
              │  │ Parse Error  │
              │  └──────┬───────┘
              │         ▼
              │  Check Memory DB
              │         │
              │         ▼
              │   Cache Hit?
              │      │    │
              │     Yes   No
              │      │     ▼
              │      │ Generate Fix
              │      │   Using LLM
              │      │
              ▼      ▼
         Success  Show Fix
                    │
                    ▼
              User Approval
                    │
                    ▼
               Apply Fix
                    │
                    ▼
               Verify Fix
                    │
                    ▼
                 Success
```

---

# 🛠️ Tech Stack

| Component             | Technology     |
| --------------------- | -------------- |
| Programming Language  | Python 3.9+    |
| Agent Framework       | LangChain      |
| LLM Provider          | Groq           |
| Model                 | Llama 3        |
| CLI Interface         | Rich           |
| Web Dashboard         | Streamlit      |
| Memory Layer          | SQLite         |
| Logging               | Python Logging |
| Environment Variables | python-dotenv  |

---

# ⚙️ Installation

## Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/self-healing-agent.git

cd self-healing-agent
```

---

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 3: Configure Environment

Create a `.env` file:

```env
GROQ_API_KEY=gsk_your_api_key_here

MODEL_NAME=llama3-8b-8192

MAX_RETRIES=3
```

---

## Step 4: Get a Free Groq API Key

1. Visit https://console.groq.com
2. Create an account
3. Generate an API Key
4. Paste it into `.env`

---

# 🚀 Usage

## Interactive CLI Mode

```bash
python main.py
```

Example:

```text
Enter command:
> python app.py
```

---

## Single Command Mode

```bash
python main.py "python app.py"
```

---

## Auto-Fix Mode

Automatically applies fixes without asking.

```bash
python main.py --auto "python app.py"
```

---

## View Stored Fixes

```bash
python main.py --memory
```

---

# 🌐 Streamlit Dashboard

Launch the browser interface:

```bash
streamlit run app_ui.py
```

Then open:

```text
http://localhost:8501
```

Dashboard Features:

* Run commands
* View errors
* AI-generated fixes
* Memory database explorer
* Session history
* Logs viewer

---

# 💾 Memory Database

The agent maintains a local SQLite database:

```text
fixes_memory.db
```

Stored Information:

* Error Type
* Error Message
* Suggested Fix
* Fix Success Status
* Timestamp

Example:

| Error                         | Fix                  |
| ----------------------------- | -------------------- |
| ModuleNotFoundError: pandas   | pip install pandas   |
| ModuleNotFoundError: requests | pip install requests |

---

# 📜 Example Session

```text
▶ Running: python app.py

Status : FAILED
Exit Code : 1

Error:
ModuleNotFoundError:
No module named 'pandas'

━━━━━━━━━━━━━━━━━━━

AI Analysis:

The pandas package is missing.

Suggested Fix:

pip install pandas

Apply fix? [Y/n]

Y

Installing pandas...

Fix applied successfully.

Re-running command...

Status : SUCCESS

✓ Issue resolved
```

---

# 🔒 Safety Mechanisms

The agent is designed with safety in mind.

### Approval Gate

Every generated fix requires user confirmation.

### Retry Limit

Prevents infinite fix loops.

```env
MAX_RETRIES=3
```

### Structured Logging

Every action is recorded for auditing.

### Command Validation

Potentially dangerous operations can be filtered before execution.

---

# 📊 Logging

All events are written to:

```text
agent.log
```

Example:

```text
[INFO] Running command
[INFO] Error detected
[INFO] Generated fix
[INFO] User approved
[INFO] Fix applied
[INFO] Verification passed
```

---

# 🔮 Future Enhancements

## Automatic Code Patching

Allow AI to directly modify source files.

## StackOverflow Integration

Search real-world solutions before querying the LLM.

## Git Integration

Automatically commit successful fixes.

## Multi-Model Support

Support:

* Groq
* Gemini
* Claude
* OpenAI

## Docker Sandbox

Apply fixes inside isolated containers.

## Team Notifications

Send alerts through:

* Slack
* Microsoft Teams
* Email

## Documentation Search

Pull relevant examples from official documentation.

---

# 🤝 Contributing

Contributions are welcome.

### Development Workflow

```bash
git checkout -b feature/new-feature

git commit -m "Add new feature"

git push origin feature/new-feature
```

Create a Pull Request and describe the proposed changes.

---

# 📄 License

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files to deal in the Software without restriction.

---

# ⭐ Why Use Self-Healing Developer Agent?

✅ Reduces debugging time

✅ Learns from previous fixes

✅ AI-assisted troubleshooting

✅ Safe approval workflow

✅ Beautiful CLI experience

✅ Web dashboard included

✅ Completely extensible

✅ Powered by Groq's ultra-fast inference

---

**Observe → Reason → Act → Verify**

*Transform your development workflow with autonomous debugging and intelligent self-healing.*

## 🎬 Example Output

```text
╔══════════════════════════════════════════════════════╗
║           🤖 Self-Healing Developer Agent           ║
║         Observe → Reason → Act → Verify            ║
╚══════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▶ Running Command

$ python app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Command Failed

Exit Code : 1
Duration  : 0.34s

Error Detected:

Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import pandas as pd

ModuleNotFoundError: No module named 'pandas'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Analyzing Error...

✔ Error Type : ModuleNotFoundError
✔ Missing Module : pandas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 Consulting Groq LLM...

Suggested Fix:

Command:
pip install pandas

Confidence:
98%

Explanation:
The application requires the pandas package,
but it is not installed in the current Python
environment.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apply Fix? [Y/n]: Y

Applying Fix...

$ pip install pandas

✔ Installation completed successfully

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Verifying Fix...

Re-running:

$ python app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ SUCCESS

Exit Code : 0
Duration  : 1.02s

Command executed successfully.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Session Summary

Command      : python app.py
Status       : FIXED & PASSING
Attempts     : 1
Fix Applied  : pip install pandas
Source       : Groq LLM
Memory Saved : Yes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 Issue Resolved Successfully!
```
