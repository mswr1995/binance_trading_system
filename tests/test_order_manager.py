# tests/test_order_manager.py

import asyncio
import unittest
import logging
from src.execution.order_manager import OrderManager
import sys

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class TestOrderManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Dummy config with test API credentials (not real)
        self.config = {
            "api": {
                "binance": {
                    "api_key": "test_key",
                    "api_secret": "test_secret",
                    "base_url": "https://api.binance.com"
                }
            }
        }
        self.logger = logging.getLogger("TestLogger")
        self.logger.addHandler(logging.StreamHandler())
        self.order_manager = OrderManager(self.config, self.logger)

        # Monkey-patch _send_request to return a dummy success response
        self.order_manager._send_request = self.dummy_send_request

    async def asyncTearDown(self):
        # Close the client session to avoid the unclosed session warning
        await self.order_manager.close()

    async def dummy_send_request(self, method, path, params):
        return {"status": "success", "order_id": 9999}

    async def test_send_order(self):
        response = await self.order_manager.send_order("BTCUSDT", "BUY", 0.1, 30000.0)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["order_id"], 9999)

if __name__ == '__main__':
    unittest.main()
