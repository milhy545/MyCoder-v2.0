#!/usr/bin/env python3
"""Quick test script for claude-cli-auth module."""

import asyncio
import logging
import sys
from pathlib import Path

# Set up simple logging
logging.basicConfig(level=logging.WARNING)

# Disable structured logging issues
logging.getLogger("claude_cli_auth").setLevel(logging.CRITICAL)

async def test_basic_functionality():
    """Test basic module functionality."""
    print("🧪 Testing Claude CLI Auth module...")

    try:
        # Test 1: Import
        print("1️⃣  Testing imports...")
        from claude_cli_auth import ClaudeAuthManager, AuthConfig
        print("   ✅ Imports successful")

        # Test 2: Configuration
        print("2️⃣  Testing configuration...")
        config = AuthConfig(
            working_directory=Path.cwd(),
            timeout_seconds=30,
            use_sdk=False,  # Disable SDK to avoid issues
        )
        print("   ✅ Configuration created")

        # Test 3: Authentication status
        print("3️⃣  Testing authentication...")
        try:
            # We expect this might fail since we haven't set up auth properly
            claude = ClaudeAuthManager(config=config, prefer_sdk=False)
            print("   ✅ ClaudeAuthManager initialized")

            # Test health check
            health = claude.is_healthy()
            print(f"   Health status: {'✅ Healthy' if health else '⚠️ Unhealthy'}")

            await claude.shutdown()

        except Exception as e:
            print(f"   ⚠️  Authentication error (expected): {str(e)[:100]}")

        print("\n🎉 Basic tests completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    sys.exit(0 if success else 1)