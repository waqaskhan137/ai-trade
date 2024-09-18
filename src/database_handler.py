import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

class DatabaseHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.write_api = None
        self.initialize_influxdb()

    def initialize_influxdb(self):
        try:
            self.client = InfluxDBClient(
                url="http://influxdb:8086",
                token=os.getenv('INFLUXDB_TOKEN'),
                org=os.getenv('INFLUXDB_ORG')
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.logger.info("InfluxDB client initialized")
        except Exception as e:
            self.logger.error(f"Error initializing InfluxDB client: {e}")
            raise

    def write_market_data(self, symbol, data):
        try:
            point = Point("market_data") \
                .tag("symbol", symbol) \
                .field("open", float(data['open'].iloc[-1])) \
                .field("high", float(data['high'].iloc[-1])) \
                .field("low", float(data['low'].iloc[-1])) \
                .field("close", float(data['close'].iloc[-1])) \
                .field("volume", float(data['volume'].iloc[-1])) \
                .field("ma_short", float(data['ma_short'].iloc[-1])) \
                .field("ma_long", float(data['ma_long'].iloc[-1]))

            self.write_api.write(
                bucket=os.getenv('INFLUXDB_BUCKET'),
                org=os.getenv('INFLUXDB_ORG'),
                record=point
            )
            self.logger.debug("Data written to InfluxDB")
        except Exception as e:
            self.logger.error(f"Error writing to InfluxDB: {e}")
            raise

    def close(self):
        if self.client:
            self.client.close()
            self.logger.info("InfluxDB connection closed")