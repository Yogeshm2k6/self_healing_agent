"""
demo_zero_division.py
=====================
DEMO: ZeroDivisionError — agent catches divide-by-zero and suggests a guard

Run with:  agent> run demo_zero_division.py
"""

def calculate_average(total, count):
    return total / count   # BUG: will crash if count == 0

students = [
    {"name": "Alice",  "marks": 450},
    {"name": "Bob",    "marks": 380},
    {"name": "Charlie","marks": 0},
]

total_students = 0   # BUG: starts at 0 — nobody incremented it!
total_marks    = sum(s["marks"] for s in students)

avg = calculate_average(total_marks, total_students)
print(f"Class Average: {avg:.2f}")
