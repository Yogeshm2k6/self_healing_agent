"""
test_app.py
-----------
A deliberately broken test script to demonstrate the Self-Healing Agent.

Run via the agent:
    python main.py "python test_app.py"

Expected behaviour:
    1. Agent detects: ModuleNotFoundError: No module named 'pandas'
    2. LLM suggests: pip install pandas
    3. After approval and installation, this script runs successfully.
"""

import pandas as pd  # will fail if pandas is not installed

data = {
    "Name":  ["Alice", "Bob", "Charlie"],
    "Score": [95, 87, 92],
}

df = pd.DataFrame(data)
print("✓ Script ran successfully!")
print(df.to_string(index=False))
