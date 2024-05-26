import numpy as np

def calculate_correlation(btc_data, sol_data):
    btc_closes = np.array([float(candle[4]) for candle in btc_data])
    sol_closes = np.array([float(candle[4]) for candle in sol_data])
    min_length = min(len(btc_closes), len(sol_closes))
    btc_closes = btc_closes[:min_length]
    sol_closes = sol_closes[:min_length]
    correlation = np.corrcoef(btc_closes, sol_closes)[0, 1]
    return correlation
