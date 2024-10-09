import os
import time
import base64
import requests
import logging
from dotenv import load_dotenv
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes



class BinanceClient:
    def __init__(self, testnet=True):
        """
        Initialize the Binance Client using API key and private key from environment variables.
        If `testnet=True`, it will use the Binance Testnet endpoint.
        """
        load_dotenv()  # Load environment variables from the .env file
        self.api_key = os.getenv("BINANCE_TESTNET_API_KEY")
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.private_key_path = os.path.join(base_path, 'test-prv-key.pem')

       
        self.original_private_key_password= os.getenv("BINANCE_TESTNET_KEY_PASSWORD")
        if self.original_private_key_password is not None:
            self.private_key_password = self.original_private_key_password.encode('utf-8')
        
        if not self.api_key:
            raise ValueError("API key must be set in the .env file")
        
        if not self.original_private_key_password:
            raise ValueError("Private key password must be set in the .env file")

        # Load the private key (assuming it's not password-protected)
        try:
            # Load the private key (assuming it's not password-protected)
            with open(self.private_key_path, 'rb') as f:
                self.private_key = load_pem_private_key(data=f.read(), password=self.private_key_password)
        except FileNotFoundError:
            raise ValueError(f"Private key file not found at {self.private_key_path}")
        except Exception as e:
            raise ValueError(f"Error loading private key: {e}")

        # Set the appropriate base URL depending on whether it's testnet or mainnet
        if testnet:
            self.BASE_URL = "https://testnet.binance.vision"
        else:
            self.BASE_URL = "https://api.binance.com"

    def _sign_request(self, params):
        """
        Sign the request using the private key and return the base64-encoded signature.
        """
        try:
            # Create the payload string to be signed
            payload = '&'.join([f'{param}={value}' for param, value in params.items()])

            # Sign the request using the private key with PKCS1v15 padding and SHA256 hashing algorithm
            signature = self.private_key.sign(
                payload.encode('ASCII'),
                padding.PKCS1v15(),  # Use padding.PSS() if required by the API
                hashes.SHA256()
            )

            # Base64 encode the signature and return it
            return base64.b64encode(signature).decode()
        except Exception as e:
            logging.error(f"Error signing request for _sign_request function : {e}")
            raise
            

    def _send_request(self, method, endpoint, params=None):
        """
        Send HTTP request to the Binance API.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, data=params)
            elif method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except requests.exceptions.Timeout:
            logging.error("Request timed out for _send_request function")
            raise
        except requests.exceptions.ConnectionError:
            logging.error("Network connection error for _send_request function")
            raise
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTPError for _send_request function: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logging.error(f"Error in request for _send_request function: {e}")
            raise

    def place_order(self, symbol, side, quantity):
        """
        Place a market or limit order (buy/sell) for the specified symbol and quantity.
        """
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': "MARKET",
            'quantity': quantity,
            'timestamp': int(time.time() * 1000)  # UNIX timestamp in milliseconds
        }

        # Sign the request
        try:
            params['signature'] = self._sign_request(params)
        except Exception as e:
            logging.error(f"Error signing order request for place_order function: {e}")
            raise

        try:
            order = self._send_request('POST', endpoint, params=params)
            logging.info(f"Order placed successfully for place_order function: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing order for place_order function: {e}")
            raise

    def get_btcusdt_price(self):
        """
        Get the current market price of the BTC/USDT pair.
        """
        endpoint = "/api/v3/ticker/price"
        params = {'symbol': 'BTCUSDT'}
        try:
            data = self._send_request('GET', endpoint, params)
            return float(data['price'])
        except Exception as e:
            logging.error(f"Error fetching BTC/USDT price: {e}")
            raise


# Example usage:
if __name__ == "__main__":
    binance_client = BinanceClient(testnet=True) 

    # Get the current BTC/USDT price
    btcusdt_price = binance_client.get_btcusdt_price()
    print(f"Current BTC/USDT price: {btcusdt_price}")

    # Place a market buy order for 0.003 BTC
    order = binance_client.place_order('BTCUSDT', 'SELL', 0.2)
    print(f"Order details: {order}")
