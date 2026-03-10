"""
demo_type_error.py
==================
DEMO: TypeError — agent detects incompatible types and suggests a fix

Run with:  agent> run demo_type_error.py
"""

scores = [95, 87, 92, 78, 88]
total_label = "Total score"

# BUG: This will throw TypeError — can't concatenate str and int
summary = total_label + sum(scores)

print(f"Result: {summary}")
print("Average:", sum(scores) / len(scores))
