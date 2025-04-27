"""Transaction Settlement Module

Contains the following main components:
1. SwapSettlementProcessor: Transaction settlement processor, responsible for retrieving and validating transaction status
"""

from .processor import SwapSettlementProcessor

__all__ = ["SwapSettlementProcessor"]
