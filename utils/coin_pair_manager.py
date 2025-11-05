"""Utility for managing exchange pair mappings across supported coins."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from config.config import CONFIG


@dataclass(frozen=True)
class CoinPair:
    """Representation of the pair symbols used for a given coin."""

    rest: str
    websocket: str
    rest_alt: Optional[str] = None


class CoinPairManager:
    """Centralised helper for resolving pair names and per-coin settings."""

    def __init__(self, config: Dict | None = None) -> None:
        self._config = config or CONFIG
        self._coin_pairs = self._normalise_pairs(self._config.get('coin_pairs', {}))

    @staticmethod
    def _normalise_pairs(pairs: Dict[str, Dict[str, str]]) -> Dict[str, CoinPair]:
        normalised: Dict[str, CoinPair] = {}
        for coin, values in pairs.items():
            upper_coin = coin.upper()
            normalised[upper_coin] = CoinPair(
                rest=values.get('rest') or values.get('rest_alt') or upper_coin,
                websocket=values.get('websocket') or upper_coin,
                rest_alt=values.get('rest_alt'),
            )
        return normalised

    def supported_coins(self) -> List[str]:
        return [coin.upper() for coin in self._config.get('tradable_coins', [])]

    def validate_coin(self, coin: str) -> str:
        upper_coin = coin.upper()
        if upper_coin not in self.supported_coins():
            raise ValueError(f"Unsupported coin '{coin}'. Supported coins: {self.supported_coins()}")
        return upper_coin

    def get_rest_pair(self, coin: str, prefer_usdt: bool = True) -> str:
        upper_coin = self.validate_coin(coin)
        pair = self._coin_pairs.get(upper_coin)
        if not pair:
            raise KeyError(f"Missing REST pair mapping for {upper_coin}")
        if prefer_usdt:
            return pair.rest
        return pair.rest_alt or pair.rest

    def get_websocket_pair(self, coin: str) -> str:
        upper_coin = self.validate_coin(coin)
        pair = self._coin_pairs.get(upper_coin)
        if not pair:
            raise KeyError(f"Missing websocket pair mapping for {upper_coin}")
        return pair.websocket

    def get_volume_limits(self, coin: str) -> Dict[str, float]:
        upper_coin = self.validate_coin(coin)
        limits = self._config.get('coin_volume_limits', {}).get(upper_coin)
        if limits:
            return limits
        # Fallback to legacy single coin values
        return {
            'min': self._config.get('min_volume', 0.0),
            'max': self._config.get('max_volume', float('inf')),
        }

    def initial_coin_balance(self, coin: str) -> float:
        upper_coin = self.validate_coin(coin)
        return float(self._config.get('initial_coin_balances', {}).get(upper_coin, 0.0))

    def get_counter_coin(self, coin: str) -> Optional[str]:
        upper_coin = self.validate_coin(coin)
        coins = self.supported_coins()
        for candidate in coins:
            if candidate != upper_coin:
                return candidate
        return None

    def rest_pair_map(self, coins: Iterable[str] | None = None) -> Dict[str, str]:
        coins = coins or self.supported_coins()
        return {coin.upper(): self.get_rest_pair(coin) for coin in coins}

    def websocket_pairs(self, coins: Iterable[str] | None = None) -> List[str]:
        coins = coins or self.supported_coins()
        return [self.get_websocket_pair(coin) for coin in coins]


def get_coin_pair_manager() -> CoinPairManager:
    """Factory to create a singleton-like manager if needed later."""

    return CoinPairManager(CONFIG)
