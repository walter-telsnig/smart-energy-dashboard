import requests
import sys

API_URL = "http://localhost:8000/api/v1/accounts/"

def create_user(email, password, full_name):
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        print(f"✅ User created successfully: {response.json()}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print(f"⚠️ User already exists: {email}")
        else:
            print(f"❌ Error creating user: {e.response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_user.py <email> <password> [full_name]")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Test User"
    
    create_user(email, password, full_name)
