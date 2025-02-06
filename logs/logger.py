# src/utils/logger.py

import logging
import os
import yaml

def setup_logger(config_path: str = os.path.join(os.path.dirname(__file__), '../../config/config.yaml')) -> logging.Logger:
    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    log_config = config.get("logging", {})
    log_level = getattr(logging, log_config.get("level", "INFO").upper(), logging.INFO)
    log_file = os.path.join(os.path.dirname(__file__), '../../', log_config.get("file", "logs/trading_system.log"))

    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Create and configure logger
    logger = logging.getLogger("TradingSystem")
    logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.debug("Logger initialized.")
    return logger
