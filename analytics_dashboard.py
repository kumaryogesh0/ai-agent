# analytics_dashboard.py
"""
Run this script to view conversation analytics and logs
Usage: python analytics_dashboard.py
"""

from conversation_logger import get_analytics, get_all_sessions, export_logs_csv, load_logs
from datetime import datetime
import json

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def display_analytics():
    """Display conversation analytics"""
    print_header("📊 CONVERSATION ANALYTICS")
    
    analytics = get_analytics()
    
    print(f"\n👥 Total Visitors: {analytics['total_visitors']}")
    print(f"💬 Total Messages: {analytics['total_messages']}")
    print(f"📞 Leads Captured: {analytics['leads_captured']}")
    print(f"✅ Verified Leads: {analytics['verified_leads']}")
    print(f"📈 Conversion Rate: {analytics['conversion_rate']}")
    
    print("\n🏆 Top Project Interests:")
    for project, count in analytics['top_projects']:
        print(f"   • {project}: {count} leads")

def display_recent_conversations(limit=10):
    """Display recent conversations"""
    print_header(f"📝 RECENT CONVERSATIONS (Last {limit})")
    
    logs = load_logs()
    recent = logs[-limit:][::-1]  # Get last N and reverse
    
    for i, log in enumerate(recent, 1):
        print(f"\n{i}. Session: {log['session_id'][:8]}...")
        print(f"   Time: {log['formatted_time']}")
        print(f"   User: {log['user_message'][:50]}...")
        
        # Show lead info if available
        lead = log.get('lead_data', {})
        if lead.get('name'):
            print(f"   👤 Name: {lead['name']}")
        if lead.get('phone'):
            print(f"   📞 Phone: {lead['phone']}")
        if lead.get('interested_project_name'):
            print(f"   🏡 Interest: {lead['interested_project_name']}")

def display_session_details(session_id):
    """Display full conversation for a session"""
    print_header(f"🔍 SESSION DETAILS: {session_id}")
    
    logs = load_logs()
    session_logs = [l for l in logs if l['session_id'] == session_id]
    
    if not session_logs:
        print("❌ Session not found!")
        return
    
    for i, log in enumerate(session_logs, 1):
        print(f"\n--- Message {i} ({log['formatted_time']}) ---")
        print(f"👤 User: {log['user_message']}")
        
        # Try to parse AI response
        try:
            ai_resp = json.loads(log['ai_response'])
            if 'blocks' in ai_resp:
                for block in ai_resp['blocks']:
                    if block.get('component') == 'Text':
                        print(f"🤖 AI: {block['props']['text'][:100]}...")
        except:
            print(f"🤖 AI: {str(log['ai_response'])[:100]}...")

def main_menu():
    """Interactive menu for analytics"""
    while True:
        print("\n" + "="*60)
        print("  🏢 AMOGH BUILDTECH - CHATBOT ANALYTICS")
        print("="*60)
        print("\n1. View Analytics Summary")
        print("2. View Recent Conversations")
        print("3. View All Sessions")
        print("4. View Session Details")
        print("5. Export Logs to CSV")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            display_analytics()
        elif choice == '2':
            try:
                limit = int(input("How many conversations to show? (default 10): ") or "10")
                display_recent_conversations(limit)
            except:
                display_recent_conversations(10)
        elif choice == '3':
            print_header("📋 ALL SESSIONS")
            sessions = get_all_sessions()
            for i, s in enumerate(sessions, 1):
                print(f"\n{i}. Session: {s['session_id'][:8]}...")
                print(f"   First: {s['first_message']}")
                print(f"   Last: {s['last_message']}")
                print(f"   Messages: {s['message_count']}")
                if s['lead_info'].get('name'):
                    print(f"   Name: {s['lead_info']['name']}")
                if s['lead_info'].get('phone'):
                    print(f"   Phone: {s['lead_info']['phone']}")
        elif choice == '4':
            session_id = input("Enter session ID: ").strip()
            display_session_details(session_id)
        elif choice == '5':
            filename = export_logs_csv()
            print(f"\n✅ Logs exported to: {filename}")
        elif choice == '6':
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()