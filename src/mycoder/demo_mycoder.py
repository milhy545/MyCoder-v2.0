#!/usr/bin/env python3
"""
MyCoder Adaptive Modes Demo Script

This demo showcases the intelligent adaptive mode switching system that automatically
adapts to network conditions, resource availability, and service health.
"""

import asyncio
import time
from pathlib import Path

from . import MyCoder, OperationalMode


async def demo_basic_usage():
    """Demonstrate basic MyCoder usage with adaptive modes."""
    print("🎯 MyCoder Adaptive Modes Demo")
    print("=" * 50)

    # Initialize MyCoder - it will automatically detect the best mode
    mycoder = MyCoder(working_directory=Path.cwd())

    print("1️⃣  Initializing MyCoder...")
    await mycoder.initialize()

    # Show current status
    status = mycoder.get_status()
    print(f"   Current mode: {status['mode']}")
    print(
        f"   Health: Internet ✅, Orchestrator {'✅' if status['health']['orchestrator_available'] else '❌'}, Claude {'✅' if status['health']['claude_auth_working'] else '❌'}"
    )

    # Basic AI request
    print("\n2️⃣  Making AI request...")
    result = await mycoder.process_request(
        "Hello! Can you briefly explain what you are and what mode you're operating in?"
    )

    if result.get("success"):
        print(f"   ✅ Response from {result['source']}:")
        print(f"   {result['content'][:200]}...")
    else:
        print(f"   ℹ️  {result.get('content', 'Service response')}")

    # File analysis demo
    print("\n3️⃣  Creating test file for analysis...")
    test_file = Path("demo_file.py")
    test_file.write_text(
        """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# This could be optimized with memoization
result = calculate_fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""
    )

    result = await mycoder.process_request(
        "Analyze this Python code and suggest improvements", files=[test_file]
    )

    if result.get("success"):
        print(f"   ✅ File analysis completed in {result['duration_seconds']:.1f}s")
        print(f"   Mode: {result['mode']}, Source: {result.get('source', 'unknown')}")
    else:
        print(
            f"   ℹ️  Analysis result: {result.get('content', 'No analysis available')[:100]}..."
        )

    # Clean up
    test_file.unlink()

    print("\n4️⃣  System capabilities in current mode:")
    capabilities = mycoder.mode_manager.get_current_capabilities()
    print(f"   Claude Auth: {'✅' if capabilities.claude_auth else '❌'}")
    print(f"   MCP Tools: {len(capabilities.available_tools)} available")
    print(f"   Memory System: {capabilities.memory_system}")
    print(f"   Max Timeout: {capabilities.max_timeout}s")

    await mycoder.shutdown()
    print("\n✅ Demo completed!")


async def demo_mode_transitions():
    """Demonstrate adaptive mode transitions."""
    print("\n🔄 Mode Transition Demo")
    print("=" * 30)

    mycoder = MyCoder()
    await mycoder.initialize()

    # Show all possible modes
    modes = [
        OperationalMode.FULL,
        OperationalMode.DEGRADED,
        OperationalMode.AUTONOMOUS,
        OperationalMode.RECOVERY,
    ]

    for mode in modes:
        print(f"\n   Testing {mode.value} mode...")
        await mycoder.force_mode(mode, "demo testing")

        # Test capability in each mode
        result = await mycoder.process_request(f"Test in {mode.value} mode")
        source = result.get("source", "unknown")
        print(f"     Source: {source}")

        if result.get("success"):
            print(f"     ✅ Working: {result['content'][:50]}...")
        else:
            print(f"     ℹ️  Response: {result.get('content', 'No response')[:50]}...")

    # Show transition history
    status = mycoder.get_status()
    print(f"\n   Transitions made: {len(status.get('mode_history', []))}")

    await mycoder.shutdown()


async def demo_health_monitoring():
    """Demonstrate health monitoring and automatic adaptation."""
    print("\n📊 Health Monitoring Demo")
    print("=" * 30)

    mycoder = MyCoder()
    await mycoder.initialize()

    print("   Monitoring system health for 10 seconds...")
    start_time = time.time()

    while time.time() - start_time < 10:
        await asyncio.sleep(2)
        status = mycoder.get_status()
        health = status["health"]

        print(
            f"     Mode: {status['mode']}, "
            f"Internet: {'✅' if health['internet_stable'] else '❌'}, "
            f"Orchestrator: {'✅' if health['orchestrator_available'] else '❌'}, "
            f"Claude: {'✅' if health['claude_auth_working'] else '❌'}"
        )

    await mycoder.shutdown()
    print("   Health monitoring completed!")


async def main():
    """Run all demos."""
    try:
        await demo_basic_usage()
        await demo_mode_transitions()
        await demo_health_monitoring()

        print("\n🎉 All demos completed successfully!")
        print("\n📖 Key Features Demonstrated:")
        print("   • Automatic mode detection and switching")
        print("   • Graceful degradation when services unavailable")
        print("   • File analysis with context awareness")
        print("   • Health monitoring and adaptation")
        print("   • Session management and persistence")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
