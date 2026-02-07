# agent_logic.py
from openai import OpenAI
from tools import get_projects, add_lead_to_crm
from system_prompt import SYSTEM_PROMPT
import json
import re

client = OpenAI()

# -----------------------
# MEMORY & LEAD STATE
# -----------------------

conversation_history = []

lead_data = {
    "name": None,
    "phone": None,
    "interested_project_id": None,
    "interested_project_name": None,
    "lead_submitted": False,
    "conversation_remarks": []
}

# =========================
# HELPERS
# =========================
def extract_name_from_message(message):
    """Extract name from user message"""
    words = message.strip().split()
    common_phrases = ['hi', 'hello', 'yes', 'no', 'okay', 'sure', 'haan', 'nahi', 'my', 'name', 'is']
    
    # Filter out common phrases
    potential_name = ' '.join([w for w in words if w.lower() not in common_phrases])
    
    if potential_name and len(potential_name) > 1:
        return potential_name.strip().title()
    
    # Try regex pattern
    match = re.search(r"my name is (\w+(?:\s+\w+)?)", message, re.IGNORECASE)
    if match:
        return match.group(1).title()
    
    return None

def extract_phone_from_message(message):
    """Extract 10-digit phone number from message"""
    # Remove all non-digits
    digits = re.sub(r'\D', '', message)
    
    # Handle country code +91
    if digits.startswith('91') and len(digits) > 10:
        digits = digits[2:]  # Remove 91 prefix
    
    # Handle leading zero
    if digits.startswith('0') and len(digits) > 10:
        digits = digits[1:]  # Remove leading 0
    
    # Check if exactly 10 digits
    if len(digits) == 10:
        print(f"✅ Valid phone extracted: {digits}")
        return digits
    
    # Check if more than 10 digits, take last 10
    if len(digits) > 10:
        phone = digits[-10:]
        print(f"✅ Valid phone extracted (last 10 digits): {phone}")
        return phone
    
    print(f"❌ Invalid phone: {digits} (length: {len(digits)})")
    return None

def safe_parse_projects(projects_str):
    """Safely parse projects string to list"""
    try:
        if isinstance(projects_str, str):
            return json.loads(projects_str.replace("'", '"'))
        return projects_str
    except:
        return []

def extract_project_interest(message, projects_str):
    """Extract project interest from user message"""
    message_lower = message.lower()
    projects = safe_parse_projects(projects_str)
    
    for p in projects:
        pname = p.get("name", "").lower()
        if pname and pname in message_lower:
            print(f"🎯 Project detected in user message: {p.get('name')}")
            return {"id": p.get("id"), "name": p.get("name")}
    
    return None

def extract_project_from_ai_response(ai_text, projects_str):
    """Extract project from AI response"""
    ai_text_lower = ai_text.lower()
    projects = safe_parse_projects(projects_str)
    
    for p in projects:
        pname = p.get("name", "").lower()
        if pname and pname in ai_text_lower:
            print(f"🎯 Project detected in AI response: {p.get('name')}")
            return {"id": p.get("id"), "name": p.get("name")}
    
    return None

def check_and_submit_lead():
    """Check if all required fields are present and submit lead to CRM"""
    print("\n" + "="*60)
    print("🔍 CHECKING LEAD SUBMISSION CONDITIONS:")
    print(f"   Name: {lead_data['name']}")
    print(f"   Phone: {lead_data['phone']}")
    print(f"   Project ID: {lead_data['interested_project_id']}")
    print(f"   Project Name: {lead_data['interested_project_name']}")
    print(f"   Already Submitted: {lead_data['lead_submitted']}")
    print("="*60)
    
    # Check all conditions
    if (
        lead_data["name"] and 
        lead_data["phone"] and 
        lead_data["interested_project_id"] and 
        not lead_data["lead_submitted"]
    ):
        print("\n✅ ALL CONDITIONS MET - SUBMITTING LEAD TO CRM...")
        
        # Prepare remarks
        remarks = " | ".join(lead_data["conversation_remarks"]) if lead_data["conversation_remarks"] else "Customer showed interest via AI chatbot"
        
        # Prepare payload for debugging
        payload = {
            "name": lead_data["name"],
            "phone": lead_data["phone"],
            "project_id": lead_data["interested_project_id"],
            "project_name": lead_data["interested_project_name"],
            "remarks": remarks
        }
        
        print("\n📦 CRM PAYLOAD:")
        print(json.dumps(payload, indent=2))
        
        # Call CRM API
        result = add_lead_to_crm(
            name=lead_data["name"],
            phone=lead_data["phone"],
            project_id=lead_data["interested_project_id"],
            remarks=remarks
        )
        
        print("\n📨 CRM API RESPONSE:")
        print(json.dumps(result, indent=2))
        
        # Check result
        if result.get("status") == "success":
            lead_data["lead_submitted"] = True
            print("\n🎉 ✅ LEAD SUCCESSFULLY SUBMITTED TO CRM!")
            return True
        else:
            print(f"\n❌ LEAD SUBMISSION FAILED!")
            print(f"Error: {result.get('message', 'Unknown error')}")
            return False
    else:
        print("\n⏳ CONDITIONS NOT MET YET - WAITING FOR MORE INFO...")
        if not lead_data["name"]:
            print("   ❌ Missing: Name")
        if not lead_data["phone"]:
            print("   ❌ Missing: Phone")
        if not lead_data["interested_project_id"]:
            print("   ❌ Missing: Project Interest")
        if lead_data["lead_submitted"]:
            print("   ℹ️ Lead already submitted")
        print("="*60 + "\n")
        return False

# =========================
# MAIN CONVERSATION
# =========================
def run_conversation(user_prompt):
    global conversation_history, lead_data

    print(f"\n{'='*60}")
    print(f"👤 USER MESSAGE: {user_prompt}")
    print(f"{'='*60}\n")

    projects = get_projects("")  # dynamic fetch

    # ----------------- EXTRACT INFO -----------------
    print("🔍 EXTRACTING INFORMATION FROM USER MESSAGE...\n")
    
    # Extract Name
    if not lead_data["name"]:
        name = extract_name_from_message(user_prompt)
        if name:
            lead_data["name"] = name
            lead_data["conversation_remarks"].append(f"Name: {name}")
            print(f"✅ Name captured: {name}")

    # Extract Phone
    if not lead_data["phone"]:
        phone = extract_phone_from_message(user_prompt)
        if phone:
            lead_data["phone"] = phone
            lead_data["conversation_remarks"].append(f"Phone: {phone}")
            print(f"✅ Phone captured: {phone}")

    # Extract Project Interest from user message
    if not lead_data["interested_project_id"]:
        project = extract_project_interest(user_prompt, projects)
        if project:
            lead_data["interested_project_id"] = project["id"]
            lead_data["interested_project_name"] = project["name"]
            lead_data["conversation_remarks"].append(f"Interested in: {project['name']}")
            print(f"✅ Project interest captured: {project['name']}")

    # ----------------- SYSTEM PROMPT -----------------
    system_prompt = SYSTEM_PROMPT.format(
        name=lead_data.get('name', 'NOT CAPTURED'),
        phone=lead_data.get('phone', 'NOT CAPTURED'),
        project_name=lead_data.get('interested_project_name', 'NOT IDENTIFIED'),
        lead_submitted=lead_data.get('lead_submitted', False),
        projects=json.dumps(projects)
    )

    if not conversation_history:
        conversation_history.append({"role": "system", "content": system_prompt})
    conversation_history.append({"role": "user", "content": user_prompt})

    # ----------------- AI CALL -----------------
    print("\n🤖 CALLING AI MODEL...\n")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            temperature=0.3
        )
        ai_reply = response.choices[0].message.content
        print(f"🤖 AI RESPONSE: {ai_reply}\n")

        # ----------------- PROJECT AUTO-DETECT FROM AI RESPONSE -----------------
        if not lead_data["interested_project_id"]:
            detected = extract_project_from_ai_response(ai_reply, projects)
            if detected:
                lead_data["interested_project_id"] = detected["id"]
                lead_data["interested_project_name"] = detected["name"]
                lead_data["conversation_remarks"].append(f"Interested in: {detected['name']}")
                print(f"✅ Project detected from AI response: {detected['name']}")

        # ----------------- AUTO CRM SUBMIT -----------------
        check_and_submit_lead()

        # ----------------- VALIDATE JSON -----------------
        try:
            json.loads(ai_reply)
        except:
            print("⚠️ Invalid JSON detected, wrapping in proper format...")
            ai_reply = json.dumps({
                "blocks": [{
                    "component": "Text",
                    "props": {"text": "⚠️ Kuch technical issue aa gaya hai. Please try again."}
                }]
            })

        conversation_history.append({"role": "assistant", "content": ai_reply})
        return ai_reply

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return json.dumps({
            "blocks": [{
                "component": "Text",
                "props": {"text": f"⚠️ Kuch technical issue aa gaya hai: {str(e)}"}
            }]
        })