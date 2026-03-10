"""
project_generator.py
--------------------
Uses the Groq LLM to generate entire multi-file projects based on a natural language description.
It asks the LLM to output files in a structured format, parses them, and saves them to a new folder.
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from logger import get_logger

load_dotenv()
log = get_logger(__name__)

_PROJECT_GEN_SYSTEM = """You are an expert full-stack developer.
The user wants to create a whole multi-file project.
You must generate the complete code for ALL necessary files.

Output FORMAT:
For each file you create, you MUST use exactly this format:

### FILE: <filename>
```<language>
<file contents here>
```

Example:
### FILE: index.html
```html
<!DOCTYPE html>
<html>...</html>
```

### FILE: main.py
```python
print("Hello")
```

Rules:
1. Provide fully functional, complete files. No placeholders like "TODO: add logic".
2. ALWAYS use the exact string "### FILE: filename" before the code block.
3. Keep it as simple and dependency-free as possible while satisfying the prompt.
4. Do NOT output any files outside this format.
"""

_PROJECT_GEN_HUMAN = "Create a project that: {description}"


def generate_project(description: str, project_name: str) -> dict:
    """
    Call the LLM to generate a multi-file project.
    Parses the response and saves the files into `./{project_name}/`.
    Returns dict with success status and list of created files.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

    if not api_key:
        log.error("GROQ_API_KEY not set.")
        return {"success": False, "error": "GROQ_API_KEY not set", "files": []}

    log.info(f"Generating project '{project_name}'...")

    llm = ChatGroq(model=model, temperature=0.2, groq_api_key=api_key)

    response = llm.invoke([
        SystemMessage(content=_PROJECT_GEN_SYSTEM),
        HumanMessage(content=_PROJECT_GEN_HUMAN.format(description=description)),
    ])

    raw_text = response.content

    # Parse the format:
    # ### FILE: filename.ext
    # ```lang
    # code
    # ```
    
    # regex matches:
    # Group 1: filename
    # Group 2: language (optional)
    # Group 3: file contents
    pattern = re.compile(
        r"###\s*FILE:\s*([^\n]+)\n+```[a-zA-Z0-9]*\n(.*?)```", 
        re.DOTALL | re.IGNORECASE
    )

    matches = pattern.findall(raw_text)

    if not matches:
        log.error("Failed to parse any files from LLM output. Raw output:\n" + raw_text[:500])
        return {"success": False, "error": "LLM did not return files in the correct format.", "files": []}

    # Create project directory
    project_dir = Path(project_name)
    project_dir.mkdir(parents=True, exist_ok=True)

    created_files = []

    for filename, code_content in matches:
        filename = filename.strip()
        code_content = code_content.strip() + "\n"
        
        # Prevent path traversal
        safe_filename = os.path.basename(filename)
        file_path = project_dir / safe_filename
        
        file_path.write_text(code_content, encoding="utf-8")
        created_files.append(str(file_path))

    return {
        "success": True,
        "project_dir": str(project_dir),
        "files": created_files
    }

def description_to_project_name(description: str) -> str:
    """Convert natural language to a safe snake_case directory name."""
    words = re.sub(r"[^a-z0-9 ]", "", description.lower()).split()
    name = "_".join(words[:4]) or "my_project"
    return name

def is_project_command(text: str) -> tuple[bool, str]:
    """
    Check if the user is asking to create a multi-file project.
    E.g. "make a project in which..." or "create a project that..."
    Returns (True, description) if matched.
    """
    text_lower = text.strip().lower()

    
    # explicit prefix
    if text_lower.startswith("project ") or text_lower.startswith("create project "):
        desc = re.sub(r"^(create\s+)?project\s+", "", text.strip(), flags=re.IGNORECASE)
        return True, desc
        
    # phrases
    if "make a project" in text_lower or "create a project" in text_lower or "build a project" in text_lower or "a whole project" in text_lower:
        return True, text.strip()
        
    return False, ""
