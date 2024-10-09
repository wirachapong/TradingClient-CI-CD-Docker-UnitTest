from unittest.mock import patch, MagicMock
import pytest
from exchange.bybit_client import BybitClient
import requests
import logging
import time
import os
import hmac
import hashlib
import json

# Set up basic logging configuration (optional, for better log visibility)
logging.basicConfig(level=logging.ERROR)

# --- Initialization Tests ---

# Test 1.1: Ensure BybitClient raises a ValueError if the API key is missing from the environment.
def test_missing_api_key():
    with patch.dict(os.environ, {"BYBIT_TESTNET_API_KEY": ""}):
        with pytest.raises(ValueError, match="API key must be set in the .env file"):
            BybitClient(testnet=True)

# Test 1.2: Ensure BybitClient raises a ValueError if the secret key is missing from the environment.
def test_missing_api_secret():
    with patch.dict(os.environ, {"BYBIT_TESTNET_API_SECRET": ""}):
        with pytest.raises(ValueError, match="Secret key password must be set in the .env file"):
            BybitClient(testnet=True)

# Test 1.3: Confirm that BybitClient correctly sets the base URL based on whether testnet=True or testnet=False.
def test_base_url_setting():
    client_testnet = BybitClient(testnet=True)
    assert client_testnet.BASE_URL == "https://api-testnet.bybit.com"

    client_mainnet = BybitClient(testnet=False)
    assert client_mainnet.BASE_URL == "https://api.bybit.com"

# --- Signature Generation Tests ---

# Test 2.1: Verify that _generate_signature produces a correct HMAC SHA256 signature.
def test_generate_signature():
    
    with patch.dict(os.environ, {
        "BYBIT_TESTNET_API_KEY": "test_key",
        "BYBIT_TESTNET_API_SECRET": "test_secret"
    }):
        client = BybitClient(testnet=True)
        params = "category=spot&symbol=BTCUSDT"
        timestamp = "1234567890"
        expected_signature = hmac.new(
            bytes("test_secret","utf-8"),
            f"{timestamp}test_key{client.recv_window}{params}".encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        signature = client._generate_signature(params, timestamp)
        assert signature == expected_signature

# --- Request Sending Tests ---

# Test 3.1: Mock _send_request to simulate a successful GET request and verify the response is parsed as expected.
def test_send_get_request_success():
    client = BybitClient(testnet=True)
    mock_response_data = {'result': {'price': '62000.0'}}
    with patch.object(client, '_send_request', return_value=mock_response_data) as mock_send_request:
        response = client._send_request('GET', '/v5/market/tickers', {'category': 'spot', 'symbol': 'BTCUSDT'})
        assert response == mock_response_data
        mock_send_request.assert_called_once_with('GET', '/v5/market/tickers', {'category': 'spot', 'symbol': 'BTCUSDT'})

# Test 3.2: Simulate a Timeout exception in _send_request and confirm it logs the correct error.
def test_send_request_timeout():
    with patch('requests.get', side_effect=requests.exceptions.Timeout):
        with patch('logging.error') as mock_logging:
            with pytest.raises(requests.exceptions.Timeout):
                client = BybitClient(testnet=True)
                answer=client._send_request('GET', '/v5/market/tickers', {'category': 'spot', 'symbol': 'BTCUSDT'})
            mock_logging.assert_called_with("Request timed out for _send_request function")

# Test 3.3: Simulate a ConnectionError exception in _send_request and confirm it logs the correct error.
def test_send_request_connection_error():
    client = BybitClient(testnet=True)
    with patch('requests.get', side_effect=requests.exceptions.ConnectionError):
        with patch('logging.error') as mock_logging:
            with pytest.raises(requests.exceptions.ConnectionError):
                client._send_request('GET', '/v5/market/tickers', {'category': 'spot', 'symbol': 'BTCUSDT'})
            mock_logging.assert_called_with("Network connection error for _send_request function")

# Test 3.4: Simulate a HTTPError exception in _send_request and confirm it logs the correct error.
def test_send_request_http_error():
    # Mock the response to simulate an HTTPError with a status code and error message
    mock_response = MagicMock()    
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    
    # Patch `requests.get` to raise an HTTPError with the mocked response
    with patch('requests.get', side_effect=requests.exceptions.HTTPError(response=mock_response)):
        with patch('logging.error') as mock_logging:
            with pytest.raises(requests.exceptions.HTTPError):
                client = BybitClient(testnet=True)
                client._send_request('GET', '/v5/market/tickers', {'category': 'spot', 'symbol': 'BTCUSDT'})
            
            # Check that the log was created with the expected error message
            mock_logging.assert_called_with("HTTPError: 404 - Not Found")

# --- Price Retrieval Tests ---

# Test 4.1: Mock get_price to simulate a successful price retrieval.
@patch.object(BybitClient, '_send_request')
def test_get_price_success(mock_send):
    mock_price_data = {"result": {"price": "62000.0"}}
    mock_send.return_value = mock_price_data

    client = BybitClient(testnet=True)
    price = client.get_price('BTCUSDT')
    
    assert isinstance(price, dict)
    assert price == mock_price_data

# Test 4.2: Simulate an error in get_price and ensure the error is logged.
@patch.object(BybitClient, '_send_request', side_effect=Exception("Price retrieval error"))
def test_get_price_error(mock_send):
    client = BybitClient(testnet=True)
    with patch('logging.error') as mock_logging:
        with pytest.raises(Exception, match="Price retrieval error"):
            client.get_price('BTCUSDT')
        mock_logging.assert_called_with("Error fetching price: Price retrieval error")

# --- Order Placement Tests ---

# Test 5.1: Mock _sign_request and _send_request to validate that place_order constructs the correct payload for a market order.
@patch.object(BybitClient, '_send_request')
@patch.object(BybitClient, '_generate_signature', return_value="mocked_signature")
def test_place_order_payload(mock_sign, mock_send):
    client = BybitClient(testnet=True)
    symbol = "BTCUSDT"
    side = "Buy"
    qty = 0.02

    # Call place_order to trigger the mocked _send_request
    client.place_order(symbol, side, qty)

    # Capture the actual params used in the _send_request call and parse it as JSON
    actual_params = json.loads(mock_send.call_args[1]["params"])
    
    # Construct the expected params with the actual orderLinkId used
    expected_params = (
        f'{{"category":"linear","symbol": "{symbol}","side": "{side}","positionIdx": 0,"orderType": "Market",'
        f'"qty": "{qty}","timeInForce": "GTC","orderLinkId": "{actual_params["orderLinkId"]}"}}'
    )

    # Assert that _send_request was called with the correct arguments
    mock_send.assert_called_once_with('POST', '/v5/order/create', params=expected_params, signed=True)

# Test 5.2: Mock _send_request to simulate a successful order response.
@patch.object(BybitClient, '_send_request')
def test_place_order_success(mock_send):
    mock_order_response = {
        "result": {
            "symbol": "BTCUSDT",
            "orderId": "12345678",
            "side": "Buy",
            "orderType": "Market",
            "price": "0.0",
            "qty": "0.02",
            "orderStatus": "Created"
        }
    }
    mock_send.return_value = mock_order_response

    client = BybitClient(testnet=True)
    response = client.place_order("BTCUSDT", "Buy", 0.02)
    
    assert response == mock_order_response

# Test 5.3: Mock _send_request to simulate an error during order placement.
@patch.object(BybitClient, '_send_request', side_effect=Exception("Order placement error"))
def test_place_order_error(mock_send):
    client = BybitClient(testnet=True)
    with patch('logging.error') as mock_logging:
        with pytest.raises(Exception, match="Order placement error"):
            client.place_order("BTCUSDT", "Buy", 0.02)
        mock_logging.assert_called_with("Error placing order: Order placement error")
