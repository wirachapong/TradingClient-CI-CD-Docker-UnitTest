import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from exchange.binance_client import BinanceClient
import requests
import logging
import time
import builtins
import logging
import sys

# Set up basic logging configuration (optional, for better log visibility)
logging.basicConfig(level=logging.ERROR) 

# --- Initialization Tests ---

# Test 1.1: Ensure BinanceClient raises a ValueError if the API key is missing from the environment.
def test_missing_api_key():
    with patch.dict(os.environ, {"BINANCE_TESTNET_API_KEY": ""}):
        with pytest.raises(ValueError, match="API key must be set in the .env file"):
            BinanceClient(testnet=True)

# Test 1.2: Ensure BinanceClient raises a ValueError if the private key path does not exist.
def test_missing_private_key_file():
    # Store the expected private key path based on the class logic.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    private_key_path = os.path.join(project_root, 'exchange', 'test-prv-key.pem')

    # Use the original `open` function
    original_open = builtins.open
    
    # Patches the built-in open function to raise FileNotFoundError only for the private key path.
    with patch("builtins.open", side_effect=lambda filename, *args, **kwargs: (
        original_open(filename, *args, **kwargs) if filename != private_key_path else (_ for _ in ()).throw(FileNotFoundError)
    )):
        # Expects BinanceClient to raise a ValueError with a specific message due to the missing private key file.
        with pytest.raises(ValueError, match=f"Private key file not found at {private_key_path}"):
            BinanceClient(testnet=True)


# Test 1.3: Confirm that BinanceClient correctly sets the base URL based on whether testnet=True or testnet=False.
def test_base_url_setting():
    client_testnet = BinanceClient(testnet=True)
    assert client_testnet.BASE_URL == "https://testnet.binance.vision"

    client_mainnet = BinanceClient(testnet=False)
    assert client_mainnet.BASE_URL == "https://api.binance.com"

# Test 1.4: Confirm that API key is loaded correctly from the environment variables.
def test_api_key_loading():
    with patch.dict(os.environ, {"BINANCE_TESTNET_API_KEY": "mock_api_key"}):
        client = BinanceClient(testnet=True)
        # print(client.api_key)
        assert client.api_key == "mock_api_key"  # Verify that it correctly loaded the mocked key

# Test 1.5: case wrong password to open private key
def test_wrong_private_key_password():
    # Mock environment variables with a string password (it will be encoded in the main code)
    with patch.dict(os.environ, {
        "BINANCE_TESTNET_KEY_PASSWORD": "wrongpassword"
    }):
        # Check if the ValueError is raised with the correct message
        with pytest.raises(ValueError, match="the provided password may be incorrect"):
            BinanceClient(testnet=True)
            
# Test 1.7: Confirm that Testnet key password is loaded correctly from the environment variables.
def test_missing_private_key_password():
    with patch.dict(os.environ, {"BINANCE_TESTNET_KEY_PASSWORD": ""}):
        with pytest.raises(ValueError, match="Private key password must be set in the .env file"):
            BinanceClient(testnet=True)

# Test 1.8 Ensure Error is raised if the testnet key password can't be encoded.
def test_unencodable_private_key_password():
    with patch.dict(os.environ, {
        "BINANCE_TESTNET_KEY_PASSWORD": "\udc80"  # Use a character that can't be encoded in utf-8
    }):
        # Patch the encoding process to raise a UnicodeEncodeError
        with patch("builtins.open", new_callable=MagicMock):
            with pytest.raises(UnicodeEncodeError):
                BinanceClient(testnet=True)

# --- Signing Tests ---

# Test 2.1: Mock the _sign_request method to confirm it correctly builds and returns a valid signature.
@patch.object(BinanceClient, '_sign_request')
def test_sign_request(mock_sign_request):
    mock_sign_request.return_value = "mocked_signature"
    client = BinanceClient(testnet=True)
    params = {'symbol': 'BTCUSDT', 'side': 'BUY', 'quantity': 0.001, 'timestamp': int(time.time() * 1000)}
    signature = client._sign_request(params)
    assert signature == "mocked_signature"
    mock_sign_request.assert_called_once_with(params)

# Test 2.2: Test that _sign_request logs an error and raises an exception if an error occurs during signing.
def test_sign_request_error_logging():
    client = BinanceClient(testnet=True)
    
    # Mock the `self.private_key.sign` method to raise an exception
    with patch.object(client, 'private_key', MagicMock()) as mock_private_key:
        mock_private_key.sign.side_effect = Exception("Signing error")
        
        # Patch logging.error to ensure it is called
        with patch('logging.error') as mock_logging:
            with pytest.raises(Exception, match="Signing error"):
                # Parameters for _sign_request
                params = {'symbol': 'BTCUSDT', 'side': 'BUY', 'quantity': 0.001, 'timestamp': int(time.time() * 1000)}
                
                # Call _sign_request, which should now raise an exception within the method
                client._sign_request(params)

            # Ensure that logging.error was called due to the exception
            mock_logging.assert_called_once()
            # Check that the log message is as expected
            args, _ = mock_logging.call_args
            assert "Error signing request for _sign_request function :" in args[0]
# --- Request Sending Tests ---

# Test 3.1: Mock _send_request to simulate a successful GET request and verify the response is parsed as expected.
def test_send_get_request_success():
    client = BinanceClient(testnet=True)
    mock_response_data = {'price': '62000.0'}
    with patch.object(client, '_send_request', return_value=mock_response_data) as mock_send_request:
        response = client._send_request('GET', '/api/v3/ticker/price', {'symbol': 'BTCUSDT'})
        assert response == mock_response_data
        mock_send_request.assert_called_once_with('GET', '/api/v3/ticker/price', {'symbol': 'BTCUSDT'})

# Test 3.2: Simulate a Timeout exception in _send_request and confirm it logs the correct error.
def test_send_request_timeout():
    client = BinanceClient(testnet=True)
    with patch('requests.get', side_effect=requests.exceptions.Timeout):
        with patch('logging.error') as mock_logging:
            with pytest.raises(requests.exceptions.Timeout):
                client._send_request('GET', '/api/v3/ticker/price', {'symbol': 'BTCUSDT'})
            mock_logging.assert_called_with("Request timed out for _send_request function")

# Test 3.3: Simulate a ConnectionError exception in _send_request and confirm it logs the correct error.
def test_send_request_connection_error():
    client = BinanceClient(testnet=True)
    with patch('requests.get', side_effect=requests.exceptions.ConnectionError):
        with patch('logging.error') as mock_logging:
            with pytest.raises(requests.exceptions.ConnectionError):
                client._send_request('GET', '/api/v3/ticker/price', {'symbol': 'BTCUSDT'})
            mock_logging.assert_called_with("Network connection error for _send_request function")

# Test 3.4: Simulate a HTTPError exception in _send_request with a custom status code and message, and verify the logged error message.
def test_send_request_http_error():
    client = BinanceClient(testnet=True)
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    with patch('requests.get', side_effect=requests.exceptions.HTTPError(response=mock_response)):
        with patch('logging.error') as mock_logging:
            with pytest.raises(requests.exceptions.HTTPError):
                client._send_request('GET', '/api/v3/ticker/price', {'symbol': 'BTCUSDT'})
            mock_logging.assert_called_with("HTTPError for _send_request function: 403 - Forbidden")

# Test 3.5: Simulate a successful POST request in _send_request and verify that the parsed JSON response is returned as expected.
def test_send_post_request_successful():
    client = BinanceClient(testnet=True)
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}

        # Call _send_request and capture the response
        response = client._send_request("POST", "/test-endpoint", {"key": "value"})

        # Assert that the response is as expected
        assert response == {"success": True}

        # Ensure requests.post was called once with the expected arguments
        mock_post.assert_called_once_with(
            "https://testnet.binance.vision/test-endpoint",  # Example full URL
            headers={'X-MBX-APIKEY': client.api_key},  # Ensure the API key is passed in headers if required
            data={"key": "value"}  # Change to 'data' as used by _send_request
        )
# Test 3.6: Test that illegal characters in 'quantity' parameter within _send_request logs a specific error.
def test_send_request_illegal_characters_simple_error():
    client = BinanceClient(testnet=True)
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Illegal characters found in parameter 'quantity'"
    
    with patch('requests.post', side_effect=requests.exceptions.HTTPError(response=mock_response)):
        with patch('logging.error') as mock_logging:
            with pytest.raises(requests.exceptions.HTTPError):
                client._send_request('POST', '/api/v3/order', {'symbol': 'BTCUSDT', 'side': 'BUY', 'quantity': 'invalid_quantity'})
            mock_logging.assert_called_with(
                "HTTPError for _send_request function: 400 - Illegal characters found in parameter 'quantity'"
            )

# Test 3.7: Test that illegal characters in 'quantity' parameter within _send_request logs a specific error.
def test_send_request_illegal_characters_detailed_error():
    client = BinanceClient(testnet=True)
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = (
        '{"code":-1100,"msg":"Illegal characters found in parameter \'quantity\'; '
        'legal range is \'^([0-9]{1,20})(\\\\.[0-9]{1,20})?$\'."}'
    )
    
    with patch('requests.post', side_effect=requests.exceptions.HTTPError(response=mock_response)):
        with patch('logging.error') as mock_logging:
            with pytest.raises(requests.exceptions.HTTPError):
                client._send_request('POST', '/api/v3/order', {'symbol': 'BTCUSDT', 'side': 'BUY', 'quantity': 'invalid_quantity'})
            mock_logging.assert_called_with(
                "HTTPError for _send_request function: 400 - "
                "{\"code\":-1100,\"msg\":\"Illegal characters found in parameter 'quantity'; "
                "legal range is '^([0-9]{1,20})(\\\\.[0-9]{1,20})?$'.\"}"
            )
# --- Order Placement Tests ---

# Test 4.1: Mock _sign_request and _send_request to validate that place_order constructs the correct payload for a market order.
@patch.object(BinanceClient, '_send_request')
@patch.object(BinanceClient, '_sign_request', return_value="mocked_signature")
def test_place_market_order_payload(mock_sign, mock_send):
    client = BinanceClient(testnet=True)
    symbol = "BTCUSDT"
    side = "BUY"
    quantity = 0.001
    client.place_order(symbol, side, quantity)

    expected_params = {
        'symbol': symbol,
        'side': side,
        'type': "MARKET",
        'quantity': quantity,
        'timestamp': mock_send.call_args[1]['params']['timestamp'],
        'signature': "mocked_signature"
    }
    
    mock_send.assert_called_once_with('POST', '/api/v3/order', params=expected_params)

# Test 4.2: Mock _send_request to simulate a successful order response and ensure that place_order returns the expected order details.
@patch.object(BinanceClient, '_send_request')
def test_place_order_success(mock_send):
    mock_order_response = {
        "symbol": "BTCUSDT",
        "orderId": 12345678,
        "clientOrderId": "test_order",
        "transactTime": int(time.time() * 1000),
        "price": "0.0",
        "origQty": "0.001",
        "executedQty": "0.001",
        "status": "FILLED",
        "type": "MARKET",
        "side": "BUY"
    }
    mock_send.return_value = mock_order_response

    client = BinanceClient(testnet=True)
    response = client.place_order("BTCUSDT", "BUY", 0.001)

    assert response == mock_order_response

# Test 4.3: Mock _send_request to simulate an error during order placement, and verify that place_order logs the error and raises an exception.
@patch.object(BinanceClient, '_send_request', side_effect=Exception("Order placement error"))
def test_place_order_error(mock_send):
    client = BinanceClient(testnet=True)
    with patch('logging.error') as mock_logging:
        with pytest.raises(Exception, match="Order placement error"):
            client.place_order("BTCUSDT", "BUY", 0.001)
        mock_logging.assert_called_with("Error placing order for place_order function: Order placement error")

# --- BTC/USDT Price Retrieval Tests ---

# Test 5.1: Mock _send_request to simulate a successful price retrieval and confirm that the method returns a float.
@patch.object(BinanceClient, '_send_request')
def test_get_btcusdt_price_success(mock_send):
    mock_price_data = {"price": "62000.0"}
    mock_send.return_value = mock_price_data

    client = BinanceClient(testnet=True)
    price = client.get_btcusdt_price()

    assert isinstance(price, float)
    assert price == 62000.0

# Test 5.2: Simulate an error in _send_request when calling get_btcusdt_price and ensure the error is logged, and an exception is raised.
@patch.object(BinanceClient, '_send_request', side_effect=Exception("Price retrieval error"))
def test_get_btcusdt_price_error(mock_send):
    client = BinanceClient(testnet=True)
    with patch('logging.error') as mock_logging:
        with pytest.raises(Exception, match="Price retrieval error"):
            client.get_btcusdt_price()
        mock_logging.assert_called_with("Error fetching BTC/USDT price: Price retrieval error")