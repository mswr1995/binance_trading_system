# src/execution/order_manager.py

import asyncio
import logging
import time
import hmac
import hashlib
import aiohttp
from urllib.parse import urlencode

class OrderManager:
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        binance_config = self.config.get("api", {}).get("binance", {})
        self.api_key = binance_config.get("api_key")
        self.api_secret = binance_config.get("api_secret").encode()
        self.base_url = binance_config.get("base_url", "https://api.binance.com")
        self.session = aiohttp.ClientSession()

    def _get_signature(self, params: dict) -> str:
        query_string = urlencode(params)
        signature = hmac.new(self.api_secret, query_string.encode(), hashlib.sha256).hexdigest()
        return signature

    async def _send_request(self, method: str, path: str, params: dict):
        url = f"{self.base_url}{path}"
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._get_signature(params)
        headers = {"X-MBX-APIKEY": self.api_key}
        self.logger.debug("Sending %s request to %s with params: %s", method, url, params)

        for attempt in range(3):
            try:
                async with self.session.request(method, url, params=params, headers=headers) as response:
                    data = await response.json()
                    if response.status != 200:
                        self.logger.error("Error response: %s", data)
                        raise Exception(f"Request failed with status {response.status}")
                    self.logger.debug("Received response: %s", data)
                    return data
            except Exception as e:
                self.logger.exception("Request error on attempt %d: %s", attempt + 1, e)
                await asyncio.sleep(1)
        raise Exception("Max retries exceeded for order request.")

    async def send_order(self, symbol: str, side: str, quantity: float, price: float = None, order_type: str = "LIMIT"):
        """
        Send an order to Binance.
        :param symbol: Trading pair symbol (e.g., 'BTCUSDT')
        :param side: 'BUY' or 'SELL'
        :param quantity: Amount to trade
        :param price: Price for limit orders; if None, a market order is assumed
        :param order_type: Type of order ("LIMIT" or "MARKET")
        """
        path = "/api/v3/order"
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"
        order_response = await self._send_request("POST", path, params)
        self.logger.info("Order submitted: %s", order_response)
        return order_response

    async def close(self):
        """Cleanly close the aiohttp session."""
        await self.session.close()
