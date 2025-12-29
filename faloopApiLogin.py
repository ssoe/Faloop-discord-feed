import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Common headers based on FaloopApiClient.cs
SESSION_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ja",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Microsoft Edge\";v=\"126\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
}

# Step 1: Obtain Session ID and JWT
def getJWTsessionID(session):
    url = "https://faloop.app/api/auth/user/refresh"
    # Update headers for this specific request
    session.headers.update(SESSION_HEADERS)
    session.headers.update({
        "Origin": "https://faloop.app",
        "Referer": "https://faloop.app/"
    })
    
    data = {"sessionId": None}
    response = session.post(url, json=data)
    

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error Refreshing Session: Status {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception(f"Failed to get session and JWT: {response.status_code}")

# Step 2: Use the Session ID and JWT to Login
def login(session, session_id, jwt_token, username, password):
    url = "https://faloop.app/api/auth/user/login"
    
    # Update headers for login
    session.headers.update({
        "Origin": "https://faloop.app",
        "Referer": "https://faloop.app/login",
        "Authorization": jwt_token
    })
    
    data = {
        "sessionId": session_id,
        "username": username,
        "password": password,
        "rememberMe": False
    }
    response = session.post(url, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error Logging In: Status {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception(f"Login failed: {response.status_code}")


username = os.getenv('FALOOP_USERNAME')
password = os.getenv('FALOOP_PASSWORD')

if not username or not password:
    print("Error: FALOOP_USERNAME or FALOOP_PASSWORD not found in environment variables.")
else:
    try:
        with requests.Session() as session:
            # Get the session ID and JWT
            responseJWTsessionID = getJWTsessionID(session)
            
            # The API returns {"success": true, "data": {...}}
            response_data = responseJWTsessionID.get("data", {})
            
            session_id = response_data.get("sessionId")
            jwt_token = response_data.get("token")
            
            if not session_id or not jwt_token:
               print("Error: Could not retrieve session ID or token from refresh response.")
               print(f"Full response: {responseJWTsessionID}")
            else:
               # Login using the session ID and JWT
               login_response = login(session, session_id, jwt_token, username, password)
               print("Login successful:", login_response)
    except Exception as e:
        print(f"Exception main: {e}")
