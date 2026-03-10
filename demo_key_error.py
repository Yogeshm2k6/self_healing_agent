"""
demo_key_error.py
=================
DEMO: KeyError — agent identifies the missing key and suggests a fix

Run with:  agent> run demo_key_error.py
"""

user_profile = {
    "name": "Yogesh",
    "age": 22,
    "city": "Chennai"
}

# BUG: 'email' key does not exist in the dictionary
print(f"Name:  {user_profile['name']}")
print(f"City:  {user_profile['city']}")
print(f"Email: {user_profile['email']}")   # <-- KeyError here!
print(f"Age:   {user_profile['age']}")
