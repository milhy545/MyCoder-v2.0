#!/usr/bin/env python3
"""
Enhanced MyCoder v2.1.0 - Thermal Management Example

This example demonstrates the Q9550 thermal management capabilities
of Enhanced MyCoder v2.1.0, including temperature monitoring,
throttling, and emergency protection.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mycoder import EnhancedMyCoderV2


async def thermal_monitoring_example():
    """Demonstrate thermal monitoring capabilities"""

    print("🌡️  Enhanced MyCoder v2.1.0 - Thermal Management")
    print("=" * 50)

    # Configuration with thermal management enabled
    config = {
        "claude_oauth": {"enabled": True},
        "ollama_local": {"enabled": True},
        "thermal": {
            "enabled": True,
            "max_temp": 75.0,  # Start throttling at 75°C
            "critical_temp": 85.0,  # Emergency shutdown at 85°C
            "check_interval": 10,  # Check every 10 seconds
            "throttle_threshold": 0.8,  # Throttle when above 80% of max
            "performance_script": "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh",
        },
    }

    print("🔧 Initializing with thermal management...")
    mycoder = EnhancedMyCoderV2(working_directory=Path("."), config=config)

    try:
        await mycoder.initialize()

        # Check initial thermal status
        print("\n🌡️  Initial Thermal Status:")
        status = await mycoder.get_system_status()

        if "thermal" in status:
            thermal = status["thermal"]
            print(f"   Current Temperature: {thermal.get('current_temp', 'N/A')}°C")
            print(f"   Max Temperature: {thermal.get('max_temp', 'N/A')}°C")
            print(f"   Critical Temperature: {thermal.get('critical_temp', 'N/A')}°C")
            print(f"   Safe Operation: {thermal.get('safe_operation', 'N/A')}")
            print(f"   Throttling Active: {thermal.get('throttling_active', 'N/A')}")
        else:
            print("   ⚠️  Thermal management not available (sensors not detected)")
            print("   This is normal on non-Q9550 systems or without lm-sensors")

        # Demonstrate thermal-aware processing
        print("\n🔥 Running thermal stress test...")

        # Simulate heavy workload requests
        heavy_requests = [
            "Analyze this large codebase and provide detailed architectural recommendations",
            "Generate comprehensive unit tests for a complex Python class with multiple inheritance",
            "Refactor this legacy code to use modern Python patterns and best practices",
            "Create detailed API documentation with examples for a REST service",
            "Optimize this algorithm for better performance and memory usage",
        ]

        for i, request in enumerate(heavy_requests, 1):
            print(f"\n📝 Processing request {i}/5...")
            print(f"   Request: {request[:50]}...")

            start_time = time.time()

            # Check temperature before request
            pre_status = await mycoder.get_system_status()
            pre_temp = pre_status.get("thermal", {}).get("current_temp", "N/A")

            response = await mycoder.process_request(request)

            end_time = time.time()
            duration = end_time - start_time

            # Check temperature after request
            post_status = await mycoder.get_system_status()
            post_temp = post_status.get("thermal", {}).get("current_temp", "N/A")

            if response["success"]:
                print(f"   ✅ Completed in {duration:.1f}s")
                print(f"   Provider: {response['provider']}")
                print(f"   Temperature: {pre_temp}°C → {post_temp}°C")

                # Check if throttling occurred
                thermal_info = post_status.get("thermal", {})
                if thermal_info.get("throttling_active"):
                    print(f"   🐌 Thermal throttling active!")

                # Check for thermal warnings
                if isinstance(post_temp, (int, float)) and post_temp > 80:
                    print(f"   ⚠️  High temperature warning!")

            else:
                print(f"   ❌ Failed: {response['error']}")

            # Brief pause between requests
            await asyncio.sleep(2)

        # Final thermal summary
        print("\n📊 Final Thermal Summary:")
        final_status = await mycoder.get_system_status()

        if "thermal" in final_status:
            thermal = final_status["thermal"]
            print(f"   Final Temperature: {thermal.get('current_temp', 'N/A')}°C")
            print(f"   Peak Temperature: {thermal.get('peak_temp', 'N/A')}°C")
            print(f"   Throttle Events: {thermal.get('throttle_events', 0)}")
            print(f"   Emergency Events: {thermal.get('emergency_events', 0)}")

            # Thermal history if available
            if hasattr(mycoder, "get_thermal_history"):
                try:
                    history = await mycoder.get_thermal_history()
                    print(
                        f"   Average Temp (last 10 min): {history.get('avg_temp_10m', 'N/A')}°C"
                    )
                    print(
                        f"   Time above 75°C: {history.get('time_above_max', 0):.1f}s"
                    )
                except Exception:
                    # History retrieval can fail if the manager doesn't support it.
                    pass

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\n🧹 Cleaning up...")
        await mycoder.shutdown()
        print("✅ Thermal management example complete")


async def thermal_configuration_example():
    """Show different thermal configuration options"""

    print("\n🔧 Thermal Configuration Examples")
    print("=" * 35)

    # Conservative configuration (for older systems)
    print("1. Conservative Configuration (Older Systems):")
    conservative_config = {
        "thermal": {
            "enabled": True,
            "max_temp": 65.0,  # Lower threshold
            "critical_temp": 75.0,  # Conservative critical temp
            "check_interval": 15,  # More frequent checks
            "throttle_threshold": 0.6,  # Earlier throttling
        }
    }
    print(json.dumps(conservative_config, indent=2))

    # Performance configuration (for robust systems)
    print("\n2. Performance Configuration (Robust Systems):")
    performance_config = {
        "thermal": {
            "enabled": True,
            "max_temp": 80.0,  # Higher threshold
            "critical_temp": 90.0,  # Higher critical temp
            "check_interval": 30,  # Less frequent checks
            "throttle_threshold": 0.9,  # Later throttling
        }
    }
    print(json.dumps(performance_config, indent=2))

    # Q9550-specific configuration
    print("\n3. Q9550-Specific Configuration:")
    q9550_config = {
        "thermal": {
            "enabled": True,
            "max_temp": 75.0,  # Q9550 safe operating temp
            "critical_temp": 85.0,  # Q9550 absolute maximum
            "check_interval": 20,  # Balanced monitoring
            "throttle_threshold": 0.8,  # Gradual throttling
            "performance_script": "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh",
        }
    }
    print(json.dumps(q9550_config, indent=2))

    # Disabled configuration (for containers/virtual environments)
    print("\n4. Disabled Configuration (Containers/VMs):")
    disabled_config = {
        "thermal": {"enabled": False, "reason": "Running in virtualized environment"}
    }
    print(json.dumps(disabled_config, indent=2))


async def thermal_emergency_example():
    """Demonstrate emergency thermal protection"""

    print("\n🚨 Emergency Thermal Protection Example")
    print("=" * 40)
    print("⚠️  This is a simulation - no actual overheating will occur")

    # Mock thermal manager for demonstration
    class MockThermalManager:
        def __init__(self):
            self.temp = 70.0
            self.emergency_triggered = False

        async def get_current_temperature(self):
            # Simulate rising temperature
            self.temp += 2.0
            return self.temp

        async def emergency_shutdown(self):
            self.emergency_triggered = True
            print("🚨 EMERGENCY THERMAL SHUTDOWN TRIGGERED!")
            print("   System would now:")
            print("   1. Stop all AI processing")
            print("   2. Save current session state")
            print("   3. Activate emergency cooling")
            print("   4. Wait for safe temperature")

    mock_thermal = MockThermalManager()

    print("\nSimulating temperature rise:")
    for step in range(10):
        temp = await mock_thermal.get_current_temperature()
        print(f"Step {step + 1}: Temperature: {temp:.1f}°C")

        if temp >= 85.0:
            await mock_thermal.emergency_shutdown()
            break
        elif temp >= 75.0:
            print("   🐌 Throttling would activate")

        await asyncio.sleep(0.5)

    print("\n✅ Emergency protection simulation complete")


async def thermal_integration_example():
    """Show integration with PowerManagement system"""

    print("\n🔌 PowerManagement Integration Example")
    print("=" * 40)

    # Check if PowerManagement scripts are available
    performance_script = Path(
        "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh"
    )

    if performance_script.exists():
        print("✅ PowerManagement integration available")

        # Configuration with PowerManagement integration
        config = {
            "claude_oauth": {"enabled": True},
            "thermal": {
                "enabled": True,
                "max_temp": 75.0,
                "critical_temp": 85.0,
                "performance_script": str(performance_script),
                "integration_mode": "active",
            },
        }

        print("\n🔧 Testing integrated thermal management...")

        mycoder = EnhancedMyCoderV2(working_directory=Path("."), config=config)

        try:
            await mycoder.initialize()

            # Test a request that should trigger thermal monitoring
            response = await mycoder.process_request(
                "Analyze system performance and suggest optimizations"
            )

            if response["success"]:
                print("✅ Integration test successful")

                # Check thermal status
                status = await mycoder.get_system_status()
                if "thermal" in status:
                    thermal = status["thermal"]
                    print(f"   Temperature: {thermal.get('current_temp', 'N/A')}°C")
                    print(f"   PowerManagement: {thermal.get('pm_integration', 'N/A')}")

        finally:
            await mycoder.shutdown()

    else:
        print("⚠️  PowerManagement scripts not found")
        print("   This is normal if not running on the Q9550 development system")
        print(f"   Looking for: {performance_script}")


def main():
    """Main entry point with different thermal examples"""

    if len(sys.argv) > 1:
        example_type = sys.argv[1]
        if example_type == "config":
            asyncio.run(thermal_configuration_example())
        elif example_type == "emergency":
            asyncio.run(thermal_emergency_example())
        elif example_type == "integration":
            asyncio.run(thermal_integration_example())
        else:
            print(f"Unknown example type: {example_type}")
            print("Available types: config, emergency, integration")
    else:
        # Run main thermal monitoring example
        asyncio.run(thermal_monitoring_example())


if __name__ == "__main__":
    main()
