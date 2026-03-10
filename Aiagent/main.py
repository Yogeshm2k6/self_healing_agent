import os
import subprocess
import json
import requests
from transformers import pipeline
import torch
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse

# Initialize the LLM model
llm_model = pipeline("text-generation", model="t5-base")

# Initialize the API client
api_client = requests.Session()

def monitor_command_execution(command):
    try:
        # Execute the command
        output = subprocess.check_output(command, shell=True)
        # Parse the output
        output = output.decode("utf-8")
        # Check for errors
        if "Error" in output or "Exception" in output:
            # Analyze the error using the LLM
            error_text = output.split("\n")[-1]
            analysis = llm_model(error_text, max_length=1024)
            # Get the suggested fix
            suggested_fix = analysis[0]["generated_text"]
            # Ask the user for approval
            approval = input(f"Error detected: {error_text}\nSuggested fix: {suggested_fix}\nApprove? (y/n): ")
            if approval.lower() == "y":
                # Apply the fix
                fix_command = f"python -c '{suggested_fix}'"
                subprocess.run(fix_command, shell=True)
            else:
                # Do nothing
                pass
        else:
            # No errors detected
            pass
    except Exception as e:
        # Handle any exceptions
        print(f"Error: {e}")

def handle_http_errors(url):
    try:
        response = requests.head(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            print(f"404 Error: Page not found at {url}")
        elif http_err.response.status_code == 500:
            print(f"500 Error: Internal Server Error at {url}")
        else:
            print(f"HTTP Error: {http_err}")
    except Exception as err:
        print(f"Other Error: {err}")

def main():
    # Get the current working directory
    cwd = os.getcwd()
    # Get the list of files in the current directory
    files = os.listdir(cwd)
    # Monitor each file
    for file in files:
        # Check if the file is a Python script
        if file.endswith(".py"):
            # Monitor the command execution
            command = f"python {file}"
            monitor_command_execution(command)
    # Get the list of URLs from a file (for example, a text file named 'urls.txt')
    url_file = 'urls.txt'
    if os.path.exists(url_file):
        with open(url_file, 'r') as f:
            urls = f.readlines()
        for url in urls:
            url = url.strip()
            handle_http_errors(url)

if __name__ == "__main__":
    main()