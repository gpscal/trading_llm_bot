from strategies.indicators import calculate_indicators  # Import the calculate_indicators function

def analyze_historical_data(btc_historical, sol_historical):
    btc_indicators, sol_indicators = calculate_indicators(btc_historical, sol_historical)
    return btc_indicators, sol_indicators
