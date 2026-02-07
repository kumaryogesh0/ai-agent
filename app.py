import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from agent_logic import run_conversation

app = Flask(__name__)
CORS(app) # Taaki aapka Next.js app isse baat kar sake

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message")
    response = run_conversation(user_message)
    return response # response pehle se JSON string hai agent_logic.py se

if __name__ == "__main__":
    # Render sets the PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)