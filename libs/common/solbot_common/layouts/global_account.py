import struct
from dataclasses import dataclass
from typing import Final

from construct import Flag, Int64ul, Struct
from solbot_common.layouts.layouts import PUBLIC_KEY_LAYOUT
from solders.pubkey import Pubkey  # type: ignore

from .calculate_discriminator import calculate_discriminator

# See: https://github.com/pump-fun/pump-public-docs/blob/main/docs/PUMP_PROGRAM_README.md
GLOBAL_ACCOUNT_LAYOUT = Struct(
    "initialized" / Flag,
    "authority" / PUBLIC_KEY_LAYOUT,
    "fee_recipient" / PUBLIC_KEY_LAYOUT,
    "initial_virtual_token_reserves" / Int64ul,
    "initial_virtual_sol_reserves" / Int64ul,
    "initial_real_token_reserves" / Int64ul,
    "token_total_supply" / Int64ul,
    "fee_basis_points" / Int64ul,
    "withdrawal_authority" / PUBLIC_KEY_LAYOUT,
    "enable_migration" / Flag,
    "pool_migration_fee" / Int64ul,
    "creator_fee" / Int64ul,
    "fee_recipients" / PUBLIC_KEY_LAYOUT[7],
)
_EXPECTED_DISCRIMINATOR: Final[bytes] = struct.pack("<Q", 9183522199395952807)

#@dataclass
class GlobalAccount:
    initialized: bool
    authority: Pubkey
    fee_recipient: Pubkey
    initial_virtual_token_reserves: int
    initial_virtual_sol_reserves: int
    initial_real_token_reserves: int
    token_total_supply: int
    fee_basis_points: int
    withdrawal_authority: Pubkey
    enable_migration: bool
    pool_migration_fee: int
    creator_fee: int
    fee_recipients: list[Pubkey]
    
    
    def __init__(self, data: bytes) -> None:
        discriminator = calculate_discriminator("account:global")
        if data[:8] != _EXPECTED_DISCRIMINATOR:
            raise ValueError("Invalid global account discriminator")

        parsed = GLOBAL_ACCOUNT_LAYOUT.parse(data[8:])
        
        # Convert byte arrays to Pubkey objects
        self.authority = Pubkey.from_bytes(parsed.authority)
        self.fee_recipient = Pubkey.from_bytes(parsed.fee_recipient)
        self.withdrawal_authority = Pubkey.from_bytes(parsed.withdrawal_authority)
        self.fee_recipients = [Pubkey.from_bytes(recipient) for recipient in parsed.fee_recipients]
        
        # Set other fields directly
        self.initialized = parsed.initialized
        self.initial_virtual_token_reserves = parsed.initial_virtual_token_reserves
        self.initial_virtual_sol_reserves = parsed.initial_virtual_sol_reserves
        self.initial_real_token_reserves = parsed.initial_real_token_reserves
        self.token_total_supply = parsed.token_total_supply
        self.fee_basis_points = parsed.fee_basis_points
        self.enable_migration = parsed.enable_migration
        self.pool_migration_fee = parsed.pool_migration_fee
        self.creator_fee = parsed.creator_fee

    def get_initial_buy_price(self, amount: int) -> int:
        """
        Calculate the initial purchase price
        """
        if amount <= 0:
            return 0

        n = self.initial_virtual_sol_reserves * self.initial_virtual_token_reserves
        i = self.initial_virtual_sol_reserves + amount
        r = n // i + 1  # 使用整数除法
        s = self.initial_virtual_token_reserves - r

        return min(s, self.initial_real_token_reserves)

    # @classmethod
    # def from_buffer(cls, buffer: bytes) -> "GlobalAccount":
    #     """
    #     Parse account data from a byte buffer
    #     Format: <Q ? 32s 32s Q Q Q Q Q
    #     Q: unsigned long long (8 bytes)
    #     ?: boolean (1 byte)
    #     32s: 32 bytes for Pubkey
    #     """
    #     try:
    #         # 解包数据
    #         (
    #             discriminator,
    #             initialized,
    #             authority_bytes,
    #             fee_recipient_bytes,
    #             initial_virtual_token_reserves,
    #             initial_virtual_sol_reserves,
    #             initial_real_token_reserves,
    #             token_total_supply,
    #             fee_basis_points,
    #         ) = struct.unpack("<Q?32s32sQQQQQ", buffer)

    #         # 转换 Pubkey
    #         authority = Pubkey.from_bytes(authority_bytes)
    #         fee_recipient = Pubkey.from_bytes(fee_recipient_bytes)

    #         return cls(
    #             discriminator=discriminator,
    #             initialized=initialized,
    #             authority=authority,
    #             fee_recipient=fee_recipient,
    #             initial_virtual_token_reserves=initial_virtual_token_reserves,
    #             initial_virtual_sol_reserves=initial_virtual_sol_reserves,
    #             initial_real_token_reserves=initial_real_token_reserves,
    #             token_total_supply=token_total_supply,
    #             fee_basis_points=fee_basis_points,
    #         )
    #     except struct.error as e:
    #         raise ValueError(f"Failed to decode buffer: {e}")

    # def __post_init__(self):
    #     """
    #     数据类初始化后的验证
    #     """
    #     if not isinstance(self.authority, (Pubkey, type(None))):
    #         raise TypeError("authority must be a Pubkey or None")
    #     if not isinstance(self.fee_recipient, (Pubkey, type(None))):
    #         raise TypeError("fee_recipient must be a Pubkey or None")
