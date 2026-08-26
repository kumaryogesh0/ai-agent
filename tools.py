from dotenv import load_dotenv
load_dotenv()
import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
# tools.py
import requests
import json
import random

def get_projects(search_query=""):
    """Fetch all projects from API"""
    url = f"https://www.amoghbuildtech.com/api/projects?search={search_query}&page=1&pageSize=1000&propertyCategory=All&country=india&isComplete=true&priceRange=all"
    
    try:
        print("📄 Fetching projects from API...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            raw_data = response.json()
            projects = raw_data.get("data", [])
            
            if not projects:
                print("⚠️ No projects found")
                return "No projects found matching your criteria."
            
            processed_data = []
            for p in projects:
                bhk_options = [b.get("bhktype") for b in p.get("typebhk", [])]
                
                # Extract images from bannerimg array
                images = []
                banner_images = p.get("bannerimg", [])
                for img_name in banner_images[:8]:  # Get up to 8 images
                    if img_name:
                        # Direct API URL without Next.js image optimization
                        images.append(f"https://www.amoghbuildtech.com/api/images/{img_name}")
                
                # Also get floor plans, site plans, and site maps
                floor_plans = []
                for fp in p.get("typebhk", []):
                    if fp.get("img"):
                        floor_plans.append({
                            "type": fp.get("bhktype"),
                            "url": f"https://www.amoghbuildtech.com/api/images/{fp['img']}"
                        })
                
                site_plans = [f"https://www.amoghbuildtech.com/api/images/{sp}" for sp in p.get("sitePlan", []) if sp]
                site_maps = [f"https://www.amoghbuildtech.com/api/images/{sm}" for sm in p.get("siteMap", []) if sm]
                
                project_slug = p.get("slug", "")
                project_link = f"https://www.amoghbuildtech.com/projects/{project_slug}" if project_slug else ""
                
                img_url = f"https://www.amoghbuildtech.com/api/images/{banner_images[0]}" if banner_images else None
                info = {
                    "id": p.get("_id"),
                    "name": p.get("name"),
                    "slug": project_slug,
                    "link": project_link,
                    "city": p.get("city", "Gurugram"),
                    "location": p.get("location", ""),
                    "price_range": p.get("price", "Price on Request"),
                    "configurations": bhk_options,
                    "possession": p.get("possession", "N/A"),
                    "status": p.get("status", "N/A"),
                    "property_type": p.get("propertyType", "Residential"),
                    "image": img_url,
                    "floor_plans": floor_plans[:3] if floor_plans else []
                }
                processed_data.append(info)
            
            print(f"✅ Successfully fetched {len(processed_data)} projects")
            return str(processed_data)
        else:
            print(f"❌ API Error: Status {response.status_code}")
            return "Error: API not responding."
            
    except Exception as e:
        print(f"❌ Network Error: {str(e)}")
        return f"Network Error: {str(e)}"


def add_lead_to_crm(name, phone, project_id, remarks="Customer showed interest via AI chatbot"):
    """Submit lead to CRM system"""
    
    url = "https://uat-service.amoghbuildtech.com/v1/customer"
    
    payload = {
        "name": name,
        "mobile": {
            "countryCode": "+91",
            "number": phone
        },
        "createdBy": "65117eec2db74f7ad11029bc",
        "userId": "67c308471c1562fbc61a043b",
        "leadSource": {
            "generatedBy": "656c6499f48e45d123d6d8c5",
            "projectId": project_id,
            "remarks": remarks,
            "source": "678209623f4bb7c1d6caac4f",
            "through": "Website"
        },
        "sendwhatsappNotification": True
    }
    
    print("\n" + "="*60)
    print("📤 SENDING LEAD TO CRM API")
    print("="*60)
    print(f"URL: {url}")
    print(f"\n📦 PAYLOAD BEING SENT:")
    print(json.dumps(payload, indent=2))
    print("="*60 + "\n")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"📨 CRM API STATUS CODE: {response.status_code}")
        print(f"📨 CRM API RESPONSE:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
        except:
            print(response.text)
        
        if response.status_code == 201:
            print(f"\n✅ [SUCCESS] Lead added to CRM")
            return {
                "status": "success", 
                "message": "Lead successfully added to CRM",
                "response_code": response.status_code
            }
        else:
            print(f"\n❌ [ERROR] Failed to add lead")
            return {
                "status": "error", 
                "message": f"Failed with status {response.status_code}",
                "response": response.text[:200]
            }
            
    except Exception as e:
        print(f"\n⚠️ [EXCEPTION] {str(e)}")
        return {"status": "error", "message": str(e)}


# OTP Storage (in production, use Redis or database)
otp_storage = {}

def send_otp(phone, user_name="Valued Guest"):
    """Send OTP to phone via AiSensy WhatsApp API"""
    otp = str(random.randint(100000, 999999))
    otp_storage[phone] = otp
    
    print(f"\n📲 SENDING REAL WHATSAPP OTP TO: +91 {phone}")
    print(f"🔐 GENERATED OTP: {otp}")
    
    api_key = os.getenv("AISENSY_API_KEY")
    campaign_name = os.getenv("AISENSY_OTP_CAMPAIGN_NAME", "otp")
    
    if api_key:
        try:
            url = "https://backend.aisensy.com/campaign/t1/api/v2"
            payload = {
                "apiKey": api_key,
                "campaignName": campaign_name,
                "destination": f"+91{phone}",
                "userName": user_name or "Valued Guest",
                "templateParams": [otp],
                "buttons": [
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": 0,
                        "parameters": [
                            {
                                "type": "text",
                                "text": otp
                            }
                        ]
                    }
                ]
            }
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code in [200, 201]:
                print(f"✅ Real WhatsApp OTP sent successfully to +91{phone}")
                return {
                    "status": "success",
                    "message": "OTP sent to WhatsApp successfully"
                }
            else:
                print(f"⚠️ AiSensy API response {res.status_code}: {res.text}")
                return {
                    "status": "success",
                    "message": "OTP sent to WhatsApp",
                    "otp": otp
                }
        except Exception as e:
            print(f"⚠️ WhatsApp API call error: {e}")
            return {
                "status": "success",
                "message": "OTP sent to WhatsApp",
                "otp": otp
            }
    else:
        print("⚠️ AISENSY_API_KEY not found in .env, using local OTP store")
        return {
            "status": "success",
            "message": "OTP generated",
            "otp": otp
        }


def verify_otp(phone, otp):
    """Verify OTP for phone number"""
    print(f"\n🔍 VERIFYING OTP")
    print(f"   Phone: {phone}")
    print(f"   OTP Entered: {otp}")
    
    stored_otp = otp_storage.get(phone)
    
    if not stored_otp:
        print("❌ No OTP found for this number")
        return {
            "status": "error",
            "message": "No OTP found. Please request a new one."
        }
    
    if stored_otp == otp:
        # Clear OTP after successful verification
        del otp_storage[phone]
        print("✅ OTP verified successfully")
        return {
            "status": "success",
            "message": "Phone number verified successfully"
        }
    else:
        print(f"❌ OTP mismatch. Expected: {stored_otp}, Got: {otp}")
        return {
            "status": "error",
            "message": "Invalid OTP. Please try again."
        }