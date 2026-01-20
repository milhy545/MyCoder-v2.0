import time

import pytest

from mycoder.api_providers import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_tokens() -> None:
    limiter = RateLimiter(requests_per_minute=2)

    await limiter.acquire()
    await limiter.acquire()

    assert limiter.tokens >= 0


def test_rate_limiter_refill() -> None:
    limiter = RateLimiter(requests_per_minute=1)
    limiter.tokens = 0
    limiter.last_refill = time.time() - 120

    limiter._refill()

    assert limiter.tokens == 1
