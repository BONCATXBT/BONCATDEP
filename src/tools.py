# tools.py
import json
import aiohttp
import asyncio
from typing import Dict, Any

try:
    from src.auth import get_tokens, refresh_access_token
except ImportError as e:
    print(f"[ERROR] Failed to import auth module: {e}")
    raise

# Helius API key
HELIUS_API_KEY = "b6d9d85c-9541-4db4-956e-67ff03bbf3fb"

async def fetch_helius_data(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.json()

async def fetch_axiom_token_details(token_address: str) -> Dict[str, Any]:
    refresh_token, access_token = get_tokens()
    url = "https://api2.axiom.trade/meme-trending?timePeriod=1h"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://axiom.trade",
        "referer": "https://axiom.trade/",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        ),
        "Cookie": (
            f"auth-refresh-token={refresh_token}; "
            f"auth-access-token={access_token}"
        )
    }
    max_retries = 2
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    print(f"[DEBUG] Axiom Trade API response status: {response.status}")
                    print(f"[DEBUG] Axiom Trade API response headers: {response.headers}")
                    if response.status in (401, 434, 403):
                        print(f"[INFO] Received {response.status}, attempting token refresh...")
                        if await refresh_access_token():
                            refresh_token, access_token = get_tokens()
                            headers["Cookie"] = (
                                f"auth-refresh-token={refresh_token}; "
                                f"auth-access-token={access_token}"
                            )
                            continue
                        else:
                            print("[ERROR] Token refresh failed, cannot fetch Axiom data")
                            return None
                    if response.status != 200:
                        print(f"[ERROR] Axiom Trade API returned status {response.status}")
                        raw_response = await response.text()
                        print(f"[DEBUG] Axiom Trade API raw response: {raw_response[:500]}...")
                        return None
                    # Manually parse the response text as JSON
                    raw_response = await response.text()
                    try:
                        data = json.loads(raw_response)
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Failed to manually parse response as JSON: {str(e)}")
                        print(f"[DEBUG] Axiom Trade API raw response: {raw_response[:500]}...")
                        if attempt < max_retries - 1:
                            print("[INFO] Attempting token refresh due to JSON parsing failure...")
                            if await refresh_access_token():
                                refresh_token, access_token = get_tokens()
                                headers["Cookie"] = (
                                    f"auth-refresh-token={refresh_token}; "
                                    f"auth-access-token={access_token}"
                                )
                                continue
                        return None
                    token_data = next(
                        (item for item in data if item["tokenAddress"] == token_address),
                        None
                    )
                    return token_data
        except Exception as e:
            print(f"[ERROR] Error fetching Axiom token details: {str(e)}")
            if attempt < max_retries - 1:
                print("[INFO] Attempting token refresh due to exception...")
                if await refresh_access_token():
                    refresh_token, access_token = get_tokens()
                    headers["Cookie"] = (
                        f"auth-refresh-token={refresh_token}; "
                        f"auth-access-token={access_token}"
                    )
                    continue
            return None
    print("[ERROR] Max retries reached, failed to fetch Axiom token details")
    return None

async def get_token_details(token_address: str) -> Dict[str, Any]:
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    
    asset_payload = {
        "jsonrpc": "2.0",
        "id": "get-asset",
        "method": "getAsset",
        "params": {"id": token_address}
    }
    asset_response = await fetch_helius_data(url, asset_payload)
    asset_data = asset_response.get("result", {})

    holders_payload = {
        "jsonrpc": "2.0",
        "id": "get-holders",
        "method": "getTokenLargestAccounts",
        "params": [token_address]
    }
    holders_response = await fetch_helius_data(url, holders_payload)
    holders_data = holders_response.get("result", {})

    axiom_data = await fetch_axiom_token_details(token_address)

    if not asset_data or not holders_data:
        if axiom_data:
            return {
                "token_address": token_address,
                "name": axiom_data.get("tokenName", "UNKNOWN"),
                "symbol": axiom_data.get("tokenTicker", "UNKNOWN"),
                "description": "N/A",
                "holders": 0,
                "total_supply": axiom_data.get("supply", 0),
                "top_holders_percentage": axiom_data.get("top10Holders", 0),
                "tokenImage": axiom_data.get("tokenImage", ""),
                "marketCapSol": axiom_data.get("marketCapSol", 0),
                "marketCapPercentChange": axiom_data.get("marketCapPercentChange", 0),
                "liquiditySol": axiom_data.get("liquiditySol", 0),
                "liquidityToken": axiom_data.get("liquidityToken", 0),
                "volumeSol": axiom_data.get("volumeSol", 0),
                "buyCount": axiom_data.get("buyCount", 0),
                "sellCount": axiom_data.get("sellCount", 0),
                "website": axiom_data.get("website", ""),
                "twitter": axiom_data.get("twitter", ""),
                "telegram": axiom_data.get("telegram", ""),
                "discord": axiom_data.get("discord", "")
            }
        return {
            "token_address": token_address,
            "name": "UNKNOWN",
            "symbol": "UNKNOWN",
            "description": "N/A",
            "holders": 0,
            "total_supply": 0,
            "top_holders_percentage": 0,
            "error": "Failed to fetch token details from Helius API"
        }

    top_holders = holders_data.get("value", [])[:5]
    total_supply = asset_data.get("token_info", {}).get("supply", 0)
    top_holders_amount = sum(holder.get("uiAmount", 0) for holder in top_holders)
    decimals = asset_data.get("token_info", {}).get("decimals", 0)
    top_holders_percentage = (top_holders_amount / (total_supply / (10 ** decimals))) * 100 if total_supply else 0

    result = {
        "token_address": token_address,
        "name": asset_data.get("content", {}).get("metadata", {}).get("name", "UNKNOWN"),
        "symbol": asset_data.get("content", {}).get("metadata", {}).get("symbol", "UNKNOWN"),
        "description": asset_data.get("content", {}).get("metadata", {}).get("description", "N/A"),
        "holders": len(holders_data.get("value", [])),
        "total_supply": total_supply / (10 ** decimals) if total_supply else 0,
        "top_holders_percentage": round(top_holders_percentage, 2)
    }

    if result["name"] == "UNKNOWN" and axiom_data:
        result["name"] = axiom_data.get("tokenName", "UNKNOWN")
    if result["symbol"] == "UNKNOWN" and axiom_data:
        result["symbol"] = axiom_data.get("tokenTicker", "UNKNOWN")

    if axiom_data:
        result.update({
            "tokenImage": axiom_data.get("tokenImage", ""),
            "marketCapSol": axiom_data.get("marketCapSol", 0),
            "marketCapPercentChange": axiom_data.get("marketCapPercentChange", 0),
            "liquiditySol": axiom_data.get("liquiditySol", 0),
            "liquidityToken": axiom_data.get("liquidityToken", 0),
            "volumeSol": axiom_data.get("volumeSol", 0),
            "buyCount": axiom_data.get("buyCount", 0),
            "sellCount": axiom_data.get("sellCount", 0),
            "website": axiom_data.get("website", ""),
            "twitter": axiom_data.get("twitter", ""),
            "telegram": axiom_data.get("telegram", ""),
            "discord": axiom_data.get("discord", "")
        })
        if result["total_supply"] == 0:
            result["total_supply"] = axiom_data.get("supply", 0)
        if result["top_holders_percentage"] == 0:
            result["top_holders_percentage"] = axiom_data.get("top10Holders", 0)

    return result

async def get_chart_data(token_address: str) -> Dict[str, Any]:
    return {"token_address": token_address, "prices": []}

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_token_details",
            "description": (
                "Fetches detailed information about a Solana token, including name, symbol, description, "
                "holder count, total supply, top holders percentage, market cap, liquidity, volume, "
                "buy/sell counts, LP burned percentage, and social media links."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "token_address": {
                        "type": "string",
                        "description": "The address of the Solana token to fetch details for."
                    }
                },
                "required": ["token_address"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_chart_data",
            "description": "Fetches chart data for a Solana token, such as price history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "token_address": {
                        "type": "string",
                        "description": "The address of the Solana token to fetch chart data for."
                    }
                },
                "required": ["token_address"]
            }
        }
    }
]

tools_map = {
    "get_token_details": get_token_details,
    "get_chart_data": get_chart_data
}