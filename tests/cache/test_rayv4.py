import pytest
from solbot_cache.rayidum import get_preferred_pool


@pytest.mark.asyncio
@pytest.mark.parametrize("token_mint", [
    "2ru87k7yAZnDRsnqVpgJYETFgqVApuBcwB2xDb19pump",
    "B5r8sv2EsxHj9orqVah3UxGkMjkL4CZNrz8PCvyUpump"
])
async def test_get_preferred_pool(token_mint):
    pool = await get_preferred_pool(token_mint)
    assert pool is not None
