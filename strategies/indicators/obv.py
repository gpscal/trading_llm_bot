import numpy as np

def calculate_obv(ohlc_data):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    volumes = np.array([float(candle[5]) for candle in ohlc_data])
    obv = np.zeros_like(closes)
    obv[0] = volumes[0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv[i] = obv[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            obv[i] = obv[i - 1] - volumes[i]
        else:
            obv[i] = obv[i - 1]
    return obv[-1]
