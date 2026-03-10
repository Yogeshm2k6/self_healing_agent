from flask import Flask, jsonify
import sys

# INTENTIONAL BUG 1: The flask module may not be installed. 
# The agent will catch the ModuleNotFoundError and run: pip install flask
app = Flask(__name__)

@app.route("/")
def home():
    # INTENTIONAL BUG 2: This would normally error if started without the right config, 
    # but the agent is smart enough to handle missing modules first!
    return jsonify({
        "status": "success",
        "message": "Welcome to the Self-Healing Demo Web API!"
    })

if __name__ == "__main__":
    print("🚀 Starting the Presentation REST API on port 8080...")
    # The agent will auto-install flask, run this script again, 
    # and you'll see the server start gracefully!
    app.run(host="0.0.0.0", port=8080)
