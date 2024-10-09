import os
import time
import hashlib
import hmac
import requests
import logging
import uuid
from dotenv import load_dotenv

class BybitClient:
    def __init__(self, testnet=True):
        """
        Initialize the Bybit Client using API key and secret from environment variables.
        If `testnet=True`, it will use the Bybit Testnet endpoint.
        """
        load_dotenv()  # Load environment variables from the .env file
        self.api_key = os.getenv("BYBIT_TESTNET_API_KEY")
        self.api_secret = os.getenv("BYBIT_TESTNET_API_SECRET")

        if not self.api_key:
            raise ValueError("API key must be set in the .env file")
        
        if not self.api_secret:
            raise ValueError("Secret key password must be set in the .env file")
        
        # Set the appropriate base URL depending on whether it's testnet or mainnet
        if testnet:
            self.BASE_URL = "https://api-testnet.bybit.com"
        else:
            self.BASE_URL = "https://api.bybit.com"
        
        self.recv_window = str(5000)

    def _generate_signature(self, params, timestamp):      
        """
        Generate HMAC SHA256 signature for the parameters.
        """
        param_str = str(timestamp) + self.api_key + self.recv_window + params
        hash = hmac.new(bytes(self.api_secret, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)

        return hash.hexdigest()
    
    # param_str = str(timestamp) + "test_key" + self.recv_window + params
    # hash = hmac.new(bytes("test_secret", "utf-8"), param_str.encode("utf-8"), hashlib.sha256)

    def _send_request(self, method, endpoint, params=None, signed=False):
        """
        Send HTTP request to the Bybit API.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            'X-BAPI-API-KEY': self.api_key,
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-RECV-WINDOW': self.recv_window,
            'Content-Type': 'application/json'
        }

        if signed:
            timestamp = str(int(time.time() * 10 ** 3))
            signature = self._generate_signature(params, timestamp)
            headers.update({
                'X-BAPI-SIGN': signature,
                'X-BAPI-TIMESTAMP': timestamp
            })

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=params)

            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except requests.exceptions.Timeout as e:
            logging.error("Request timed out for _send_request function")
            raise
        except requests.exceptions.ConnectionError:
            logging.error("Network connection error for _send_request function")
            raise
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTPError: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(e)
            logging.error(f"Error in request: {e}")
            raise

    def get_price(self, symbol):
        """
        Get the current market price of the specified symbol.
        """
        endpoint = "/v5/market/tickers"
        params = f"category=spot&symbol={symbol}"
        try:
            data = self._send_request('GET', endpoint, params=params)
            return data
        except Exception as e:
            logging.error(f"Error fetching price: {e}")
            raise

    def place_order(self, symbol, side, qty):
        """
        Place a market order (buy/sell) for the specified symbol and quantity.
        """
        endpoint = "/v5/order/create"
        orderLinkId = uuid.uuid4().hex
        params = f'{{"category":"linear","symbol": "{symbol}","side": "{side}","positionIdx": 0,"orderType": "Market","qty": "{qty}","timeInForce": "GTC","orderLinkId": "{orderLinkId}"}}'
        
        try:
            order = self._send_request('POST', endpoint, params=params, signed=True)
            logging.info(f"Order placed successfully: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            raise


# Example usage:
if __name__ == "__main__":
    bybit_client = BybitClient(testnet=True)  # Set testnet=True to use testnet

    # Get the current price of BTC/USDT
    price = bybit_client.get_price('BTCUSDT')
    print(f"Current BTC/USDT price: {price}")

    # Place a market buy order for 0.02 BTC
    order = bybit_client.place_order('BTCUSDT', 'Sell', 0.01)
    print(f"Order details: {order}")
