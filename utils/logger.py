import logging
import json

def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.hasHandlers():
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        handler = logging.FileHandler(log_file)        
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

def log_trade(action, volume, price, balance_usdt, balance_sol):
    trade_log = {
        "timestamp": get_timestamp(),
        "action": action,
        "volume": volume,
        "price": price,
        "balance_usdt": balance_usdt,
        "balance_sol": balance_sol
    }
    with open('trade_log.json', 'a') as file:
        json.dump(trade_log, file)
        file.write('\n')

def print_status(btc_current_price, sol_current_price, btc_momentum, confidence, balance_usdt, balance_sol, initial_total_usd, current_total_usd):
    total_gain_usd = current_total_usd - initial_total_usd
    status_log = {
        "timestamp": get_timestamp(),
        "btc_price": btc_current_price,
        "sol_price": sol_current_price,
        "btc_momentum": btc_momentum,
        "confidence": confidence,
        "balance_usdt": balance_usdt,
        "balance_sol": balance_sol,
        "current_total_usd": current_total_usd,
        "total_gain_usd": total_gain_usd
    }
    with open('status_log.json', 'a') as file:
        json.dump(status_log, file)
        file.write('\n')
    print(f"{Fore.GREEN}[{get_timestamp()}] BTC@{btc_current_price:.2f} SOL@{sol_current_price:.2f} BTC momentum: {btc_momentum:.2f} Confidence level: {confidence:.2f} Balance USDT: {balance_usdt:.2f}, SOL: {balance_sol:.6f}, Total USD: {current_total_usd:.2f}, Total Gain USD: {total_gain_usd:.2f}{Fore.RESET}")
