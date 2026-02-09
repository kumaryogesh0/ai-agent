# agent_logic.py
from openai import OpenAI
from tools import get_projects, add_lead_to_crm, send_otp, verify_otp
from system_prompt import SYSTEM_PROMPT
import json
import re

client = OpenAI()

# -----------------------
# MEMORY & LEAD STATE
# -----------------------

conversation_history = []
conversation_stage = "INITIAL"  # INITIAL, NAME_COLLECTED, PHONE_COLLECTED, OTP_SENT, VERIFIED, REQUIREMENT_GATHERING

lead_data = {
    "customer_type": None,  # "existing" or "new"
    "name": None,
    "phone": None,
    "phone_verified": False,
    "otp_sent": False,
    "interested_project_id": None,
    "interested_project_name": None,
    "lead_submitted": False,
    "conversation_remarks": [],
    "requirements": {
        "purpose": None,
        "budget": None,
        "possession": None,
        "configuration": None
    }
}

# =========================
# HELPERS
# =========================
def extract_name_from_message(message):
    """Extract name from user message"""
    words = message.strip().split()
    common_phrases = ['hi', 'hello', 'yes', 'no', 'okay', 'sure', 'my', 'name', 'is', 'i', 'am', 'the']
    
    # Filter out common phrases
    potential_name = ' '.join([w for w in words if w.lower() not in common_phrases])
    
    if potential_name and len(potential_name) > 1:
        return potential_name.strip().title()
    
    # Try regex pattern
    match = re.search(r"(?:my name is|i am|i'm|this is) (\w+(?:\s+\w+)?)", message, re.IGNORECASE)
    if match:
        return match.group(1).title()
    
    # If message is just a name (single or two words)
    if len(words) <= 2 and all(w[0].isupper() or w.lower() not in common_phrases for w in words):
        return message.strip().title()
    
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

def check_customer_type(message):
    """Check if user selected customer type"""
    message_lower = message.lower()
    if "existing" in message_lower or "already" in message_lower or "client" in message_lower:
        return "existing"
    elif "new" in message_lower or "guest" in message_lower or "first time" in message_lower:
        return "new"
    return None

def check_and_submit_lead():
    """Check if all required fields are present and submit lead to CRM"""
    print("\n" + "="*60)
    print("🔍 CHECKING LEAD SUBMISSION CONDITIONS:")
    print(f"   Name: {lead_data['name']}")
    print(f"   Phone: {lead_data['phone']}")
    print(f"   Phone Verified: {lead_data['phone_verified']}")
    print(f"   Project ID: {lead_data['interested_project_id']}")
    print(f"   Already Submitted: {lead_data['lead_submitted']}")
    print("="*60)
    
    # Check all conditions
    if (
        lead_data["name"] and 
        lead_data["phone"] and 
        lead_data["phone_verified"] and
        lead_data["interested_project_id"] and 
        not lead_data["lead_submitted"]
    ):
        print("\n✅ ALL CONDITIONS MET - SUBMITTING LEAD TO CRM...")
        
        # Prepare remarks
        requirements_text = ", ".join([f"{k}: {v}" for k, v in lead_data["requirements"].items() if v])
        remarks = " | ".join(lead_data["conversation_remarks"]) + f" | Requirements: {requirements_text}"
        
        # Call CRM API
        result = add_lead_to_crm(
            name=lead_data["name"],
            phone=lead_data["phone"],
            project_id=lead_data["interested_project_id"],
            remarks=remarks
        )
        
        if result.get("status") == "success":
            lead_data["lead_submitted"] = True
            print("\n🎉 ✅ LEAD SUCCESSFULLY SUBMITTED TO CRM!")
            return True
        else:
            print(f"\n❌ LEAD SUBMISSION FAILED: {result.get('message')}")
            return False
    else:
        print("\n⏳ CONDITIONS NOT MET YET - WAITING FOR MORE INFO...")
        return False

# =========================
# MAIN CONVERSATION
# =========================
def run_conversation(user_prompt):
    global conversation_history, lead_data, conversation_stage

    print(f"\n{'='*60}")
    print(f"💤 USER MESSAGE: {user_prompt}")
    print(f"📍 CURRENT STAGE: {conversation_stage}")
    print(f"{'='*60}\n")

    projects = get_projects("")  # dynamic fetch

    # ----------------- STAGE MANAGEMENT -----------------
    
    # Check for customer type selection
    if conversation_stage == "INITIAL":
        customer_type = check_customer_type(user_prompt)
        if customer_type:
            lead_data["customer_type"] = customer_type
            conversation_stage = "CUSTOMER_TYPE_SELECTED"
    
    # Extract Name
    if conversation_stage in ["CUSTOMER_TYPE_SELECTED", "NAME_REQUEST"] and not lead_data["name"]:
        name = extract_name_from_message(user_prompt)
        if name:
            lead_data["name"] = name
            lead_data["conversation_remarks"].append(f"Name: {name}")
            conversation_stage = "NAME_COLLECTED"
            print(f"✅ Name captured: {name}")

    # Extract Phone
    if conversation_stage == "PHONE_REQUEST" and not lead_data["phone"]:
        phone = extract_phone_from_message(user_prompt)
        if phone:
            lead_data["phone"] = phone
            lead_data["conversation_remarks"].append(f"Phone: {phone}")
            conversation_stage = "PHONE_COLLECTED"
            print(f"✅ Phone captured: {phone}")
            
            # Trigger OTP sending
            otp_result = send_otp(phone)
            if otp_result.get("status") == "success":
                lead_data["otp_sent"] = True
                conversation_stage = "OTP_SENT"
        elif len(user_prompt.replace(" ", "").replace("-", "")) < 10:
            # Invalid phone detected
            conversation_stage = "PHONE_INVALID"

    # Check for OTP in message
    if conversation_stage == "OTP_SENT" and lead_data["phone"]:
        # Extract OTP (6 digits typically)
        otp_match = re.search(r'\b\d{4,6}\b', user_prompt)
        if otp_match:
            otp = otp_match.group()
            verify_result = verify_otp(lead_data["phone"], otp)
            if verify_result.get("status") == "success":
                lead_data["phone_verified"] = True
                conversation_stage = "VERIFIED"
                print(f"✅ Phone verified successfully")
            else:
                conversation_stage = "OTP_INVALID"

    # Extract Project Interest
    if not lead_data["interested_project_id"]:
        project = extract_project_interest(user_prompt, projects)
        if project:
            lead_data["interested_project_id"] = project["id"]
            lead_data["interested_project_name"] = project["name"]
            lead_data["conversation_remarks"].append(f"Interested in: {project['name']}")
            print(f"✅ Project interest captured: {project['name']}")

    # Extract Requirements from options selected
    if "residential" in user_prompt.lower() or "investment" in user_prompt.lower() or "commercial" in user_prompt.lower():
        lead_data["requirements"]["purpose"] = user_prompt
    if "lakh" in user_prompt.lower() or "cr" in user_prompt.lower():
        lead_data["requirements"]["budget"] = user_prompt
    if "ready" in user_prompt.lower() or "year" in user_prompt.lower():
        lead_data["requirements"]["possession"] = user_prompt
    if "bhk" in user_prompt.lower() or "studio" in user_prompt.lower():
        lead_data["requirements"]["configuration"] = user_prompt

    # ----------------- SYSTEM PROMPT -----------------
    system_prompt = SYSTEM_PROMPT.format(
        name=lead_data.get('name', 'NOT CAPTURED'),
        phone=lead_data.get('phone', 'NOT CAPTURED'),
        phone_verified=lead_data.get('phone_verified', False),
        project_name=lead_data.get('interested_project_name', 'NOT IDENTIFIED'),
        lead_submitted=lead_data.get('lead_submitted', False),
        projects=json.dumps(projects, indent=2)
    )

    if not conversation_history:
        conversation_history.append({"role": "system", "content": system_prompt})
    
    # Add stage context to user message
    context_message = f"[STAGE: {conversation_stage}] {user_prompt}"
    conversation_history.append({"role": "user", "content": context_message})

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
                    "props": {"text": ai_reply}
                }]
            })

        conversation_history.append({"role": "assistant", "content": ai_reply})
        return ai_reply

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return json.dumps({
            "blocks": [{
                "component": "Text",
                "props": {"text": f"I apologize, but I'm experiencing a technical issue. Please try again or call us at **+91 92500-94500**."}
            }]
        })