# tests/test_integration.py

import asyncio
import unittest
import logging
from src.data.market_data import MarketDataManager
from src.execution.order_manager import OrderManager
from src.risk.risk_manager import RiskManager
from src.strategies.market_making import MarketMakingStrategy
import sys

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class TestIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Dummy configuration for testing
        self.config = {
            "trading": {"default_symbol": "BTCUSDT"},
            "api": {
                "binance": {
                    "api_key": "dummy_key",
                    "api_secret": "dummy_secret",
                    "base_url": "https://api.binance.com"
                }
            },
            "risk": {"max_exposure": 0.05, "volatility_threshold": 0.1}
        }
        # Set up a simple logger that prints to the console
        self.logger = logging.getLogger("IntegrationTest")
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            self.logger.addHandler(logging.StreamHandler())

        # Instantiate the modules
        self.market_data_manager = MarketDataManager(self.config, self.logger)
        self.order_manager = OrderManager(self.config, self.logger)
        self.risk_manager = RiskManager(self.config, self.logger)
        self.strategy = MarketMakingStrategy(
            self.config,
            self.logger,
            self.market_data_manager,
            self.order_manager,
            self.risk_manager
        )

        # Override risk_manager's exposure simulation to always return 0 exposure for testing.
        self.risk_manager._simulate_exposure_update = lambda: 0.0

        # Monkey-patch send_order to capture order requests instead of sending real ones.
        self.order_calls = []
        async def dummy_send_order(symbol, side, quantity, price, order_type="LIMIT"):
            self.order_calls.append({
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "order_type": order_type
            })
            return {"status": "success", "order_id": len(self.order_calls)}
        self.order_manager.send_order = dummy_send_order

        # For this integration test, override the market data feed.
        # Instead of connecting to the live WebSocket, we simulate a message.
        async def dummy_start():
            self.logger.info("Simulated market data feed started.")
            # Simulate a new market data tick every second
            while True:
                # Create a dummy ticker message in Binance format (simplified)
                message = {
                    "e": "24hrTicker",
                    "s": self.config["trading"]["default_symbol"],
                    "c": "30000.00"  # Simulated current price
                }
                # Notify all subscribers
                for callback in self.market_data_manager.subscribers:
                    await callback(message)
                await asyncio.sleep(1)
        self.market_data_manager.start = dummy_start

    async def asyncTearDown(self):
        # Clean up any open sessions (if any)
        await self.order_manager.close()

    async def test_integration_flow(self):
        # Run risk management, strategy, and market data feed concurrently.
        risk_task = asyncio.create_task(self.risk_manager.monitor_risks())
        strategy_task = asyncio.create_task(self.strategy.run())
        market_data_task = asyncio.create_task(self.market_data_manager.start())
        
        # Let the system run for a short period (e.g., 3 seconds)
        await asyncio.sleep(3)
        
        # Cancel tasks to end the test cleanly.
        risk_task.cancel()
        strategy_task.cancel()
        market_data_task.cancel()
        try:
            await asyncio.gather(risk_task, strategy_task, market_data_task)
        except asyncio.CancelledError:
            pass

        # Verify that orders were generated (market making strategy should have triggered orders)
        self.assertGreater(len(self.order_calls), 0, "No orders were submitted during integration test")
        self.logger.info("Integration test completed. Orders generated: %s", self.order_calls)

if __name__ == '__main__':
    unittest.main()
