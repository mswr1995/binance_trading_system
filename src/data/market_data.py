# src/data/market_data.py

import asyncio
import json
import logging
import websockets

class MarketDataManager:
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.symbol = self.config.get("trading", {}).get("default_symbol", "BTCUSDT")
        self.ws_endpoint = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@ticker"
        self.subscribers = []  # Modules can subscribe to market data updates

    async def connect(self):
        """Establish a connection to Binance's WebSocket API."""
        while True:
            try:
                async with websockets.connect(self.ws_endpoint) as websocket:
                    self.logger.info("Connected to Binance WebSocket for %s", self.symbol)
                    await self._handle_messages(websocket)
            except Exception as e:
                self.logger.exception("WebSocket connection error: %s", e)
                self.logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def _handle_messages(self, websocket):
        """Listen for messages from the WebSocket and broadcast to subscribers."""
        async for message in websocket:
            try:
                data = json.loads(message)
                self.logger.debug("Received data: %s", data)
                # Notify all subscribers about new market data
                for callback in self.subscribers:
                    asyncio.create_task(callback(data))
            except json.JSONDecodeError as e:
                self.logger.exception("JSON decode error: %s", e)

    def subscribe(self, callback):
        """Subscribe a callback to market data updates."""
        self.subscribers.append(callback)
        self.logger.info("New subscriber added: %s", callback.__name__)

    async def start(self):
        """Start the market data connection loop."""
        self.logger.info("Starting live market data feed...")
        await self.connect()
