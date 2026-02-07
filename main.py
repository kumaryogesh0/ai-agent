# main.py
from agent_logic import run_conversation, lead_data
import sys
import json

def print_lead_status():
    """Print current lead status"""
    print("\n" + "="*60)
    print("📊 CURRENT LEAD STATUS:")
    print("="*60)
    print(f"Name: {lead_data.get('name', '❌ Not captured')}")
    print(f"Phone: {lead_data.get('phone', '❌ Not captured')}")
    print(f"Project: {lead_data.get('interested_project_name', '❌ Not identified')}")
    print(f"Lead Submitted: {'✅ Yes' if lead_data.get('lead_submitted') else '❌ No'}")
    print("="*60 + "\n")

def start_chat():
    print("\n" + "="*60)
    print("🤖 REAL ESTATE AI AGENT STARTING...")
    print("="*60)
    print("Debug Mode: ON")
    print("Type 'status' to check lead status")
    print("Type 'exit' to stop the chat")
    print("="*60 + "\n")

    while True:
        try:
            user_input = input("You: ")
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Agent: Goodbye! Have a great day.")
                print_lead_status()
                break
            
            if user_input.lower() == 'status':
                print_lead_status()
                continue
            
            if not user_input.strip():
                continue

            print("\n🤖 Agent is thinking...\n")
            
            # Run conversation
            response = run_conversation(user_input)
            
            # Parse and display response
            try:
                response_json = json.loads(response)
                if "blocks" in response_json:
                    for block in response_json["blocks"]:
                        if block.get("component") == "Text":
                            print(f"\n💬 Agent: {block['props']['text']}\n")
                else:
                    print(f"\n💬 Agent: {response}\n")
            except:
                print(f"\n💬 Agent: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            print_lead_status()
            break
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    start_chat()