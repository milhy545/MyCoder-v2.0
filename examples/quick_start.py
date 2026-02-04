#!/usr/bin/env python3
"""
Enhanced MyCoder v2.1.0 - Quick Start Example

This example demonstrates basic usage of Enhanced MyCoder v2.1.0
with the 5-tier API provider fallback system.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mycoder import EnhancedMyCoderV2
from mycoder.config_manager import ConfigManager


async def quick_start_example():
    """Basic usage example of Enhanced MyCoder v2.1.0"""

    print("🚀 Enhanced MyCoder v2.1.0 - Quick Start")
    print("=" * 50)

    # Basic configuration
    config = {
        "claude_oauth": {"enabled": True, "timeout_seconds": 30},
        "ollama_local": {
            "enabled": True,
            "base_url": "http://localhost:11434",
            "model": "tinyllama",
            "timeout_seconds": 60,
        },
        "thermal": {"enabled": True, "max_temp": 75.0, "critical_temp": 85.0},
        "system": {"log_level": "INFO", "enable_tool_registry": True},
    }

    # Initialize MyCoder
    print("🔧 Initializing Enhanced MyCoder v2.1.0...")
    mycoder = EnhancedMyCoderV2(working_directory=Path("."), config=config)

    try:
        # Initialize the system
        await mycoder.initialize()
        print("✅ MyCoder initialized successfully!")

        # Get system status
        print("\n📊 System Status:")
        status = await mycoder.get_system_status()
        print(f"   Status: {status['status']}")
        print(f"   Available Providers: {len(status['providers'])}")

        # Show provider status
        print("\n🔌 Provider Status:")
        for provider, info in status["providers"].items():
            status_icon = "✅" if info["status"] == "healthy" else "❌"
            print(f"   {status_icon} {provider}: {info['status']}")

        # Test basic query
        print("\n💬 Testing Basic Query...")
        response = await mycoder.process_request(
            "Hello! Can you tell me the current date and time?"
        )

        if response["success"]:
            print(f"✅ Response: {response['content']}")
            print(f"   Provider used: {response['provider']}")
            print(f"   Cost: ${response['cost']:.4f}")
        else:
            print(f"❌ Request failed: {response['error']}")

        # Test file analysis
        print("\n📄 Testing File Analysis...")

        # Create a sample Python file
        sample_file = Path("sample_code.py")
        sample_code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""
        sample_file.write_text(sample_code)

        try:
            response = await mycoder.process_request(
                "Analyze this Python code and suggest improvements", files=[sample_file]
            )

            if response["success"]:
                print("✅ File analysis successful!")
                print(f"   Analysis: {response['content'][:200]}...")
                print(f"   Provider used: {response['provider']}")
            else:
                print(f"❌ File analysis failed: {response['error']}")

        finally:
            # Clean up sample file
            if sample_file.exists():
                sample_file.unlink()

        # Test session management
        print("\n🔄 Testing Session Management...")
        session_id = "quick_start_session"

        # First message in session
        response1 = await mycoder.process_request(
            "Remember: I'm working on a Python project about data analysis",
            session_id=session_id,
        )

        # Continue session
        response2 = await mycoder.process_request(
            "What did I tell you I was working on?",
            session_id=session_id,
            continue_session=True,
        )

        if response1["success"] and response2["success"]:
            print("✅ Session management working!")
            print(f"   Session ID: {response1['session_id']}")
            print(
                f"   Context maintained: {'data analysis' in response2['content'].lower()}"
            )
        else:
            print("❌ Session management test failed")

        # Show final statistics
        print("\n📈 Final Statistics:")
        final_status = await mycoder.get_system_status()
        print(f"   Active Sessions: {final_status['active_sessions']}")
        print(f"   Total Requests: {final_status.get('total_requests', 'N/A')}")

        if "thermal" in final_status:
            thermal = final_status["thermal"]
            print(f"   Current Temperature: {thermal.get('current_temp', 'N/A')}°C")
            print(f"   Thermal Status: {thermal.get('status', 'N/A')}")

        print("\n🎉 Quick start example completed successfully!")

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Always clean up
        print("\n🧹 Cleaning up...")
        await mycoder.shutdown()
        print("✅ MyCoder shutdown complete")


async def configuration_example():
    """Example showing different configuration methods"""

    print("\n🔧 Configuration Examples")
    print("=" * 30)

    # Method 1: Direct configuration
    print("Method 1: Direct Configuration")
    config1 = {"claude_oauth": {"enabled": True}, "thermal": {"enabled": False}}
    print(f"   Temporary config sections: {len(config1)}")

    # Method 2: Environment variables
    print("Method 2: Environment Variables")
    os.environ["MYCODER_PREFERRED_PROVIDER"] = "claude_oauth"
    os.environ["MYCODER_DEBUG"] = "1"

    # Method 3: Configuration file (if exists)
    config_file = Path("mycoder_config.json")
    if config_file.exists():
        print("Method 3: Configuration File Found")
        config_manager = ConfigManager(str(config_file))
        file_config = config_manager.load_config()
        print(f"   Loaded config with {len(file_config.dict())} sections")
    else:
        print("Method 3: No configuration file found (using defaults)")

    print("✅ Configuration examples complete")


async def error_handling_example():
    """Example showing error handling patterns"""

    print("\n🚨 Error Handling Examples")
    print("=" * 32)

    # Configure with potentially failing providers
    config = {
        "claude_anthropic": {"enabled": False},  # Disabled
        "claude_oauth": {"enabled": True},
        "ollama_local": {"enabled": True},
    }

    mycoder = EnhancedMyCoderV2(working_directory=Path("."), config=config)

    try:
        await mycoder.initialize()

        # Test with fallback
        print("Testing provider fallback...")
        response = await mycoder.process_request(
            "Simple test request",
            preferred_provider="claude_anthropic",  # This should fail and fall back
        )

        if response["success"]:
            print(f"✅ Fallback successful! Used: {response['provider']}")
        else:
            print(f"❌ Even fallback failed: {response['error']}")

        # Test error recovery
        print("Testing error recovery...")
        for attempt in range(3):
            try:
                response = await mycoder.process_request("Test request")
                if response["success"]:
                    print(f"✅ Success on attempt {attempt + 1}")
                    break
                else:
                    print(f"⚠️  Attempt {attempt + 1} failed, retrying...")
            except Exception as e:
                print(f"⚠️  Attempt {attempt + 1} error: {e}")

            if attempt < 2:
                await asyncio.sleep(1)  # Wait before retry

    finally:
        await mycoder.shutdown()

    print("✅ Error handling examples complete")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        example_type = sys.argv[1]
        if example_type == "config":
            asyncio.run(configuration_example())
        elif example_type == "errors":
            asyncio.run(error_handling_example())
        else:
            print(f"Unknown example type: {example_type}")
            print("Available types: config, errors")
    else:
        asyncio.run(quick_start_example())


if __name__ == "__main__":
    main()
