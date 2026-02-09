# conversation_logger.py
import json
from datetime import datetime
import os

# File to store conversation logs
LOG_FILE = "conversation_logs.json"

def load_logs():
    """Load existing conversation logs"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_logs(logs):
    """Save conversation logs to file"""
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def log_conversation(session_id, user_message, ai_response, lead_data=None):
    """
    Log a conversation turn with timestamp
    
    Args:
        session_id: Unique identifier for the chat session
        user_message: The message from the user
        ai_response: The AI's response
        lead_data: Current lead information (optional)
    """
    logs = load_logs()
    
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "session_id": session_id,
        "timestamp": timestamp,
        "formatted_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_message": user_message,
        "ai_response": ai_response,
        "lead_data": lead_data or {}
    }
    
    logs.append(log_entry)
    save_logs(logs)
    
    print(f"✅ Logged conversation at {timestamp}")
    
    return log_entry

def get_session_logs(session_id):
    """Get all logs for a specific session"""
    logs = load_logs()
    return [log for log in logs if log.get("session_id") == session_id]

def get_all_sessions():
    """Get summary of all chat sessions"""
    logs = load_logs()
    sessions = {}
    
    for log in logs:
        sid = log.get("session_id")
        if sid not in sessions:
            sessions[sid] = {
                "session_id": sid,
                "first_message": log.get("timestamp"),
                "last_message": log.get("timestamp"),
                "message_count": 0,
                "lead_info": {}
            }
        
        sessions[sid]["message_count"] += 1
        sessions[sid]["last_message"] = log.get("timestamp")
        
        # Update lead info if available
        if log.get("lead_data"):
            sessions[sid]["lead_info"] = log.get("lead_data")
    
    return list(sessions.values())

def export_logs_csv():
    """Export logs to CSV format"""
    import csv
    
    logs = load_logs()
    
    if not logs:
        return "No logs to export"
    
    csv_file = f"conversation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'session_id', 'timestamp', 'user_message', 'ai_response', 
            'name', 'phone', 'project_interest'
        ])
        writer.writeheader()
        
        for log in logs:
            writer.writerow({
                'session_id': log.get('session_id'),
                'timestamp': log.get('formatted_time'),
                'user_message': log.get('user_message'),
                'ai_response': str(log.get('ai_response'))[:200],  # Truncate long responses
                'name': log.get('lead_data', {}).get('name', ''),
                'phone': log.get('lead_data', {}).get('phone', ''),
                'project_interest': log.get('lead_data', {}).get('interested_project_name', '')
            })
    
    print(f"✅ Exported logs to {csv_file}")
    return csv_file

# Analytics functions
def get_analytics():
    """Get conversation analytics"""
    logs = load_logs()
    sessions = get_all_sessions()
    
    total_visitors = len(sessions)
    total_messages = len(logs)
    
    # Count leads with phone numbers
    leads_captured = sum(1 for s in sessions if s.get('lead_info', {}).get('phone'))
    
    # Count verified leads
    verified_leads = sum(1 for s in sessions if s.get('lead_info', {}).get('phone_verified'))
    
    # Most interested projects
    project_interests = {}
    for s in sessions:
        project = s.get('lead_info', {}).get('interested_project_name')
        if project:
            project_interests[project] = project_interests.get(project, 0) + 1
    
    return {
        "total_visitors": total_visitors,
        "total_messages": total_messages,
        "leads_captured": leads_captured,
        "verified_leads": verified_leads,
        "conversion_rate": f"{(leads_captured/total_visitors*100):.1f}%" if total_visitors > 0 else "0%",
        "top_projects": sorted(project_interests.items(), key=lambda x: x[1], reverse=True)[:5]
    }