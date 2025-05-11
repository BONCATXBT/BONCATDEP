# chat_terminal.py
import sys
import os
import json
import time
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
import aiohttp
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.api_client import send_request
    from src.tools import tools_definition, tools_map
    from src.utils import predict_trend
    from src.auth import initialize_tokens, refresh_access_token, get_tokens
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure you have added an '__init__.py' file in the 'src' directory.")
    sys.exit(1)

app = FastAPI(title="Solana Blockchain Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://boncatxbt.fun/"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

initialize_tokens()

async def auto_refresh_token():
    from src.auth import AXIOM_TOKEN_EXPIRY
    while True:
        if not AXIOM_TOKEN_EXPIRY:
            AXIOM_TOKEN_EXPIRY = datetime.utcnow() + timedelta(seconds=900)
        time_to_expiry = (AXIOM_TOKEN_EXPIRY - datetime.utcnow()).total_seconds()
        if time_to_expiry <= 60:
            print("[INFO] Access token nearing expiry, refreshing...")
            await refresh_access_token()
        await asyncio.sleep(30)

async def fetch_axiom_trade_data(token_address):
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
                        (token for token in data if token["tokenAddress"] == token_address),
                        None
                    )
                    if not token_data:
                        print(f"[INFO] Token {token_address} not found in Axiom Trade API response")
                    return token_data
        except Exception as e:
            print(f"[ERROR] Error fetching Axiom Trade data: {str(e)}")
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
    print("[ERROR] Max retries reached, failed to fetch Axiom Trade data")
    return None

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(request: ChatRequest):
    messages = [
        {
            "role": "system",
            "content": (
                "You are boncat, a Solana Blockchain Analyzer. Provide detailed, insightful, and user-friendly answers about Solana tokens and blockchain concepts. "
                "When a tool call returns data, first summarize the token details in a clear format with headers:\n"
                "- Token Summary\n"
                "- Name: <name>\n"
                "- Symbol: <symbol>\n"
                "- Description: <description>\n"
                "- Top 20 Holders: <holders>\n"
                "- Total Supply: <total_supply>\n"
                "- Top Holders Percentage: <top_holders_percentage>%\n"
                "- Market Cap: <marketCapSol> SOL\n"
                "- Market Cap Change (1h): <marketCapPercentChange>%\n"
                "- Liquidity (SOL): <liquiditySol>\n"
                "- Liquidity (Token): <liquidityToken>\n"
                "- Volume (1h): <volumeSol> SOL\n"
                "- Buy Count (1h): <buyCount>\n"
                "- Sell Count (1h): <sellCount>\n"
                "- Social Media Links: <website>, <twitter>, <telegram>, <discord>\n"
                "Then, provide a concise commentary under the following headers, keeping each section to 1-2 short sentences. Do not use ** markers, and do not repeat data already provided in the Token Summary (e.g., Top 20 Holders, Total Supply, Market Cap, etc.). Use plain text for headers and make them bold in the UI:\n"
                "- Centralization Risk: Comment on top holders percentage.\n"
                "- Project Vision: Insights from description and social media.\n"
                "- Market Dynamics: Analyze market cap, change, liquidity, and volume.\n"
                "- Trading Activity: Comment on buy/sell counts.\n"
                "- Community Engagement: Suggest checking social media for activity.\n"
                "- Key Observations: Note trends, risks, or unique aspects.\n"
                "- Price Prediction: Provide a short-term price prediction based on market dynamics and trading activity.\n"
                "If the token is not found in the Axiom Trade API response, include a note:\n"
                "- Note: Market data unavailable as this token is not trending in the last 1 hour per Axiom Trade API.\n"
                "If errors are present in the tool output, explain them clearly and provide possible reasons for the failure. "
                "Be concise and professional, focusing on actionable insights without asking follow-up questions."
            )
        },
        {"role": "user", "content": request.message}
    ]
    print(f"[DEBUG] User message: {request.message}")

    try:
        start_time = time.time()
        print("[DEBUG] Sending initial message to boncat...")
        response = send_request(messages, tools_definition)
        print(f"[DEBUG] Initial boncat call took {time.time() - start_time:.2f} seconds")
        print(f"[DEBUG] Raw response: {response}")

        assistant_message = response.choices[0].message
        print(f"[DEBUG] Initial response received: {assistant_message.content}")
        messages.append({"role": assistant_message.role, "content": assistant_message.content})

        token_details = None
        axiom_data = None

        if hasattr(assistant_message, "tool_calls") and assistant_message.tool_calls:
            tool_outputs = []
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                try:
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"Executing {function_name} with args: {function_args}")
                    start_tool_time = time.time()
                    result = await tools_map[function_name](**function_args)
                    print(f"[DEBUG] Tool {function_name} took {time.time() - start_tool_time:.2f} seconds")
                    print(f"Tool {function_name} result: {result}")

                    if function_name == "get_token_details":
                        token_details = result
                        token_address = function_args.get("token_address")
                        axiom_data = await fetch_axiom_trade_data(token_address)
                        if axiom_data:
                            token_details.update({
                                "description": token_details.get("description", "N/A"),
                                "tokenImage": axiom_data.get("tokenImage", token_details.get("tokenImage", "")),
                                "marketCapSol": axiom_data.get("marketCapSol", token_details.get("marketCapSol", 0)),
                                "marketCapPercentChange": axiom_data.get("marketCapPercentChange", token_details.get("marketCapPercentChange", 0)),
                                "liquiditySol": axiom_data.get("liquiditySol", token_details.get("liquiditySol", 0)),
                                "liquidityToken": axiom_data.get("liquidityToken", token_details.get("liquidityToken", 0)),
                                "volumeSol": axiom_data.get("volumeSol", token_details.get("volumeSol", 0)),
                                "buyCount": axiom_data.get("buyCount", token_details.get("buyCount", 0)),
                                "sellCount": axiom_data.get("sellCount", token_details.get("sellCount", 0)),
                                "website": axiom_data.get("website", token_details.get("website", "")),
                                "twitter": axiom_data.get("twitter", token_details.get("twitter", "")),
                                "telegram": axiom_data.get("telegram", token_details.get("telegram", "")),
                                "discord": axiom_data.get("discord", token_details.get("discord", ""))
                            })
                            if token_details.get("total_supply", 0) == 0:
                                token_details["total_supply"] = axiom_data.get("supply", 0)
                            if token_details.get("top_holders_percentage", 0) == 0:
                                token_details["top_holders_percentage"] = axiom_data.get("top10Holders", 0)

                    tool_outputs.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call.id
                    })

                except Exception as e:
                    print(f"Error executing tool {function_name}: {e}")
                    tool_outputs.append({
                        "role": "tool",
                        "content": json.dumps({"error": str(e)}),
                        "tool_call_id": tool_call.id
                    })

            messages.extend(tool_outputs)
            try:
                print("[DEBUG] Sending tool outputs back to boncat...")
                start_final_time = time.time()
                response = send_request(messages, tools_definition)
                print(f"[DEBUG] Final boncat call took {time.time() - start_final_time:.2f} seconds")
                final_message = response.choices[0].message.content
                if not final_message:
                    raise ValueError("boncat returned an empty response after tool call")
                final_content = final_message
            except Exception as e:
                print(f"Error getting final response from boncat: {e}")
                result = json.loads(tool_outputs[0]["content"])
                if "error" in result:
                    final_content = (
                        f"Unable to fetch details for token {result['token_address']} on Solana due to an API error: {result['error']}. "
                        f"This could be due to an issue with the Helius API or the token address being invalid. "
                        f"Default values: Name: {result['name']} ({result['symbol']}), {result['holders']} holders, "
                        f"total supply of {result['total_supply']}, top holders percentage: {result['top_holders_percentage']}%. "
                        "Please verify the token address and try again."
                    )
                else:
                    final_content = (
                        f"The token {result['token_address']} on Solana, named {result['name']} ({result['symbol']}), has {result['holders']} holders "
                        f"and a total supply of {result['total_supply']}. The top holders control {result['top_holders_percentage']}% of the supply. "
                        f"Description: {result['description']}"
                    )
        else:
            final_content = assistant_message.content

        return {"response": final_content, "tokenDetails": token_details}

    except Exception as e:
        print(f"[FATAL] Unexpected error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_refresh_token())
    print("[INFO] Performing initial token refresh on startup...")
    await refresh_access_token()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)