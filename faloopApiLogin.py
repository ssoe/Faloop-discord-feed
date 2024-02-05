import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
# Step 1: Obtain Session ID and JWT
def getJWTsessionID():
    url = "https://faloop.app/api-v2/auth/user/refresh"
    headers = {
        "Origin": "https://faloop.app",
        "Referer": "https://faloop.app",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
    }
    data = {"sessionId": None}
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get session and JWT: {response.status_code}")

# Step 2: Use the Session ID and JWT to Login
def login(session_id, jwt_token, username, password):
    url = "https://faloop.app/api-v2/auth/user/login"
    headers = {
        "Origin": "https://faloop.app",
        "Referer": "https://faloop.app/login",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Authorization": jwt_token
    }
    data = {
        "sessionId": session_id,
        "username": username,
        "password": password,
        "rememberMe": False
    }
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Login failed: {response.status_code}")


username = os.getenv('FALOOP_USERNAME')
password = os.getenv('FALOOP_PASSWORD')

try:
    # Get the session ID and JWT
    responseJWTsessionID = getJWTsessionID()
    session_id = responseJWTsessionID.get("sessionId")
    jwt_token = responseJWTsessionID.get("token")

    # Login using the session ID and JWT
    login_response = login(session_id, jwt_token, username, password)
    #print("Login successful:", login_response)
except Exception as e:
    print(e)
