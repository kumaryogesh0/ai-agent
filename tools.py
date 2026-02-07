# tools.py
import requests
import json

def get_projects(search_query=""):
    """Fetch all projects from API"""
    url = f"https://www.amoghbuildtech.com/api/projects?search={search_query}&page=1&pageSize=1000&propertyCategory=All&country=india&isComplete=true&priceRange=all"
    
    try:
        print("🔄 Fetching projects from API...")
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
                info = {
                    "id": p.get("_id"),
                    "name": p.get("name"),
                    "location": f"{p.get('city')}, Sector {p.get('slug').split('-')[-2]}",
                    "price_range": p.get("price"),
                    "configurations": bhk_options,
                    "possession": p.get("possession")
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
            print(f"   Name: {name}")
            print(f"   Phone: {phone}")
            print(f"   Project ID: {project_id}")
            return {
                "status": "success", 
                "message": "Lead successfully added to CRM",
                "response_code": response.status_code
            }
        else:
            print(f"\n❌ [ERROR] Failed to add lead")
            print(f"   Status Code: {response.status_code}")
            return {
                "status": "error", 
                "message": f"Failed with status {response.status_code}",
                "response": response.text[:200]
            }
            
    except requests.exceptions.Timeout:
        print(f"\n⏱️ [TIMEOUT] Request timed out")
        return {"status": "error", "message": "Request timed out"}
        
    except requests.exceptions.ConnectionError:
        print(f"\n🔌 [CONNECTION ERROR] Could not connect to CRM")
        return {"status": "error", "message": "Connection error"}
        
    except Exception as e:
        print(f"\n⚠️ [EXCEPTION] {str(e)}")
        return {"status": "error", "message": str(e)}