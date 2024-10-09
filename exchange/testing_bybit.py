import requests
import time
import hashlib
import hmac
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
api_key=os.getenv("BYBIT_TESTNET_API_KEY")
secret_key=os.getenv("BYBIT_TESTNET_API_SECRET")
httpClient=requests.Session()
recv_window=str(5000)
url="https://api-testnet.bybit.com" # Testnet endpoint

def HTTP_Request(endPoint, method, payload, Info):
    # Create a timestamp
    time_stamp = str(int(time.time() * 10 ** 3))
    # Generate the signature using the timestamp
    signature = genSignature(payload, time_stamp)
    
    # Define request headers
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    
    # Make the API request
    if method == "POST":
        response = httpClient.request(method, url + endPoint, headers=headers, data=payload)
    else:
        response = httpClient.request(method, url + endPoint + "?" + payload, headers=headers)
    
    # Print the response details
    print(response.text)
    print(response.headers)
    print(Info + " Elapsed Time : " + str(response.elapsed))

def genSignature(payload, time_stamp):
    # Prepare the string for hashing
    param_str = str(time_stamp) + api_key + recv_window + payload
    
    # Generate HMAC SHA256 signature
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    
    return signature

# # Create Order
endpoint = "/v5/order/create"
method = "POST"
orderLinkId = uuid.uuid4().hex
params = '{"category":"linear","symbol": "BTCUSDT","side": "Buy","positionIdx": 0,"orderType": "Market","qty": "0.02","timeInForce": "GTC","orderLinkId": "' + orderLinkId + '"}'
HTTP_Request(endpoint, method, params, "Create")

# Get Order Book
endpoint = "/v5/market/orderbook"
method = "GET"
params = "category=spot&symbol=BTCUSDT&limit=20"
HTTP_Request(endpoint, method, params, "Orderbook")

# Get Price
endpoint = "/v5/market/tickers"
method = "GET"
params = "category=spot&symbol=BTCUSDT"
HTTP_Request(endpoint, method, params, "Price")
