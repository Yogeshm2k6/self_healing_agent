"""
app_ui.py  (Bonus Feature — Streamlit Dashboard)
-------------------------------------------------
A beautiful web-based UI for the Self-Healing Developer Agent.

Run with:
    streamlit run app_ui.py

Features
--------
• Command input with Run button
• Live stdout / stderr display
• Error analysis card
• Fix suggestion with Approve / Reject buttons
• Session history table
• Memory DB viewer tab
"""

import json
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Ensure the project root is on sys.path when run from another directory
sys.path.insert(0, str(Path(__file__).parent))

from command_runner import run_command
from error_parser import parse_error, summarise_error
from fix_generator import generate_fix
from fix_applier import apply_fix
from memory_db import ErrorMemory
from code_generator import is_edit_command, is_natural_language
from project_generator import is_project_command

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Self-Healing Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

/* Global Fonts */
html, body, [class*="css"]  {
    font-family: 'Outfit', sans-serif;
}

/* Animated Dark Gradient Background with Glowing Orbs */
[data-testid="stAppViewContainer"] {
    background: #09090b;
    background-image: 
        radial-gradient(circle at 15% 50%, rgba(125, 207, 255, 0.08), transparent 25%),
        radial-gradient(circle at 85% 30%, rgba(158, 206, 106, 0.05), transparent 25%);
    background-attachment: fixed;
    color: #a9b1d6;
}

[data-testid="stSidebar"] {
    background: rgba(9, 9, 11, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Main Input Bar (Make it look like a search engine) */
[data-testid="stTextInput"] > div > div > input {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #fff;
    font-size: 1.1rem;
    padding: 18px 20px;
    border-radius: 16px;
    font-family: 'JetBrains Mono', monospace;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
[data-testid="stTextInput"] > div > div > input:focus {
    background: rgba(255, 255, 255, 0.06);
    border-color: #7dcfff;
    box-shadow: 0 0 0 2px rgba(125, 207, 255, 0.2), 0 8px 32px rgba(0, 0, 0, 0.4);
}

/* Primary Button Override (Vibrant Gradient) */
button[kind="primary"] {
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    padding: 10px 0 !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 25px rgba(79, 172, 254, 0.4) !important;
    transition: all 0.3s ease !important;
}
button[kind="primary"]:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 12px 35px rgba(79, 172, 254, 0.6) !important;
}

/* Streamlit Tabs Override */
div[data-baseweb="tab-list"] {
    gap: 15px;
    background: rgba(255, 255, 255, 0.03);
    padding: 6px 10px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}
div[data-baseweb="tab"] {
    color: #8b949e !important;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 10px;
    transition: all 0.2s ease;
}
div[data-baseweb="tab"]:hover {
    background: rgba(255, 255, 255, 0.05);
    color: #c0caf5 !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(125, 207, 255, 0.15) !important;
    color: #7dcfff !important;
    box-shadow: inset 0 0 0 1px rgba(125, 207, 255, 0.3);
}
div[data-baseweb="tab-highlight"] {
    display: none; /* Hide the default red bottom border */
}

/* Glassmorphism Cards */
.agent-card {
    background: rgba(26, 27, 38, 0.4);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.agent-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.15);
}

.success-card { border-left: 4px solid #9ece6a; }
.error-card   { border-left: 4px solid #f7768e; }
.fix-card     { border-left: 4px solid #7dcfff; }

/* Mac-like Terminal Window for Output */
.terminal-window {
    background: #101014;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    overflow: hidden;
    margin-top: 15px;
    margin-bottom: 20px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.6);
}
.terminal-header {
    background: #16161c;
    padding: 10px 15px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 0.8rem;
    color: #565f89;
    font-weight: 600;
}
.terminal-dots {
    display: flex;
    gap: 8px;
    margin-right: 15px;
}
.dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}
.dot.red { background: #ff5f56; box-shadow: 0 0 10px rgba(255, 95, 86, 0.5); }
.dot.yellow { background: #ffbd2e; box-shadow: 0 0 10px rgba(255, 189, 46, 0.5); }
.dot.green { background: #27c93f; box-shadow: 0 0 10px rgba(39, 201, 63, 0.5); }

.terminal-body {
    padding: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    color: #c0caf5;
    overflow-x: auto;
    max-height: 500px;
    white-space: pre-wrap;
    line-height: 1.5;
}
.terminal-body.stderr {
    color: #f7768e;
}

/* Secondary Buttons */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #c0caf5;
}
.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 0 15px rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    color: #fff;
}

/* Status badges */
.badge-success { color: #9ece6a; font-weight: 800; background: rgba(158,206,106,0.15); padding: 6px 12px; border-radius: 20px; text-transform: uppercase; letter-spacing: 1px; font-size: 0.8rem;}
.badge-error   { color: #f7768e; font-weight: 800; background: rgba(247,118,142,0.15); padding: 6px 12px; border-radius: 20px; text-transform: uppercase; letter-spacing: 1px; font-size: 0.8rem;}

</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
def _init_state():
    defaults = {
        "history": [],          # list of run records
        "pending_fix": None,    # fix dict awaiting approval
        "pending_cmd": None,    # original command for pending fix
        "pending_error": None,  # parsed error for pending fix
        "memory": ErrorMemory(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🤖 Self-Healing Agent")
    st.markdown("---")
    st.markdown("**Settings**")
    max_retries = st.number_input("Max retries", min_value=1, max_value=10, value=3)
    auto_apply  = st.checkbox("Auto-apply fixes (no approval)", value=False)
    st.markdown("---")
    st.markdown("**Info**")
    mem_count = st.session_state.memory.count()
    st.metric("Fixes in Memory DB", mem_count)
    if st.button("Clear Memory DB"):
        st.session_state.memory.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style='text-align:center; padding: 2rem 0; animation: fadeIn 1s ease-in;'>
        <h1 style='color:#7dcfff; font-size: 3rem; font-weight: 700; letter-spacing: -1px; margin-bottom: 0.5rem; text-shadow: 0 0 20px rgba(125,207,255,0.3);'>
            ⚡ Zero-Shot Agent
        </h1>
        <p style='color:#565f89; font-size: 1.1rem; font-weight: 400;'>Observe • Reason • Act • Verify</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_run, tab_history, tab_memory = st.tabs(["▶ Run Command", "📋 History", "🧠 Memory DB"])

# ===========================================================================
# TAB 1 — Run Command
# ===========================================================================
with tab_run:
    st.markdown("### Enter a developer command")

    col_cmd, col_btn = st.columns([5, 1])
    with col_cmd:
        user_cmd = st.text_input(
            label="Command",
            placeholder="e.g. python app.py",
            label_visibility="collapsed",
        )
    with col_btn:
        run_clicked = st.button("▶ Run", use_container_width=True, type="primary")

    # ── Run the command ────────────────────────────────────────────────
    if run_clicked and user_cmd.strip():
        cmd_text = user_cmd.strip()

        # ── Detect if it's an "ask" question ───────────────────────────
        if cmd_text.lower().startswith("ask "):
            question = cmd_text[4:].strip()
            with st.spinner("Answering..."):
                from chat_handler import handle_chat
                answer = handle_chat(question)
                st.info(f"**Question:** {question}\n\n**Agent:**\n{answer}")
            st.stop()
            
        # ── Detect if it's an "edit file" command ──────────────────────
        is_edit, edit_file, edit_instr = is_edit_command(cmd_text)
        if is_edit:
            if not edit_file or not edit_instr:
                st.error("⚠️ **Incomplete edit command.** Please specify both the file and the instruction. Example: `edit app.py to add a new function`")
                st.stop()
            with st.spinner(f"Editing {edit_file}..."):
                from code_generator import handle_edit_command
                gen = handle_edit_command(edit_file, edit_instr)
                
            if gen["success"]:
                st.success(f"File modified successfully: `{gen['filename']}`")
                with st.expander("View Code Changes"):
                    st.code(gen["code"])
                # Fall through to run the command, exactly like the CLI does!
                cmd_text = gen["command"]
            else:
                st.error(f"Code edit failed: {gen.get('error')}")
                st.stop()

        # ── Detect if it's a "create project" command ──────────────────
        is_proj, proj_desc = is_project_command(cmd_text)
        if hasattr(is_proj, 'startswith'): pass # Hack for Python scope bug
        if is_edit: pass # Avoid duplicate

        # ── Handle "run <name>" ───────────────────────────────────────────
        if not is_edit and cmd_text.lower().startswith("run "):
            target_path_str = cmd_text[4:].strip()
            target_path = Path(target_path_str)
            
            if not target_path.exists():
                st.error(f"Path not found: `{target_path_str}`")
                st.stop()
                
            run_file = None
            target_dir = None

            if target_path.is_file():
                run_file = target_path.name
                target_dir = str(target_path.parent) or "."
            else:
                target_dir = target_path_str
                entry_points = ["main.py", "app.py", "run.py", "index.js", "server.js", "server.py", "index.html"]
                for ep in entry_points:
                    if (target_path / ep).is_file():
                        run_file = ep
                        break
                        
                if not run_file:
                    for ext in ["*.py", "*.js", "*.html"]:
                        files = list(target_path.glob(ext))
                        if files:
                            run_file = files[0].name
                            break
                            
                if not run_file:
                    st.error(f"Could not find a clear entry point (like main.py or index.js) in `{target_dir}`.")
                    st.stop()
                    
                st.info(f"**Auto-detecting entry point:** Found `{run_file}`")
            
            if run_file.endswith(".py"):
                cmd_text = f'python "{run_file}"'
            elif run_file.endswith(".js"):
                cmd_text = f'node "{run_file}"'
            elif run_file.endswith(".html"):
                import subprocess as _sp
                _sp.Popen(["start", run_file], shell=True, cwd=str(Path(target_dir).resolve()))
                st.success(f"✓ Opening `{run_file}` in your default browser...")
                st.stop()
            elif run_file.endswith(".sh"):
                cmd_text = f'bash "{run_file}"'
            else:
                cmd_text = f'python "{run_file}"'

            # Store the intended working directory in st.session_state so the agent loop
            # below knows to use it (since app_ui uses a persistent agent)
            st.session_state.agent_cwd = str(Path(target_dir).resolve())

        elif not is_edit and is_proj:
            with st.spinner(f"Generating full project..."):
                from project_generator import generate_project, description_to_project_name
                proj_name = description_to_project_name(proj_desc)
                gen_proj = generate_project(proj_desc, proj_name)
                
            if gen_proj["success"]:
                st.success(f"✓ Created project directory: `{proj_name}` with {len(gen_proj['files'])} files.")
                for fp in gen_proj['files']:
                    st.markdown(f"- `{fp}`")
            else:
                st.error(f"Project generation failed: {gen_proj.get('error')}")
            st.stop()

        # ── Detect if it's a general natural language idea ───────────────
        elif not is_edit and is_natural_language(cmd_text):
            with st.spinner(f"Generating Python code..."):
                from code_generator import handle_natural_language
                gen = handle_natural_language(cmd_text, language="Python")
                
            if gen["success"]:
                st.success(f"Generated successfully: `{gen['filename']}`")
                with st.expander("View Generated Code"):
                    st.code(gen["code"])
                # Fall through to run the command
                cmd_text = gen["command"]
            else:
                st.error(f"Code generation failed.")
                st.stop()

        with st.spinner(f"Running `{cmd_text}` …"):
            cwd_to_use = st.session_state.agent_cwd if hasattr(st.session_state, "agent_cwd") else None
            result = run_command(cmd_text, cwd=cwd_to_use)
            if hasattr(st.session_state, "agent_cwd"):
                del st.session_state.agent_cwd  # cleanup

        # Store in history
        record = {
            "command": user_cmd,
            "result": result,
            "fix_applied": None,
            "fix_success": None,
            "timestamp": time.strftime("%H:%M:%S"),
        }

        # Display output
        st.markdown("<br><h3>Output Console</h3>", unsafe_allow_html=True)
        
        status_color = "badge-success" if result["success"] else "badge-error"
        status_text  = "✓ SUCCESS" if result["success"] else "✗ FAILED"
        st.markdown(
            f'<div style="margin-bottom: 15px;">'
            f'<span class="{status_color}">{status_text}</span> &nbsp;&nbsp;'
            f'<span style="color:#565f89; font-size:0.9rem;">Exit: <strong>{result["returncode"]}</strong> &nbsp;•&nbsp; Time: <strong>{result["elapsed"]}s</strong></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if result["stdout"].strip():
            st.markdown(f'''
            <div class="terminal-window">
                <div class="terminal-header">
                    <div class="terminal-dots">
                        <div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div>
                    </div>
                    <span>stdout — {user_cmd}</span>
                </div>
                <div class="terminal-body">{result["stdout"]}</div>
            </div>
            ''', unsafe_allow_html=True)

        if result["stderr"].strip():
            st.markdown(f'''
            <div class="terminal-window" style="border-color: rgba(247,118,142,0.3);">
                <div class="terminal-header" style="color: #f7768e;">
                    <div class="terminal-dots">
                        <div class="dot red" style="box-shadow: 0 0 8px #ff5f56;"></div><div class="dot yellow"></div><div class="dot green"></div>
                    </div>
                    <span>stderr — {user_cmd}</span>
                </div>
                <div class="terminal-body stderr">{result["stderr"]}</div>
            </div>
            ''', unsafe_allow_html=True)

        if result["success"]:
            st.success("Command succeeded — no healing needed.")
            st.session_state.history.append(record)
        else:
            # ── Analyse error ──────────────────────────────────────────
            error_info = parse_error(result)

            st.markdown("---")
            st.markdown("#### 🔍 Error Analysis")
            st.markdown(
                f'<div class="agent-card error-card">'
                f'<strong>Error Type:</strong> {error_info["error_type"]}<br>'
                f'<strong>Message:</strong><br>'
                f'<div class="code-block">{error_info["error_message"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Generate fix ───────────────────────────────────────────
            st.markdown("#### 💡 Suggested Fix")
            with st.spinner("Consulting the LLM…"):
                fix = generate_fix(user_cmd, error_info, memory=st.session_state.memory)

            conf_color = {"high": "#3fb950", "medium": "#d29922", "low": "#f85149"}.get(
                fix.get("confidence", "medium"), "#8b949e"
            )
            source = "Memory Cache ⚡" if fix.get("from_cache") else "LLM 🧠"

            st.markdown(
                f'<div class="agent-card fix-card">'
                f'<strong>Fix Command:</strong><br>'
                f'<div class="code-block">{fix.get("fix_command", "(none)")}</div><br>'
                f'<strong>Confidence:</strong> <span style="color:{conf_color}">{fix.get("confidence","?")}</span>&nbsp;&nbsp;'
                f'<strong>Source:</strong> {source}<br><br>'
                f'<em>{fix.get("explanation","")}</em>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if fix.get("fix_command"):
                # Store pending state for approval
                st.session_state.pending_fix   = fix
                st.session_state.pending_cmd   = user_cmd
                st.session_state.pending_error = error_info

            st.session_state.history.append(record)

    # ── Approval section ────────────────────────────────────────────────
    if st.session_state.pending_fix and not auto_apply:
        fix = st.session_state.pending_fix
        st.markdown("---")
        st.markdown("### ⚙️ Apply this fix?")
        col_y, col_n, _ = st.columns([1, 1, 4])

        with col_y:
            if st.button("✅ Yes, Apply", type="primary", use_container_width=True):
                with st.spinner(f"Applying: `{fix['fix_command']}`…"):
                    fix_result = apply_fix(fix["fix_command"])

                success_fix = fix_result["success"]
                st.session_state.memory.store(
                    st.session_state.pending_error["error_type"],
                    st.session_state.pending_cmd,
                    fix["fix_command"],
                    fix.get("explanation", ""),
                    success=success_fix,
                )

                if success_fix:
                    st.success(f"Fix applied! Re-running `{st.session_state.pending_cmd}`…")
                    rerun_result = run_command(st.session_state.pending_cmd)

                    if rerun_result["success"]:
                        st.success("✓ Command now passes!")
                        if rerun_result["stdout"].strip():
                            st.code(rerun_result["stdout"], language="text")
                    else:
                        st.error("Command still failing after fix.")
                        st.code(rerun_result["stderr"], language="text")
                else:
                    st.error(f"Fix command failed: {fix_result['stderr'][:300]}")

                st.session_state.pending_fix   = None
                st.session_state.pending_cmd   = None
                st.session_state.pending_error = None
                st.rerun()

        with col_n:
            if st.button("❌ No, Skip", use_container_width=True):
                st.session_state.pending_fix   = None
                st.session_state.pending_cmd   = None
                st.session_state.pending_error = None
                st.info("Fix skipped.")
                st.rerun()

    # Auto-apply path
    elif st.session_state.pending_fix and auto_apply:
        fix = st.session_state.pending_fix
        with st.spinner(f"Auto-applying: `{fix['fix_command']}`…"):
            apply_fix(fix["fix_command"])
        st.session_state.pending_fix = None
        st.rerun()


# ===========================================================================
# TAB 2 — History
# ===========================================================================
with tab_history:
    st.markdown("### Session History")
    history = st.session_state.history
    if not history:
        st.info("No commands run yet in this session.")
    else:
        for i, rec in enumerate(reversed(history)):
            status = "✓" if rec["result"]["success"] else "✗"
            color  = "green" if rec["result"]["success"] else "red"
            with st.expander(
                f"[{rec['timestamp']}]  {status}  `{rec['command']}`",
                expanded=(i == 0),
            ):
                st.write(f"**Exit code:** `{rec['result']['returncode']}`  |  **Time:** `{rec['result']['elapsed']}s`")
                if rec["result"]["stdout"].strip():
                    st.code(rec["result"]["stdout"], language="text")
                if rec["result"]["stderr"].strip():
                    st.code(rec["result"]["stderr"], language="text")


# ===========================================================================
# TAB 3 — Memory DB
# ===========================================================================
with tab_memory:
    st.markdown("### Error Memory Database")
    records = st.session_state.memory.get_all()
    if not records:
        st.info("No fixes stored yet. Run a failing command and apply a fix.")
    else:
        import pandas as pd
        df = pd.DataFrame(records)[
            ["id", "error_type", "command", "fix_command", "success", "applied_at"]
        ]
        df["success"] = df["success"].map({1: "✓", 0: "✗"})
        df["applied_at"] = df["applied_at"].str[:19]
        st.dataframe(df, use_container_width=True, hide_index=True)
