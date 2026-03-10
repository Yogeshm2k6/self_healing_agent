import json
import os

# INTENTIONAL BUG: We are trying to open a file that does not exist yet!
# When this errors out with FileNotFoundError, the self-healing agent 
# will ask the LLM for a fix. The LLM will suggest a command like:
# echo {"token":"demo123"} > demo_config.json
# The agent will execute it and restart the script!

def load_and_verify_config():
    print("Attempting to load demo_config.json...")
    with open("demo_config.json", "r") as file:
        config = json.load(file)
        
    print("✅ Configuration loaded successfully!")
    print(f"Server Name: {config.get('server_name', 'Unknown')}")
    print(f"API Token:   {config.get('api_token', 'No token found')}")
    
    # Just to add another layer, we check if valid
    if "api_token" not in config:
        raise KeyError("api_token is missing from the configuration file.")
        
if __name__ == "__main__":
    print("--- User Preferences Data Loader ---")
    load_and_verify_config()
