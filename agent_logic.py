import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()
# agent_logic.py
from openai import OpenAI
from tools import get_projects, add_lead_to_crm, send_otp, verify_otp
from system_prompt import SYSTEM_PROMPT
from conversation_logger import log_conversation
import json
import re
import uuid

client = OpenAI()

# -----------------------
# MEMORY & LEAD STATE
# -----------------------

# -----------------------
# PER-SESSION STATE STORE
# -----------------------
_sessions: dict = {}

def _get_session(sid: str) -> dict:
    if sid not in _sessions:
        _sessions[sid] = {
            'conversation_history': [],
            'conversation_stage': 'INITIAL',
            'lead_data': {
                'customer_type': None,
                'name': None,
                'phone': None,
                'phone_verified': False,
                'otp_sent': False,
                'interested_project_id': None,
                'interested_project_name': None,
                'lead_submitted': False,
                'conversation_remarks': [],
                'requirements': {
                    'purpose': None,
                    'budget': None,
                    'possession': None,
                    'configuration': None
                }
            }
        }
    return _sessions[sid]

def get_lead_data(session_id: str = "default") -> dict:
    return _get_session(session_id)['lead_data']

# Backward compatibility for direct imports
lead_data = _get_session("default")['lead_data']

# =========================
# HELPERS
# =========================
def extract_name_from_message(message):
    """Extract full name from user message (filtering out options and customer type keywords)"""
    trimmed = message.strip()
    words = trimmed.split()
    
    invalid_keywords = {
        'guest', 'client', 'customer', 'broker', 'investor', 'agent',
        'existing', 'new', 'residential', 'commercial', 'project', 'projects',
        'gurgaon', 'amogh', 'hi', 'hello', 'hey', 'yes', 'no', 'okay', 'sure',
        'options', 'help', 'details', 'call', 'callback', 'brochure', 'floor',
        'plan', 'price', 'budget', 'bhk', 'ready', 'move', 'construction',
        '1bhk', '2bhk', '3bhk', '4bhk', '5bhk', 'plot', 'plots', 'villa', 'villas',
        'flat', 'flats', 'apartment', 'apartments'
    }
    
    if any(w.lower().rstrip('s') in invalid_keywords for w in words):
        return None
        
    match = re.search(r"(?:my name is|i am|i'm|this is)\s+([a-zA-Z\s]+)", trimmed, re.IGNORECASE)
    if match:
        extracted = match.group(1).strip()
        extracted_words = extracted.split()
        if not any(w.lower() in invalid_keywords for w in extracted_words) and len(extracted) >= 2:
            return extracted.title()
    
    filler_words = {'my', 'name', 'is', 'i', 'am', 'the', 'a', 'mr', 'mrs', 'ms', 'dr'}
    clean_words = [w for w in words if w.lower() not in filler_words and not re.search(r'\d', w)]
    
    if clean_words and len(clean_words) <= 5:
        candidate = ' '.join(clean_words)
        if len(candidate) >= 2 and all(w.replace('.', '').isalpha() for w in clean_words):
            return candidate.strip().title()
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

def check_and_submit_lead(lead_data):
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
def run_conversation(user_prompt, session_id="default"):
    sess = _get_session(session_id)
    conversation_history = sess['conversation_history']
    lead_data = sess['lead_data']
    conversation_stage = sess['conversation_stage']

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
            print(f"✅ Customer type captured: {customer_type}")
    
    # Extract Name: When AI asked for name in previous step, this user message IS their direct full name!
    elif conversation_stage in ["CUSTOMER_TYPE_SELECTED", "NAME_REQUEST"]:
        # Clean user message directly as name
        clean_name = user_prompt.strip().title()
        if clean_name and len(clean_name) >= 2:
            lead_data["name"] = clean_name
            lead_data["conversation_remarks"].append(f"Name: {clean_name}")
            conversation_stage = "NAME_COLLECTED"
            print(f"✅ Name captured directly from user response: {clean_name}")

    # Extract Phone
    if (conversation_stage in ["PHONE_REQUEST", "NAME_COLLECTED"] or not lead_data["phone"]) and not lead_data["phone_verified"]:
        phone = extract_phone_from_message(user_prompt)
        if phone:
            lead_data["phone"] = phone
            lead_data["conversation_remarks"].append(f"Phone: {phone}")
            lead_data["otp_sent"] = True
            conversation_stage = "OTP_SENT"
            print(f"✅ Phone captured & set to OTP_SENT: {phone}")
        elif len(user_prompt.replace(" ", "").replace("-", "")) < 10 and conversation_stage == "PHONE_REQUEST":
            conversation_stage = "PHONE_INVALID"

    # Check for OTP verification in message (verified by Next.js /api/otp/verify)
    if (conversation_stage in ["OTP_SENT", "PHONE_COLLECTED"] or lead_data["phone"]) and not lead_data["phone_verified"]:
        otp_match = re.search(r'\b\d{4,6}\b', user_prompt)
        is_verified_msg = "verified" in user_prompt.lower() or "success" in user_prompt.lower()
        if otp_match or is_verified_msg:
            lead_data["phone_verified"] = True
            conversation_stage = "VERIFIED"
            print(f"✅ Phone verified successfully in session for: {lead_data['phone']}")

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

    # Save updated stage back to session
    sess['conversation_stage'] = conversation_stage

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
    else:
        # Always update system prompt with latest lead details on each turn
        conversation_history[0] = {"role": "system", "content": system_prompt}
    
    # Keep conversation history compact to prevent slowdown (keep system + last 12 messages)
    if len(conversation_history) > 13:
        conversation_history = [conversation_history[0]] + conversation_history[-12:]
        sess['conversation_history'] = conversation_history

    # Add stage context to user message
    context_message = f"[STAGE: {conversation_stage}] {user_prompt}"
    conversation_history.append({"role": "user", "content": context_message})

    # ----------------- AI CALL -----------------
    print("\n🤖 CALLING AI MODEL...\n")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        ai_reply = response.choices[0].message.content
        print(f"🤖 AI RESPONSE: {ai_reply}\n")

        # ----------------- AUTO CRM SUBMIT -----------------
        check_and_submit_lead(lead_data)

        # ----------------- CLEAN & VALIDATE JSON -----------------
        clean_reply = ai_reply.strip()
        if clean_reply.startswith("```"):
            clean_reply = re.sub(r"^```(?:json)?\s*", "", clean_reply)
            clean_reply = re.sub(r"\s*```$", "", clean_reply)

        try:
            parsed = json.loads(clean_reply)
            if not isinstance(parsed, dict) or "blocks" not in parsed:
                parsed = {
                    "blocks": [{
                        "component": "Text",
                        "props": {"text": clean_reply}
                    }]
                }
            ai_reply = json.dumps(parsed)
        except Exception as json_err:
            print(f"⚠️ Invalid JSON detected ({json_err}), wrapping in proper format...")
            ai_reply = json.dumps({
                "blocks": [{
                    "component": "Text",
                    "props": {"text": clean_reply}
                }]
            })

        conversation_history.append({"role": "assistant", "content": ai_reply})
        
        # Conversation logging disabled (in-memory only)
        # log_conversation(...)
        
        return ai_reply

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return json.dumps({
            "blocks": [{
                "component": "Text",
                "props": {"text": f"I apologize, but I'm experiencing a technical issue. Please try again or call us at **+91 92500-94500**."}
            }]
        })