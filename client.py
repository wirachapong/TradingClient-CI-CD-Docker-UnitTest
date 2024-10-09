import logging
from exchange.binance_client import BinanceClient
from exchange.bybit_client import BybitClient

class TradingClient:
    def __init__(self, testnet=True):
        """
        Initialize the trading client that connects to Binance and Bybit.
        """
        self.binance_client = BinanceClient(testnet=testnet)
        self.bybit_client = BybitClient(testnet=testnet)
        logging.basicConfig(level=logging.INFO)

    def get_best_price(self, symbol='BTCUSDT', price_type='lowest'):
        """
        Get the best price (either 'lowest' or 'highest') for BTC/USDT from both exchanges.
        
        :param symbol: The trading symbol (default is BTC/USDT).
        :param price_type: Either 'lowest' for the best buying price or 'highest' for the best selling price.
        :return: A tuple of the best price and the best exchange.
        """
        try:
            # Get the Binance price as a float
            binance_price = float(self.binance_client.get_btcusdt_price())
            
            # Attempt to retrieve and convert Bybit price
            bybit_price_data = self.bybit_client.get_price(symbol)
            bybit_price = (
                float(bybit_price_data['result']['list'][0]['lastPrice'])
                if 'result' in bybit_price_data and bybit_price_data['result']['list'][0]['lastPrice'] is not None
                else None
            )
            
            # Determine the best price based on price_type
            if price_type == 'lowest':
                best_price, best_exchange = min(
                    (price, name) for price, name in [(binance_price, 'Binance'), (bybit_price, 'Bybit')] if price is not None
                )
            elif price_type == 'highest':
                best_price, best_exchange = max(
                    (price, name) for price, name in [(binance_price, 'Binance'), (bybit_price, 'Bybit')] if price is not None
                )
            else:
                raise ValueError("Invalid price_type. Use 'lowest' or 'highest'.")
            
            return best_price, best_exchange

        except Exception as e:
            logging.error(f"Error fetching prices: {e}")
            raise

    def place_order(self, side, quantity, symbol='BTCUSDT', exchange=None):
        """
        Place a market order on the specified exchange.
        :param side: 'Buy' or 'Sell' order side.
        :param quantity: Quantity to buy or sell.
        :param symbol: The trading symbol (default is BTC/USDT).
        :param exchange: The exchange to place the order. If None, it will determine the best exchange.
        :return: The order details.
        """
        try:
            if side not in ['Buy', 'Sell']:
                raise ValueError("Invalid side. Side must be either 'Buy' or 'Sell'.")

            if exchange is None:
                if side.lower() == 'buy':
                    _, exchange = self.get_best_price(symbol, price_type='lowest')
                elif side.lower() == 'sell':
                    _, exchange = self.get_best_price(symbol, price_type='highest')
                else:
                    raise ValueError("Invalid side. Side must be either 'Buy' or 'Sell'.")

            if exchange == 'Binance':
                order = self.binance_client.place_order(symbol, side, quantity)
            elif exchange == 'Bybit':
                order = self.bybit_client.place_order(symbol, side, quantity)
            else:
                raise ValueError("Invalid exchange name. Use 'Binance' or 'Bybit'.")

            logging.info(f"Order placed successfully on {exchange}: {order}")
            return order

        except Exception as e:
            logging.error(f"Error placing order on {exchange}: {e}")
            raise

# Example usage
if __name__ == "__main__":
    trading_client = TradingClient(testnet=True)

    # Get the highest price and best exchange for selling BTC/USDT
    highest_price, highest_price_exchange = trading_client.get_best_price(price_type='highest')
    print(f"Highest price for BTC/USDT is {highest_price} on {highest_price_exchange}")

    # Get the lowest price and best exchange for buying BTC/USDT
    lowest_price, lowest_price_exchange = trading_client.get_best_price(price_type='lowest')
    print(f"Lowest price for BTC/USDT is {lowest_price} on {lowest_price_exchange}")

    # # Place a market order on the best exchange for 0.001 BTC (Has to be "Buy" or "Sell"   (BUY or SELL not accepted))
    # order = trading_client.place_order('Buy', 0.001)
    # print(f"Order placed: {order}")

    # order = trading_client.place_order('Buy', 0.001,exchange='Binance')
    # print(f"Order placed: {order}")

    # order = trading_client.place_order('Buy', 0.001,exchange='Bybit')
    # print(f"Order placed: {order}")

    # order = trading_client.place_order('Sell', 0.001)
    # print(f"Order placed: {order}")

    # order = trading_client.place_order('Sell', 0.001,exchange='Binance')
    # print(f"Order placed: {order}")

    # order = trading_client.place_order('Sell', 0.001,exchange='Bybit')
    # print(f"Order placed: {order}")