# src/main.py

import os
import yaml
import asyncio

from utils.logger import setup_logger

# Import modules (we’ll build these modules step by step)
from data.market_data import MarketDataManager
from execution.order_manager import OrderManager
from risk.risk_manager import RiskManager
from strategies.market_making import MarketMakingStrategy

async def main():
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Setup logging
    logger = setup_logger(config_path)
    logger.info("Starting Binance Trading System...")

    # Initialize modules
    market_data_manager = MarketDataManager(config, logger)
    order_manager = OrderManager(config, logger)
    risk_manager = RiskManager(config, logger)

    # Initialize a strategy (example: Market Making)
    market_making_strategy = MarketMakingStrategy(config, logger, market_data_manager, order_manager, risk_manager)

    # Start data feed, risk monitoring, and strategy logic concurrently
    try:
        await asyncio.gather(
            market_data_manager.start(),       # Start market data feed (async)
            risk_manager.monitor_risks(),        # Risk monitoring loop (async)
            market_making_strategy.run()         # Trading strategy loop (async)
        )
    except Exception as e:
        logger.exception("Error in main execution loop: %s", e)
    finally:
        logger.info("Shutting down trading system.")

if __name__ == '__main__':
    asyncio.run(main())
