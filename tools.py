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
                
                
                info = {
                    "id": p.get("_id"),
                    "name": p.get("name"),
                    "slug": project_slug,
                    "link": project_link,
                    "location": f"{p.get('city')}, Sector {p.get('slug').split('-')[-2] if '-' in p.get('slug', '') else 'N/A'}",
                    "price_range": p.get("price"),
                    "configurations": bhk_options,
                    "possession": p.get("possession"),
                    "size": p.get("projectarea", "N/A"),
                    "images": images,
                    "floor_plans": floor_plans,
                    "site_plans": site_plans,
                    "site_maps": site_maps,
                    "amenities": p.get("amenities", [])[:20],  # First 20 amenities IDs
                    "key_features": p.get("keyfeatures", []),
                    "highlights": p.get("highlight", []),
                    "rera_id": p.get("reraId", "N/A"),
                    "status": p.get("status", "N/A"),
                    "towers": p.get("towers", "N/A"),
                    "units": p.get("units", "N/A"),
                    "floors": p.get("floors", []),
                    "total_area": p.get("totalProjectArea", {})
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

def send_otp(phone):
    """Send OTP to phone via WhatsApp"""
    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    
    # Store OTP (in production, use Redis with TTL)
    otp_storage[phone] = otp
    
    print(f"\n📱 SENDING OTP TO: +91 {phone}")
    print(f"🔢 OTP GENERATED: {otp}")
    
    # TODO: Integrate with actual WhatsApp API (Twilio, MessageBird, etc.)
    # For now, just log it
    
    try:
        # Placeholder for WhatsApp API integration
        # Example with Twilio:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     from_='whatsapp:+14155238886',
        #     body=f'Your Amogh Buildtech verification code is: {otp}',
        #     to=f'whatsapp:+91{phone}'
        # )
        
        print(f"✅ OTP sent successfully (simulated)")
        return {
            "status": "success",
            "message": "OTP sent to WhatsApp",
            "otp": otp  # Remove this in production!
        }
    
    except Exception as e:
        print(f"❌ Failed to send OTP: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
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