def calculate_volume(price, balance, config):
    volume = min(config['max_volume'], max(config['min_volume'], balance / price))
    return volume
