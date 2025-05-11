import requests

# Helius RPC API endpoint
url = "https://mainnet.helius-rpc.com/?api-key=b6d9d85c-9541-4db4-956e-67ff03bbf3fb"

# Request payload to get asset data for the token
payload = {
    "jsonrpc": "2.0",
    "id": "test",
    "method": "getAsset",
    "params": {"id": "DFu2WwV8UY4LiZiSxEoL2QELXkCeb9Rawderk1Uxpump"}
}

# Make the API request
response = requests.post(
    url,
    headers={"Content-Type": "application/json"},
    json=payload
)

# Parse the response
data = response.json()

# Check if the request was successful
if "result" in data:
    token_data = data["result"]
    
    # Extract the required fields
    price_per_token = token_data["token_info"]["price_info"]["price_per_token"]
    supply = token_data["token_info"]["supply"]
    name = token_data["content"]["metadata"]["name"]
    symbol = token_data["token_info"]["symbol"]
    
    # Format the data as requested
    formatted_price = f"${price_per_token:.10f}"  # Format price with $ and 10 decimal places
    formatted_supply = f"{int(supply / 1_000_000)}M"  # Convert supply to millions and append 'M'
    
    # Print the formatted data
    print(f"Token Address: DFu2WwV8UY4LiZiSxEoL2QELXkCeb9Rawderk1Uxpump")
    print(f"Price: {formatted_price}")
    print(f"Supply: {formatted_supply}")
    print(f"Name: {name}")
    print(f"Symbol: {symbol}")
else:
    print("Error fetching token data:", data.get("error", "Unknown error"))