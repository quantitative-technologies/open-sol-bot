import asyncio
from collections.abc import Sequence

from solbot_common.config import settings
from solbot_common.log import logger
from solbot_common.prestart import pre_start
from solbot_common.types import copytrade
from solbot_common.utils import get_async_client
from solbot_db.redis import RedisClient
from solders.pubkey import Pubkey  # type: ignore
from wallet_tracker.benchmark import BenchmarkService
from wallet_tracker.tx_monitor import TxMonitor
from wallet_tracker.tx_worker import TransactionWorker


class WalletTracker:
    def __init__(self, init_wallets: Sequence[Pubkey]):
        self.redis = RedisClient.get_instance()
        self.client = get_async_client()
        self.wallets = init_wallets
        self.transaction_monitor = TxMonitor(self.wallets, mode=settings.monitor.mode)
        self.transaction_worker = TransactionWorker(self.redis)
        self.benchmark_service = BenchmarkService()

    # @provide_session
    # async def sync_wallet(self, *, session: AsyncSession = NEW_ASYNC_SESSION):
    #     """
    #     The
    #     function `sync_wallet` iterates through wallets, retrieves tokens, and updates associated
    #     token accounts in a database session.
    #     """
    #     tokens = []
    #     mint_accounts = {}
    #     for wallet in self.wallets:
    #         _tokens = await get_wallet_tokens(wallet, self.client)
    #         tokens.extend(_tokens)
    #
    #     # If it does not exist, insert it; if it exists, update it
    #     for token in tokens:
    #         mint_account = mint_accounts.get(token.mint.__str__())
    #         if mint_account is None:
    #             mint_account = await get_mint_account(token.mint, self.client)
    #             mint_accounts[token.mint.__str__()] = mint_account
    #         if mint_account is None:
    #             continue
    #         ata = AssociatedTokenAccount.from_token_account(
    #             token, mint_account.decimals
    #         )
    #         await session.merge(ata)
    #         logger.info(f"sync wallet {wallet} token {token.mint} ata {ata}")
    #     await session.commit()
    #     logger.info("sync wallet done")

    async def start(self):
        # await self.sync_wallet()
        # Use asyncio.gather to perform monitoring tasks concurrently

        await asyncio.gather(
            self.benchmark_service.start(),
            self.transaction_monitor.start(),
            self.transaction_worker.start(),
        )

    async def stop(self):
        await self.transaction_monitor.stop()
        await self.transaction_worker.stop()
        await self.benchmark_service.stop()


if __name__ == "__main__":
    pre_start()

    # Get the listened wallet from the configuration
    wallets = set(settings.monitor.wallets)

    # Get the wallet to be monitored from the order configuration
    for copytrade in settings.copytrades:
        wallets.add(copytrade.target_wallet)

    tracker = WalletTracker(list(wallets))
    try:
        asyncio.run(tracker.start())
    except KeyboardInterrupt:
        logger.info("The program was terminated manually")
    except Exception as e:
        logger.error(f"Program terminates abnormally: {e}")
        logger.exception(e)
