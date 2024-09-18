import time
import pandas as pd
import logging
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
import requests.exceptions
from dotenv import load_dotenv
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from database_handler import DatabaseHandler

class TradingBot:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Setup logging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Load configuration from .env file
        self.API_KEY = os.getenv('API_KEY')
        self.API_SECRET = os.getenv('API_SECRET')
        self.SYMBOL = os.getenv('SYMBOL')
        self.TRADE_QUANTITY = float(os.getenv('TRADE_QUANTITY'))
        self.SHORT_WINDOW = int(os.getenv('SHORT_WINDOW'))
        self.LONG_WINDOW = int(os.getenv('LONG_WINDOW'))
        self.INTERVAL = os.getenv('INTERVAL')
        self.LOOKBACK = os.getenv('LOOKBACK')

        # Initialisation du gestionnaire de base de données
        self.db_handler = DatabaseHandler()

        # Initialize the Binance client
        self.initialize_client()

        # Trading parameters
        self.logger.info(f"Trading parameters set: SYMBOL={self.SYMBOL}, TRADE_QUANTITY={self.TRADE_QUANTITY}, SHORT_WINDOW={self.SHORT_WINDOW}, LONG_WINDOW={self.LONG_WINDOW}, INTERVAL={self.INTERVAL}, LOOKBACK={self.LOOKBACK}")

    def initialize_client(self):
        try:
            self.client = Client(self.API_KEY, self.API_SECRET)
            self.logger.info("Binance client initialized")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error while initializing Binance client: {e}")
            exit(1)
        except Exception as e:
            self.logger.error(f"Unexpected error while initializing Binance client: {e}")
            exit(1)

    def get_data(self):
        """Fetch historical klines from Binance and return a DataFrame."""
        self.logger.debug(f"Fetching historical klines for {self.SYMBOL}")
        try:
            klines = self.client.get_historical_klines(self.SYMBOL, self.INTERVAL, self.LOOKBACK)
            self.logger.debug(f"Received {len(klines)} klines")
            data = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
            data.set_index('timestamp', inplace=True)
            data = data[['open', 'high', 'low', 'close', 'volume']]
            data = data.astype(float)
            self.logger.debug("Data processing completed")
            return data
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error while fetching data: {e}")
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error while fetching data: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching data: {e}")
        return None

    def calculate_indicators(self, data):
        """Calculate moving averages."""
        self.logger.debug("Calculating indicators")
        try:
            data['ma_short'] = data['close'].rolling(window=self.SHORT_WINDOW).mean()
            data['ma_long'] = data['close'].rolling(window=self.LONG_WINDOW).mean()
            self.logger.debug("Indicators calculated")
            return data
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return None

    def generate_signal(self, data):
        """Generate buy/sell signal based on moving averages."""
        self.logger.debug("Generating trading signal")
        try:
            if data['ma_short'].iloc[-1] > data['ma_long'].iloc[-1]:
                signal = 'BUY'
            elif data['ma_short'].iloc[-1] < data['ma_long'].iloc[-1]:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            self.logger.debug(f"Signal generated: {signal}")
            return signal
        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return None

    def place_order(self, side):
        """Place a market order."""
        self.logger.info(f"Attempting to place {side} order for {self.TRADE_QUANTITY} {self.SYMBOL}")
        try:
            order = self.client.create_order(
                symbol=self.SYMBOL,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=self.TRADE_QUANTITY
            )
            self.logger.info(f"Order placed successfully: {order}")
            return order
        except BinanceAPIException as e:
            self.logger.error(f"API error while placing order: {e}")
        except BinanceOrderException as e:
            self.logger.error(f"Order error: {e}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error while placing order: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while placing order: {e}")
        return None

    def run(self):
        self.logger.info("Starting main trading loop")
        position = None  # Current position: 'LONG', 'SHORT', or None
        try:
            while True:
                try:
                    self.logger.debug("Starting new iteration")
                    # Fetch and prepare data
                    data = self.get_data()
                    if data is None:
                        self.logger.warning("Failed to fetch data, waiting for 60 seconds before retrying")
                        time.sleep(60)
                        continue
                    
                    data = self.calculate_indicators(data)
                    if data is not None:
                        self.db_handler.write_market_data(self.SYMBOL, data)
                    
                    if pd.isnull(data['ma_short'].iloc[-1]) or pd.isnull(data['ma_long'].iloc[-1]):
                        self.logger.warning("Not enough data to compute indicators, waiting for 60 seconds")
                        time.sleep(60)
                        continue

                    # Generate trading signal
                    signal = self.generate_signal(data)
                    if signal is None:
                        self.logger.warning("Failed to generate signal, waiting for 60 seconds before retrying")
                        time.sleep(60)
                        continue
                    
                    self.logger.info(f"Generated signal: {signal}")
                    
                    # Execute trades based on the signal
                    if signal == 'BUY' and position != 'LONG':
                        self.logger.info("Executing BUY order")
                        order = self.place_order(SIDE_BUY)
                        if order:
                            position = 'LONG'
                            self.logger.info("Position changed to LONG")
                    elif signal == 'SELL' and position != 'SHORT':
                        self.logger.info("Executing SELL order")
                        order = self.place_order(SIDE_SELL)
                        if order:
                            position = 'SHORT'
                            self.logger.info("Position changed to SHORT")
                    else:
                        self.logger.info("No action taken, maintaining current position")
                    
                    # Wait before the next iteration
                    self.logger.debug("Waiting for 60 seconds before next iteration")
                    time.sleep(60)
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received. Exiting...")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected error in main loop: {e}")
                    self.logger.info("Waiting for 60 seconds before retrying")
                    time.sleep(60)
        finally:
            self.db_handler.close()

if __name__ == "__main__":
    bot = TradingBot()
    bot.logger.info("Starting trading bot...")
    bot.run()
