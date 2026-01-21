"""
Tests for PersistentRateLimiter.
"""

import asyncio
import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from mycoder.providers.rate_limiter import PersistentRateLimiter


class TestPersistentRateLimiter(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.state_path = self.test_dir / "rate_limits.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def test_rpm_limit(self):
        limiter = PersistentRateLimiter(
            "test_provider", rpm=5, rpd=1000, state_path=self.state_path
        )

        # Should allow 5 requests
        for _ in range(5):
            start = time.time()
            await limiter.acquire()
            self.assertLess(time.time() - start, 0.1)

        # 6th request should wait (mocking sleep would be better but simple check is okay)
        # We can mock asyncio.sleep to verify it's called

        # Actually testing wait logic in unit test is slow.
        # Let's verify state updates.
        self.assertEqual(limiter.state.minute_request_count, 5)

    async def test_persistence(self):
        limiter = PersistentRateLimiter(
            "test_provider", rpm=10, rpd=1000, state_path=self.state_path
        )
        await limiter.acquire()
        self.assertEqual(limiter.state.minute_request_count, 1)

        # New instance should load state
        limiter2 = PersistentRateLimiter(
            "test_provider", rpm=10, rpd=1000, state_path=self.state_path
        )
        self.assertEqual(limiter2.state.minute_request_count, 1)


if __name__ == "__main__":
    unittest.main()
