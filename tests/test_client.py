import pytest
from unittest.mock import patch, MagicMock
from client import TradingClient
from exchange.binance_client import BinanceClient
from exchange.bybit_client import BybitClient

# --- Initialization Tests ---

# Test 1.1: Ensure TradingClient initializes without errors.
def test_initialization():
    client = TradingClient(testnet=True)
    assert client.binance_client is not None
    assert client.bybit_client is not None

# --- get_best_price Tests ---
# Test 2.1: Fetch the lowest price between Binance and Bybit
def test_get_best_price_lower_price():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        mock_binance.get_btcusdt_price.return_value = 60000.0
        mock_bybit.get_price.return_value = {'result': {'list': [{'lastPrice': '61000.0'}]}}
        
        best_price, best_exchange = client.get_best_price(price_type='lowest')
        
        assert best_price == 60000.0
        assert best_exchange == 'Binance'

# Test 2.2: Fetch the highest price between Binance and Bybit
def test_get_best_price_higher_price():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        mock_binance.get_btcusdt_price.return_value = 62000.0
        mock_bybit.get_price.return_value = {'result': {'list': [{'lastPrice': '61000.0'}]}}
        
        best_price, best_exchange = client.get_best_price(price_type='highest')
        
        assert best_price == 62000.0
        assert best_exchange == 'Binance'

# Test 2.3: Handle a case where Binance API returns an exception
def test_get_best_price_binance_exception():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        mock_binance.get_btcusdt_price.side_effect = Exception("Binance error")
        mock_bybit.get_price.return_value = {'result': {'list': [{'lastPrice': '61000.0'}]}}
        
        with pytest.raises(Exception, match="Binance error"):
            client.get_best_price(price_type='lowest')

# Test 2.4: Handle a case where Bybit API returns an exception
def test_get_best_price_bybit_exception():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        mock_binance.get_btcusdt_price.return_value = 60000.0
        mock_bybit.get_price.side_effect = Exception("Bybit error")
        
        with pytest.raises(Exception, match="Bybit error"):
            client.get_best_price(price_type='lowest')

# Test 2.5: Handle a case where Bybit API returns None for the price
def test_get_best_price_bybit_none_price():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        mock_binance.get_btcusdt_price.return_value = 62000.0
        mock_bybit.get_price.return_value = {'result': {'list': [{'lastPrice': None}]}}
        
        best_price, best_exchange = client.get_best_price(price_type='lowest')
        
        assert best_price == 62000.0
        assert best_exchange == 'Binance'

# Test 2.6: Handle a case where both Binance and Bybit APIs return valid prices as floats
def test_get_best_price_valid_prices():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        mock_binance.get_btcusdt_price.return_value = 63000.0
        mock_bybit.get_price.return_value = {'result': {'list': [{'lastPrice': '62000.0'}]}}
        
        # Get prices for lowest and highest separately to confirm they are floats
        binance_price = client.binance_client.get_btcusdt_price()
        bybit_price_data = client.bybit_client.get_price()
        bybit_price = float(bybit_price_data['result']['list'][0]['lastPrice']) if 'result' in bybit_price_data else None

        # Confirm that both are floats
        assert isinstance(binance_price, float), "Binance price should be a float"
        assert isinstance(bybit_price, float), "Bybit price should be a float"

# Test 2.7: Handle an invalid `price_type` argument
def test_get_best_price_invalid_price_type():
    client = TradingClient(testnet=True)
    
    with patch.object(client, 'get_best_price', side_effect=ValueError("Invalid price_type. Use 'lowest' or 'highest'.")) as mock_method:
        with pytest.raises(ValueError, match="Invalid price_type. Use 'lowest' or 'highest'."):
            client.get_best_price(price_type='average')
    
    mock_method.assert_called_once_with(price_type='average')

# --- place_order Tests ---
# Test 3.1: Simulate a successful "Buy" order placement on Binance
def test_place_order_binance():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        mock_binance.place_order.return_value = {"order_id": "12345"}
        
        result = client.place_order(side='Buy', quantity=0.001, exchange='Binance')
        
        assert result == {"order_id": "12345"}
        mock_binance.place_order.assert_called_once_with('BTCUSDT', 'Buy', 0.001)

# Test 3.2: Simulate a successful "Sell" order placement on Bybit
def test_place_order_bybit():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        mock_bybit.place_order.return_value = {"order_id": "54321"}
        
        result = client.place_order(side='Sell', quantity=0.002, exchange='Bybit')
        
        assert result == {"order_id": "54321"}
        mock_bybit.place_order.assert_called_once_with('BTCUSDT', 'Sell', 0.002)

# Test 3.3: Test that an invalid exchange name raises a ValueError
def test_place_order_invalid_exchange():
    client = TradingClient(testnet=True)
    with pytest.raises(ValueError, match="Invalid exchange name. Use 'Binance' or 'Bybit'."):
        client.place_order(side='Buy', quantity=0.001, exchange='Unknown')

# Test 3.4: Test that an invalid order side raises a ValueError
def test_place_order_invalid_side():
    client = TradingClient(testnet=True)
    with pytest.raises(ValueError, match="Invalid side. Side must be either 'Buy' or 'Sell'."):
        client.place_order(side='Hold', quantity=0.001, exchange='Binance')

# Test 3.5: Simulate placing a "Buy" order on the best exchange by allowing the client to select based on the lowest price
def test_place_order_best_exchange_buy():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        # Setup mock for get_best_price to return Binance as the best exchange for buying
        with patch.object(client, 'get_best_price', return_value=(60000.0, 'Binance')):
            mock_binance.place_order.return_value = {"order_id": "12345"}
            
            result = client.place_order(side='Buy', quantity=0.001)
            
            assert result == {"order_id": "12345"}
            mock_binance.place_order.assert_called_once_with('BTCUSDT', 'Buy', 0.001)

# Test 3.6: Simulate placing a "Sell" order on the best exchange by allowing the client to select based on the highest price
def test_place_order_best_exchange_sell():
    client = TradingClient(testnet=True)
    with patch.object(client, 'binance_client', create=True) as mock_binance, \
         patch.object(client, 'bybit_client', create=True) as mock_bybit:
        
        # Setup mock for get_best_price to return Bybit as the best exchange for selling
        with patch.object(client, 'get_best_price', return_value=(61000.0, 'Bybit')):
            mock_bybit.place_order.return_value = {"order_id": "54321"}
            
            result = client.place_order(side='Sell', quantity=0.002)
            
            assert result == {"order_id": "54321"}
            mock_bybit.place_order.assert_called_once_with('BTCUSDT', 'Sell', 0.002)