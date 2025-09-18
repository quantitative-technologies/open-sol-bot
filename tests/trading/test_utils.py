import pytest
from solders.pubkey import Pubkey

from app.trading.trading.utils import has_ata
from libs.common.solbot_common.utils.utils import get_async_client


@pytest.mark.asyncio
async def test_has_ata():
    client = get_async_client()
    mint = Pubkey.from_string("HiPZWtXxEvgzKnMBfHGvZqHfvgaJ1YHZVhwai1Wd8t4J")
    owner = Pubkey.from_string("Ckwd4awa6N2VWyMuuScbkdEJqSY5VpajuLd7m7QwXMvY")
    result = await has_ata(client, mint, owner)
    assert result is False
