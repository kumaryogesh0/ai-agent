from dotenv import load_dotenv
load_dotenv()
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from agent_logic import run_conversation, get_lead_data
import json

def print_lead_status(session_id="default"):
    """Print current lead status"""
    lead_data = get_lead_data(session_id)
    print("\n" + "="*60)
    print("📊 CURRENT LEAD STATUS:")
    print("="*60)
    print(f"Name: {lead_data.get('name') or '❌ Not captured'}")
    print(f"Phone: {lead_data.get('phone') or '❌ Not captured'}")
    print(f"Project: {lead_data.get('interested_project_name') or '❌ Not identified'}")
    print(f"Phone Verified: {'✅ Yes' if lead_data.get('phone_verified') else '❌ No'}")
    print("="*60 + "\n")

def display_agent_response(response_raw):
    try:
        data = json.loads(response_raw) if isinstance(response_raw, str) else response_raw
        if isinstance(data, dict) and "blocks" in data:
            for block in data["blocks"]:
                comp = block.get("component")
                props = block.get("props", {})

                if comp == "Text":
                    print(f"\n🤖 Agent: {props.get('text', '')}\n")
                elif comp == "Options":
                    opts = props.get("options", [])
                    print("👉 Select an Option:")
                    for idx, opt in enumerate(opts, 1):
                        print(f"   [{idx}] {opt}")
                    print()
                elif comp == "PhoneInput":
                    print("📱 [Please type your 10-digit WhatsApp number]\n")
                elif comp == "OTPInput":
                    print("🔐 [Please type the OTP sent to your WhatsApp]\n")
                elif comp in ["ProjectTable", "ProjectLinks"]:
                    projects = props.get("projects") or props.get("data") or []
                    print("🏢 Recommended Projects:")
                    for p in projects[:4]:
                        print(f"   • {p.get('name')} | {p.get('location', '')} | Price: {p.get('price_range') or p.get('price')}")
                        if p.get('link'):
                            print(f"     Link: {p.get('link')}")
                    print()
        else:
            print(f"\n🤖 Agent: {response_raw}\n")
    except Exception as e:
        print(f"\n🤖 Agent: {response_raw}\n")

def start_chat():
    print("\n" + "="*60)
    print("🏡 AMOGH BUILDTECH - REAL ESTATE AI AGENT")
    print("="*60)
    print("Commands:")
    print("  • Type 'status' to check current lead info")
    print("  • Type 'exit' or 'quit' to end chat")
    print("="*60)

    # Initial greeting trigger
    print("\n⏳ Initializing AI Agent...")
    init_res = run_conversation("Hello")
    display_agent_response(init_res)

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Agent: Thank you for chatting with Amogh Buildtech! Have a wonderful day.")
                print_lead_status()
                break

            if user_input.lower() == 'status':
                print_lead_status()
                continue

            # If user typed a number matching option list (e.g. 1 or 2), you can support it
            print("\n⏳ Agent is thinking...\n")
            response = run_conversation(user_input)
            display_agent_response(response)

        except KeyboardInterrupt:
            print("\n\n👋 Exiting chat...")
            print_lead_status()
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    start_chat()
