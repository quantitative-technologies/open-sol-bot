from enum import Enum


class TradingRoute(Enum):
    """Trading route types, representing different trading methods"""

    PUMP = "pump"  # PUMP protocol trading
    RAYDIUM_V4 = "raydium_v4"  # Raydium V4 protocol trading
    DEX = "dex"  # DEX trading

    @classmethod
    def from_str(cls, value: str) -> "TradingRoute":
        """Create trading route type from string

        Args:
            value (str): Trading route type string

        Returns:
            TradingRoute: Trading route type enum

        Raises:
            ValueError: If the string is not a valid trading route type
        """
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid trading route: {value}. Must be one of: {[e.value for e in cls]}"
            )
