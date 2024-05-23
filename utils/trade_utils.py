from utils.balance import initialize_balances
from utils.websocket_handler import handle_websocket_data
from utils.periodic_tasks import print_status_periodically

def analyze_historical_data(btc_historical, sol_historical):
    btc_indicators, sol_indicators = calculate_indicators(btc_historical, sol_historical)
    return btc_indicators, sol_indicators
