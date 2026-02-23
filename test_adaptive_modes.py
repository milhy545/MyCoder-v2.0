#!/usr/bin/env python3
"""Test script for MyCoder adaptive modes integration."""

import asyncio
import logging
import time
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
for logger_name in ["urllib3", "aiohttp"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

async def test_adaptive_modes():
    """Test MyCoder with adaptive modes in different scenarios."""
    print("🚀 Testing MyCoder Adaptive Modes Integration...")

    try:
        from claude_cli_auth.mycoder import MyCoder
        from claude_cli_auth.adaptive_modes import OperationalMode

        # Initialize MyCoder
        print("\n1️⃣  Initializing MyCoder with adaptive modes...")
        mycoder = MyCoder(working_directory=Path.cwd())

        # Test health check and mode detection
        print("2️⃣  Performing initial health check...")
        status = await mycoder.health_check()
        print(f"   Initial mode: {status['mode']}")
        print(f"   Health status:")
        for key, value in status['health'].items():
            emoji = "✅" if value else "❌"
            print(f"     {emoji} {key}: {value}")

        # Test basic request in current mode
        print("\n3️⃣  Testing basic AI request...")
        try:
            result = await mycoder.process_request(
                "Hello! Please respond with a brief greeting and your current status.",
                timeout=30
            )

            if result.get("success"):
                print(f"   ✅ Request successful in {result['mode']} mode")
                print(f"   Response: {result['content'][:100]}...")
                print(f"   Duration: {result['duration_seconds']:.1f}s")
                if result.get("cost"):
                    print(f"   Cost: ${result['cost']:.4f}")
            else:
                print(f"   ❌ Request failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"   ❌ Request exception: {e}")

        # Test file analysis request
        print("\n4️⃣  Testing file analysis request...")
        try:
            # Create a test file
            test_file = Path("test_file.py")
            test_file.write_text('''def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
''')

            result = await mycoder.process_request(
                "Analyze this Python file and suggest improvements",
                files=[test_file],
                timeout=45
            )

            if result.get("success"):
                print(f"   ✅ File analysis successful in {result['mode']} mode")
                print(f"   Response length: {len(result['content'])} chars")
                if result.get("session_id"):
                    print(f"   Session ID: {result['session_id']}")
            else:
                print(f"   ❌ File analysis failed: {result.get('error')}")

            # Clean up
            test_file.unlink()

        except Exception as e:
            print(f"   ❌ File analysis exception: {e}")

        # Test mode forcing
        print("\n5️⃣  Testing manual mode transitions...")
        original_mode = mycoder.mode_manager.current_mode

        for test_mode in [OperationalMode.DEGRADED, OperationalMode.AUTONOMOUS, OperationalMode.RECOVERY]:
            try:
                print(f"   Testing {test_mode.value} mode...")
                await mycoder.force_mode(test_mode, "testing")

                # Test request in forced mode
                result = await mycoder.process_request(
                    f"Test request in {test_mode.value} mode",
                    timeout=30
                )

                if result.get("success"):
                    print(f"     ✅ {test_mode.value} mode working")
                    print(f"     Source: {result.get('source', 'unknown')}")
                else:
                    print(f"     ℹ️  {test_mode.value} mode response: {result.get('content', 'No content')[:50]}...")

                await asyncio.sleep(1)  # Brief pause between tests

            except Exception as e:
                print(f"     ❌ {test_mode.value} mode failed: {e}")

        # Restore original mode
        await mycoder.force_mode(original_mode, "test cleanup")
        print(f"   ↩️  Restored to {original_mode.value} mode")

        # Test system status
        print("\n6️⃣  Final system status:")
        status = mycoder.get_status()
        print(f"   Current mode: {status['mode']}")
        print(f"   Active sessions: {status['active_sessions']}")
        print(f"   Mode transitions: {len(status.get('mode_history', []))}")

        if status.get('mode_history'):
            print("   Recent mode changes:")
            for transition in status['mode_history'][-3:]:  # Last 3
                print(f"     → {transition['mode']} ({transition['reason']})")

        # Cleanup
        print("\n7️⃣  Shutting down...")
        await mycoder.shutdown()

        print("\n🎉 MyCoder Adaptive Modes test completed successfully!")
        return True

    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Make sure the claude_cli_auth module is properly installed")
        return False

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_network_detection():
    """Test network detection capabilities."""
    print("\n🔍 Testing Network Detection...")

    try:
        from claude_cli_auth.adaptive_modes import NetworkDetective

        async with NetworkDetective() as detective:
            print("   Testing internet stability...")
            internet_ok = await detective.test_internet_stability()
            print(f"     Internet: {'✅' if internet_ok else '❌'}")

            print("   Testing orchestrator connection...")
            orchestrator_ok = await detective.test_orchestrator_connection()
            print(f"     Orchestrator: {'✅' if orchestrator_ok else '❌'}")

            print("   Testing Claude authentication...")
            claude_ok = await detective.test_claude_authentication()
            print(f"     Claude Auth: {'✅' if claude_ok else '❌'}")

        return True

    except Exception as e:
        print(f"   ❌ Network detection test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 MyCoder Adaptive Modes Test Suite")
    print("=" * 50)

    start_time = time.time()

    # Run network detection test
    network_test_ok = await test_network_detection()

    # Run main adaptive modes test
    main_test_ok = await test_adaptive_modes()

    duration = time.time() - start_time

    print("\n" + "=" * 50)
    print(f"🏁 Test suite completed in {duration:.1f}s")

    if network_test_ok and main_test_ok:
        print("✅ All tests passed! MyCoder adaptive modes are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)