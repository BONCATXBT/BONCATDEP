import httpx
from openai import OpenAI
from config.config import XAI_API_KEY

# Create a custom HTTP client without proxies
custom_client = httpx.Client()

client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
    http_client=custom_client
)

def send_request(messages, tools):
    return client.chat.completions.create(
        model="grok-3",
        messages=messages,
        tools=tools,
        stream=False,
        temperature=0,
    )