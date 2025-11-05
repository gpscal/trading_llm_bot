from utils.coin_pair_manager import get_coin_pair_manager


def calculate_volume(price, balance_in_quote, config, coin):
    """Calculate trade volume for a specific coin using configured limits."""

    if price <= 0:
        return 0.0

    manager = get_coin_pair_manager()
    limits = manager.get_volume_limits(coin)
    raw_volume = balance_in_quote / price
    min_volume = limits.get('min', config.get('min_volume', 0.0))
    max_volume = limits.get('max', config.get('max_volume', raw_volume))
    volume = min(max_volume, max(min_volume, raw_volume))
    return max(volume, 0.0)
