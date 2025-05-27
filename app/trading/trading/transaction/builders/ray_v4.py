import base64
import os

from loguru import logger
from solana.rpc.commitment import Processed
from solana.rpc.types import TokenAccountOpts
from solbot_cache import get_min_balance_rent
from solbot_cache.rayidum import get_preferred_pool
from solbot_common.constants import (ACCOUNT_LAYOUT_LEN, SOL_DECIMAL,
                                     TOKEN_PROGRAM_ID, WSOL)
from solbot_common.utils.pool import (AmmV4PoolKeys, get_amm_v4_reserves,
                                      make_amm_v4_swap_instruction)
from solbot_common.utils.utils import (get_associated_token_address,
                                       get_token_balance)
from solders.instruction import \
    Instruction  # type: ignore[reportMissingModuleSource]
from solders.keypair import Keypair  # type: ignore[reportMissingModuleSource]
from solders.pubkey import Pubkey  # type: ignore[reportMissingModuleSource]
from solders.system_program import (  # type: ignore[reportMissingModuleSource]
    CreateAccountWithSeedParams, create_account_with_seed)
from solders.transaction import VersionedTransaction  # type: ignore
from spl.token.instructions import CloseAccountParams  # type: ignore
from spl.token.instructions import (InitializeAccountParams, close_account,
                                    create_associated_token_account,
                                    initialize_account)
from trading.swap import SwapDirection, SwapInType
from trading.tx import build_transaction

from .base import TransactionBuilder


class RaydiumV4TransactionBuilder(TransactionBuilder):
    async def build_buy_instructions(
        self,
        payer_keypair: Keypair,
        token_address: str,
        sol_in: float,
        slippage_bps: int,
    ) -> list[Instruction]:
        """Build a list of instructions for buying tokens

        Args:
            payer_keypair: Payer's key pair
            token_address: 代币地址
            sol_in: 输入的SOL数量
            slippage_bps: 滑点，以基点(bps)为单位，1bps = 0.01%

        Returns:
            list[Instruction]: List of instructions
        """
        logger.info(f"Building buy transaction: {token_address}, SOL input: {sol_in}, slippage: {slippage_bps}bps")

        # Get pool information
        pool_data = await get_preferred_pool(token_address)
        if pool_data is None:
            raise ValueError(f"Pool not found for token {token_address}")

        # Build pool keys
        pool_keys = AmmV4PoolKeys.from_pool_data(
            pool_id=pool_data["pool_id"],
            amm_data=pool_data["amm_data"],
            market_data=pool_data["market_data"],
        )

        # Determine the token mint
        token_mint = pool_keys.base_mint if pool_keys.base_mint != WSOL else pool_keys.quote_mint

        # Calculate transaction amount
        amount_in = int(sol_in * SOL_DECIMAL)

        # Get pool reserves
        base_reserve, quote_reserve, token_decimal = await get_amm_v4_reserves(pool_keys)

        # Calculate expected output
        # This is a simplified calculation, actual implementation may need more complex calculations
        constant_product = base_reserve * quote_reserve
        effective_sol_in = sol_in * (1 - (0.25 / 100))  # Consider 0.25% trading fee
        new_quote_reserve = quote_reserve + effective_sol_in
        new_base_reserve = constant_product / new_quote_reserve
        amount_out = base_reserve - new_base_reserve

        # Apply slippage
        slippage_adjustment = 1 - (slippage_bps / 10000)  # Convert bps to percentage
        minimum_amount_out = int(amount_out * slippage_adjustment * (10**token_decimal))

        logger.info(f"Input amount: {amount_in}, minimum output amount: {minimum_amount_out}")

        # Check if token account exists
        token_account = None
        token_accounts = await self.rpc_client.get_token_accounts_by_owner(
            payer_keypair.pubkey(), TokenAccountOpts(mint=token_mint), Processed
        )

        create_token_account_ix = None
        if token_accounts.value:
            token_account = token_accounts.value[0].pubkey
            logger.info(f"Found existing token account: {token_account}")
        else:
            token_account = get_associated_token_address(payer_keypair.pubkey(), token_mint)
            create_token_account_ix = create_associated_token_account(
                payer_keypair.pubkey(), payer_keypair.pubkey(), token_mint
            )
            logger.info(f"Creating new associated token account: {token_account}")

        # Create temporary WSOL account
        seed = base64.urlsafe_b64encode(os.urandom(24)).decode("utf-8")
        wsol_token_account = Pubkey.create_with_seed(payer_keypair.pubkey(), seed, TOKEN_PROGRAM_ID)

        # Get minimum balance needed for rent exemption
        balance_needed = await get_min_balance_rent()

        # Create WSOL account instruction
        create_wsol_account_ix = create_account_with_seed(
            CreateAccountWithSeedParams(
                from_pubkey=payer_keypair.pubkey(),
                to_pubkey=wsol_token_account,
                base=payer_keypair.pubkey(),
                seed=seed,
                lamports=balance_needed + amount_in,
                space=ACCOUNT_LAYOUT_LEN,
                owner=TOKEN_PROGRAM_ID,
            )
        )

        # Initialize WSOL account instruction
        init_wsol_account_ix = initialize_account(
            InitializeAccountParams(
                program_id=TOKEN_PROGRAM_ID,
                account=wsol_token_account,
                mint=WSOL,
                owner=payer_keypair.pubkey(),
            )
        )

        # Create swap instruction
        swap_ix = make_amm_v4_swap_instruction(
            amount_in=amount_in,
            minimum_amount_out=minimum_amount_out,
            token_account_in=wsol_token_account,
            token_account_out=token_account,
            accounts=pool_keys,
            owner=payer_keypair.pubkey(),
        )

        # Close WSOL account instruction
        close_wsol_account_ix = close_account(
            CloseAccountParams(
                program_id=TOKEN_PROGRAM_ID,
                account=wsol_token_account,
                dest=payer_keypair.pubkey(),
                owner=payer_keypair.pubkey(),
            )
        )

        # Assemble instruction list
        instructions = [
            create_wsol_account_ix,
            init_wsol_account_ix,
        ]

        if create_token_account_ix:
            instructions.append(create_token_account_ix)

        instructions.append(swap_ix)
        instructions.append(close_wsol_account_ix)

        return instructions

    async def build_sell_instructions(
        self,
        payer_keypair: Keypair,
        token_address: str,
        ui_amount: float,
        in_type: SwapInType,
        slippage_bps: int,
    ) -> list[Instruction]:
        """Build instructions for selling tokens

        Args:
            payer_keypair: Payer's keypair
            token_address: Token address
            ui_amount: Input amount (percentage or specific amount)
            in_type: Input type (percentage or specific amount)
            slippage_bps: Slippage in basis points (bps), 1bps = 0.01%

        Returns:
            list[Instruction]: List of instructions
        """
        if in_type == SwapInType.Pct:
            if not (0 < ui_amount <= 100):
                raise ValueError("Percentage must be between 1 and 100")
        elif in_type == SwapInType.Qty:
            if ui_amount <= 0:
                raise ValueError("Amount must be greater than 0")
        else:
            raise ValueError("in_type must be pct or qty")

        logger.info(
            f"Building sell transaction: {token_address}, input: {ui_amount}{in_type.value}, slippage: {slippage_bps}bps"
        )

        # Get pool information
        pool_data = await get_preferred_pool(token_address)
        if pool_data is None:
            raise ValueError(f"Pool not found for token {token_address}")

        # Build pool keys
        pool_keys = AmmV4PoolKeys.from_pool_data(
            pool_id=pool_data["pool_id"],
            amm_data=pool_data["amm_data"],
            market_data=pool_data["market_data"],
        )

        # Determine token mint
        token_mint = pool_keys.base_mint if pool_keys.base_mint != WSOL else pool_keys.quote_mint

        # Get token account
        token_account = get_associated_token_address(payer_keypair.pubkey(), token_mint)

        # Get token balance
        token_balance = await get_token_balance(token_account, self.rpc_client)
        if token_balance is None or token_balance == 0:
            raise ValueError(f"No available token balance: {token_mint}")

        # Calculate amount to sell
        if in_type == SwapInType.Pct:
            sell_amount = token_balance * (ui_amount / 100)
            logger.info(f"Token balance: {token_balance}, sell amount: {sell_amount} ({ui_amount}%)")
        else:
            sell_amount = ui_amount
            logger.info(f"Sell amount: {sell_amount}")

        # Get pool reserves
        base_reserve, quote_reserve, token_decimal = await get_amm_v4_reserves(pool_keys)

        # Calculate expected output
        # This is a simplified calculation, actual implementation may need more complex calculations
        constant_product = base_reserve * quote_reserve
        effective_token_in = sell_amount * (1 - (0.25 / 100))  # Consider 0.25% trading fee
        new_base_reserve = base_reserve + effective_token_in
        new_quote_reserve = constant_product / new_base_reserve
        amount_out = quote_reserve - new_quote_reserve

        # Apply slippage
        slippage_adjustment = 1 - (slippage_bps / 10000)  # Convert bps to percentage
        minimum_amount_out = int(amount_out * slippage_adjustment * SOL_DECIMAL)

        # Calculate input amount
        amount_in = int(sell_amount * (10**token_decimal))

        logger.info(f"Input amount: {amount_in}, minimum output amount: {minimum_amount_out}")

        # Create temporary WSOL account
        seed = base64.urlsafe_b64encode(os.urandom(24)).decode("utf-8")
        wsol_token_account = Pubkey.create_with_seed(payer_keypair.pubkey(), seed, TOKEN_PROGRAM_ID)

        # Get minimum balance needed for rent exemption
        balance_needed = await get_min_balance_rent()

        # Create WSOL account instruction
        create_wsol_account_ix = create_account_with_seed(
            CreateAccountWithSeedParams(
                from_pubkey=payer_keypair.pubkey(),
                to_pubkey=wsol_token_account,
                base=payer_keypair.pubkey(),
                seed=seed,
                lamports=balance_needed,
                space=ACCOUNT_LAYOUT_LEN,
                owner=TOKEN_PROGRAM_ID,
            )
        )

        # Initialize WSOL account instruction
        init_wsol_account_ix = initialize_account(
            InitializeAccountParams(
                program_id=TOKEN_PROGRAM_ID,
                account=wsol_token_account,
                mint=WSOL,
                owner=payer_keypair.pubkey(),
            )
        )

        # Create swap instruction
        swap_ix = make_amm_v4_swap_instruction(
            amount_in=amount_in,
            minimum_amount_out=minimum_amount_out,
            token_account_in=token_account,
            token_account_out=wsol_token_account,
            accounts=pool_keys,
            owner=payer_keypair.pubkey(),
        )

        # Close WSOL account instruction
        close_wsol_account_ix = close_account(
            CloseAccountParams(
                program_id=TOKEN_PROGRAM_ID,
                account=wsol_token_account,
                dest=payer_keypair.pubkey(),
                owner=payer_keypair.pubkey(),
            )
        )

        # Assemble instruction list
        instructions = [
            create_wsol_account_ix,
            init_wsol_account_ix,
            swap_ix,
            close_wsol_account_ix,
        ]

        # If selling 100%, close token account
        if ui_amount == 100:
            close_token_account_ix = close_account(
                CloseAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=token_account,
                    dest=payer_keypair.pubkey(),
                    owner=payer_keypair.pubkey(),
                )
            )
            instructions.append(close_token_account_ix)

        return instructions

    async def build_swap_transaction(
        self,
        keypair: Keypair,
        token_address: str,
        ui_amount: float,
        swap_direction: SwapDirection,
        slippage_bps: int,
        in_type: SwapInType | None = None,
        use_jito: bool = False,
        priority_fee: float | None = None,
    ) -> VersionedTransaction:
        """Build swap transaction

        Args:
            keypair (Keypair): Wallet keypair
            token_address (str): Token address
            ui_amount (float): Transaction amount
            swap_direction (SwapDirection): Swap direction
            slippage_bps (int): Slippage in basis points
            in_type (SwapInType | None, optional): Input type. Defaults to None.
            use_jito (bool, optional): Whether to use Jito. Defaults to False.
            priority_fee (Optional[float], optional): Priority fee. Defaults to None.

        Returns:
            VersionedTransaction: Built transaction
        """
        if swap_direction not in [SwapDirection.Buy, SwapDirection.Sell]:
            raise ValueError("swap_direction must be buy or sell")

        if swap_direction == SwapDirection.Buy:
            instructions = await self.build_buy_instructions(
                payer_keypair=keypair,
                token_address=token_address,
                sol_in=ui_amount,
                slippage_bps=slippage_bps,
            )
        elif swap_direction == SwapDirection.Sell:
            if in_type is None:
                raise ValueError("in_type must be pct or qty")

            instructions = await self.build_sell_instructions(
                payer_keypair=keypair,
                token_address=token_address,
                ui_amount=ui_amount,
                slippage_bps=slippage_bps,
                in_type=in_type,
            )

        return await build_transaction(
            keypair=keypair,
            instructions=instructions,
            use_jito=use_jito,
            priority_fee=priority_fee,
        )
