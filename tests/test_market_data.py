# tests/test_market_data.py

import asyncio
import unittest
import json
import logging
from src.data.market_data import MarketDataManager

import sys
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class TestMarketDataManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Create a dummy config and logger
        self.config = {"trading": {"default_symbol": "BTCUSDT"}}
        self.logger = logging.getLogger("TestLogger")
        self.logger.addHandler(logging.StreamHandler())
        self.market_data_manager = MarketDataManager(self.config, self.logger)

        # Override _handle_messages to simulate receiving one message without recursion
        async def dummy_handle_messages(websocket):
            test_message = '{"e": "24hrTicker", "s": "BTCUSDT", "c": "30000.00"}'
            try:
                data = json.loads(test_message)
                self.logger.debug("Dummy data parsed: %s", data)
                # Manually call each subscriber with the test data
                for callback in self.market_data_manager.subscribers:
                    await callback(data)
            except Exception as e:
                self.logger.exception("Error in dummy_handle_messages: %s", e)
        self.market_data_manager._handle_messages = dummy_handle_messages

    async def test_subscribe(self):
        # Flag to check if callback was called
        self.callback_called = False

        async def dummy_callback(data):
            self.callback_called = True

        self.market_data_manager.subscribe(dummy_callback)
        self.assertEqual(len(self.market_data_manager.subscribers), 1)

        # Simulate receiving a message
        await self.market_data_manager._handle_messages(None)
        self.assertTrue(self.callback_called)

if __name__ == '__main__':
    unittest.main()
