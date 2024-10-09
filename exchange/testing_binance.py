import base64
import requests
import time
import os
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

# Set up authentication:
API_KEY = "hi8gnnVOSRHt8I1e2LLbS1AzKEGrkNWOCjnZFlBHNW0oO6mfA1cObNOm7RbrzKT8"
PRIVATE_KEY_PATH="test-prv-key.pem"

self.api_key = os.getenv("BINANCE_TESTNET_API_KEY")
self.api_secret = os.getenv("BINANCE_TESTNET_API_SECRET")

# Set up the request:
API_METHOD = "POST"
API_CALL = "api/v3/order"
API_PARAMS = "symbol=BTCUSDT&side=SELL&type=LIMIT&timeInForce=GTC&quantity=1&price=0.2"

# Load the private key (assuming it's not password-protected)
with open(PRIVATE_KEY_PATH, 'rb') as f:
    private_key = load_pem_private_key(data=f.read(), password=None)

# Set up the request parameters
params = {
    'symbol':       'BTCUSDT',
    'side':         'BUY',
    'type':         'MARKET',
    'quantity':     '0.003',
}

# Timestamp the request
timestamp = int(time.time() * 1000)  # UNIX timestamp in milliseconds
params['timestamp'] = timestamp

# Create the payload string to be signed
payload = '&'.join([f'{param}={value}' for param, value in params.items()])

# Sign the request using the private key with padding and hashing algorithm
signature = private_key.sign(
    payload.encode('ASCII'),
    padding.PKCS1v15(),  # or use padding.PSS() if required by the API
    hashes.SHA256()
)

# Base64 encode the signature
signature_b64 = base64.b64encode(signature).decode()

# Add the signature to the request parameters
params['signature'] = signature_b64

# Send the request
headers = {
    'X-MBX-APIKEY': API_KEY,
}

response = requests.post(
    'https://testnet.binance.vision/api/v3/order',
    headers=headers,
    data=params
)

# Print the response
print(response.status_code)
print(response.json())