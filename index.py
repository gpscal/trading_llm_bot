from trade.trade_logic import start_trading, print_current_balance
from config.config import CONFIG
from utils.logger import setup_logger

logger = setup_logger('main_logger', 'main.log')

logger.info(f"API Key: {CONFIG['api_key']}")
logger.info(f"API Secret: {CONFIG['api_secret']}")

if __name__ == '__main__':
    logger.info("Starting application")
    print_current_balance()
    start_trading()
