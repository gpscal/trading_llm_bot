def calculate_volume(price, balance, config):
    return min(config['max_volume'], balance / price)
