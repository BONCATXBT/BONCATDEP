# src/auth.py
import os
import aiohttp
import asyncio
from datetime import datetime, timedelta

# Global variables for tokens and expiry
AXIOM_AUTH_REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyZWZyZXNoVG9rZW5JZCI6ImViNTJlYjBmLWE2MDUtNGE1Zi1hMmVjLWI3ZTJkMzE3OWU0OSIsImlhdCI6MTczOTYzNjg3MH0.6vEdpftuKGimEPdKlqOgop4IoEVADDXAeJw7ZY7pE-Q"
AXIOM_AUTH_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoZW50aWNhdGVkVXNlcklkIjoiMWY2NTY0YTktZDkxZC00ZWY5LWExMDctMWVmYjJlNGQwOWYwIiwiaWF0IjoxNzQ0MzcwMDIwLCJleHAiOjE3NDQzNzA5ODB9.0g6zR19qGlszpkbBxCZEdzRMgqHxTYg-_RkHKRMXxck"
AXIOM_TOKEN_EXPIRY = datetime.utcnow() + timedelta(seconds=900)  # 15-minute expiry

def initialize_tokens(refresh_token: str = None, access_token: str = None):
    global AXIOM_AUTH_REFRESH_TOKEN, AXIOM_AUTH_ACCESS_TOKEN, AXIOM_TOKEN_EXPIRY
    AXIOM_AUTH_REFRESH_TOKEN = refresh_token or AXIOM_AUTH_REFRESH_TOKEN
    AXIOM_AUTH_ACCESS_TOKEN = access_token or AXIOM_AUTH_ACCESS_TOKEN
    AXIOM_TOKEN_EXPIRY = datetime.utcnow() + timedelta(seconds=900)

def get_tokens():
    return AXIOM_AUTH_REFRESH_TOKEN, AXIOM_AUTH_ACCESS_TOKEN

async def refresh_access_token():
    global AXIOM_AUTH_REFRESH_TOKEN, AXIOM_AUTH_ACCESS_TOKEN, AXIOM_TOKEN_EXPIRY
    url = "https://api.axiom.trade/refresh-access-token"
    headers = {
        "accept": "application/json, text/plain, */*",
        "origin": "https://axiom.trade",
        "referer": "https://axiom.trade/",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        ),
        "Cookie": f"auth-refresh-token={AXIOM_AUTH_REFRESH_TOKEN}"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                print(f"[DEBUG] Token refresh response status: {response.status}")
                print(f"[DEBUG] Token refresh response headers: {response.headers}")
                if response.status != 200:
                    print(f"[ERROR] Token refresh failed with status {response.status}")
                    raw_response = await response.text()
                    print(f"[DEBUG] Token refresh raw response: {raw_response[:500]}...")
                    return False
                cookies = response.headers.getall("set-cookie", [])
                new_access_token = None
                new_refresh_token = None
                for cookie in cookies:
                    if "auth-access-token" in cookie:
                        new_access_token = cookie.split("auth-access-token=")[1].split(";")[0]
                    if "auth-refresh-token" in cookie:
                        new_refresh_token = cookie.split("auth-refresh-token=")[1].split(";")[0]
                if not new_access_token:
                    print("[ERROR] No auth-access-token found in refresh response")
                    return False
                AXIOM_AUTH_ACCESS_TOKEN = new_access_token
                if new_refresh_token:
                    AXIOM_AUTH_REFRESH_TOKEN = new_refresh_token
                AXIOM_TOKEN_EXPIRY = datetime.utcnow() + timedelta(seconds=900)
                print("[INFO] Access token refreshed successfully")
                print(f"[DEBUG] New auth-access-token: {AXIOM_AUTH_ACCESS_TOKEN}")
                print(f"[DEBUG] New auth-refresh-token: {AXIOM_AUTH_REFRESH_TOKEN}")
                return True
    except Exception as e:
        print(f"[ERROR] Failed to refresh Axiom Trade access token: {str(e)}")
        return False