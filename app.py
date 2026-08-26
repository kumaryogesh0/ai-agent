import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from agent_logic import run_conversation, get_lead_data
import json

app = Flask(__name__)
CORS(app)  # Allow Next.js app to communicate

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message")
    session_id = data.get("session_id", "default")
    
    # Get response from agent
    response = run_conversation(user_message, session_id=session_id)
    lead = get_lead_data(session_id)
    
    # Parse the JSON string response
    try:
        response_json = json.loads(response)
        if isinstance(response_json, dict):
            response_json["leadData"] = lead
            if lead.get("name"):
                response_json["userName"] = lead.get("name")
        return jsonify(response_json)
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Response was: {response}")
        # Return fallback response
        return jsonify({
            "blocks": [{
                "component": "Text",
                "props": {
                    "text": "I'm having trouble processing your request. Please try again or call **+91 92500-94500**."
                }
            }]
        })

if __name__ == "__main__":
    # Render sets the PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)