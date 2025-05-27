from enum import Enum


class SwapDirection(str, Enum):
    Buy = "buy"
    Sell = "sell"


class SwapInType(str, Enum):
    Qty = "qty"  # Trade by quantity
    Pct = "pct"  # Trade by percentage
