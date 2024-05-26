import asyncio
import numpy as np
from utils.data_fetchers import fetch_and_analyze_historical_data
from utils.logger import setup_logger
from trade.trade_logic import handle_trade_with_fees
from utils.utils import log_and_print_status
from config.config import CONFIG

logger = setup_logger('main_logger', 'main.log')

async def trading_loop(balance, pairs, poll_interval):
    initial_sol_price = balance['sol_price']
    while True:
        logger.debug("Top of the main loop")
        
        await asyncio.sleep(poll_interval)
        logger.debug("After sleep in the main loop")
        
        await fetch_and_analyze_historical_data(pairs, balance)

        btc_price = balance['btc_price']
        sol_price = balance['sol_price']
        btc_indicators = balance.get('btc_indicators', {})
        sol_indicators = balance.get('sol_indicators', {})

        if btc_price and sol_price and btc_indicators and sol_indicators:
            logger.debug(f"BTC Price: {btc_price}, SOL Price: {sol_price}")
            logger.debug(f"BTC Indicators: {btc_indicators}")
            logger.debug(f"SOL Indicators: {sol_indicators}")

            balance['usdt'], balance['sol'], balance['last_trade_time'] = handle_trade_with_fees(
                btc_price, sol_price, balance['usdt'], balance['sol'], balance['last_trade_time'], btc_indicators, sol_indicators, initial_sol_price, balance['initial_total_usd']
            )
        
        current_total_usd = balance['usdt'] + balance['sol'] * balance['sol_price']
        total_gain_usd = current_total_usd - balance['initial_total_usd']
        
        log_and_print_status(balance, current_total_usd, total_gain_usd)
