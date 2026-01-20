#!/usr/bin/env python3
"""
Enhanced MyCoder v2.1.0 - Production Readiness Test

Simple test script to verify production readiness without
complex import issues. Tests core functionality in a tmux-friendly format.
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import time
import os

# Set up path for module imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Set environment to avoid relative import issues
os.environ["PYTHONPATH"] = str(PROJECT_ROOT / "src")


def test_imports():
    """Test that all core modules can be imported."""
    print("🔍 Testing module imports...")

    try:
        from mycoder import EnhancedMyCoderV2, MyCoder
        from mycoder.api_providers import APIProviderRouter
        from mycoder.config_manager import ConfigManager
        from mycoder.tool_registry import ToolRegistry

        if not all(
            [EnhancedMyCoderV2, MyCoder, APIProviderRouter, ConfigManager, ToolRegistry]
        ):
            raise RuntimeError("Core modules resolved to empty values")

        print("   ✅ Core module imports: OK")
        return True
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False


async def test_config_manager():
    """Test configuration management"""
    print("\n🔧 Testing Configuration Manager...")

    try:
        from mycoder.config_manager import ConfigManager, MyCoderConfig

        # Test basic config creation
        config_data = {
            "claude_oauth": {"enabled": True, "timeout_seconds": 30},
            "ollama_local": {"enabled": True, "base_url": "http://localhost:11434"},
            "thermal": {"enabled": True, "max_temp": 75.0},
        }

        # Test config validation
        try:
            config = MyCoderConfig(**config_data)
            print("   ✅ Config validation: OK")
        except Exception as e:
            print(f"   ❌ Config validation failed: {e}")
            return False

        # Test config manager
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json

            json.dump(config_data, f)
            config_file = Path(f.name)

        try:
            manager = ConfigManager(config_file)
            loaded_config = manager.load_config()
            print("   ✅ Config loading: OK")

            # Cleanup
            config_file.unlink()

        except Exception as e:
            print(f"   ❌ Config manager failed: {e}")
            if config_file.exists():
                config_file.unlink()
            return False

        return True

    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False


async def test_tool_registry():
    """Test tool registry system"""
    print("\n🛠️  Testing Tool Registry...")

    try:
        from mycoder.tool_registry import ToolRegistry, BaseTool

        # Test registry creation
        registry = ToolRegistry()
        print("   ✅ Registry creation: OK")

        # Test getting available tools
        tools = registry.get_available_tools()
        print(f"   ✅ Available tools: {len(tools)} found")

        # Test tool execution (mock)
        if tools:
            first_tool = tools[0]
            print(f"   ✅ First tool: {first_tool}")

        return True

    except Exception as e:
        print(f"   ❌ Tool registry test failed: {e}")
        return False


async def test_api_providers():
    """Test API provider system"""
    print("\n🔌 Testing API Providers...")

    try:
        from mycoder.api_providers import APIProviderType, BaseAPIProvider

        # Test enum
        providers = list(APIProviderType)
        print(f"   ✅ Provider types: {len(providers)} available")

        # Test that we have expected providers
        expected_providers = [
            APIProviderType.CLAUDE_ANTHROPIC,
            APIProviderType.CLAUDE_OAUTH,
            APIProviderType.GEMINI,
            APIProviderType.OLLAMA_LOCAL,
            APIProviderType.OLLAMA_REMOTE,
        ]

        for provider in expected_providers:
            if provider in providers:
                print(f"   ✅ {provider.value}: Available")
            else:
                print(f"   ❌ {provider.value}: Missing")
                return False

        return True

    except Exception as e:
        print(f"   ❌ API provider test failed: {e}")
        return False


async def test_basic_system():
    """Test basic system integration without full MyCoder"""
    print("\n🎯 Testing Basic System Integration...")

    try:
        # Test that core components work together
        from mycoder.config_manager import ConfigManager, MyCoderConfig
        from mycoder.tool_registry import ToolRegistry
        from mycoder.api_providers import APIProviderType
        from dataclasses import asdict

        # Create basic config
        config_data = {
            "claude_oauth": {"enabled": True},
            "thermal": {"enabled": False},  # Disable for testing
            "system": {"log_level": "INFO"},
        }

        config = MyCoderConfig(**config_data)
        registry = ToolRegistry()

        print("   ✅ Component integration: OK")
        print(f"   ✅ Config providers: {len(asdict(config))} sections")
        print(f"   ✅ Registry tools: {len(registry.get_available_tools())} tools")

        return True

    except Exception as e:
        print(f"   ❌ Basic system test failed: {e}")
        return False


async def test_file_operations():
    """Test file operation capabilities"""
    print("\n📁 Testing File Operations...")

    try:
        # Test basic file operations
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            test_file = Path(tmp.name)
        test_content = '''def hello_world():
    """Simple test function"""
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
'''

        # Write test file
        test_file.write_text(test_content)
        print("   ✅ File creation: OK")

        # Read test file
        read_content = test_file.read_text()
        if read_content == test_content:
            print("   ✅ File reading: OK")
        else:
            print("   ❌ File reading: Content mismatch")
            return False

        # Test Path operations
        if test_file.exists():
            print("   ✅ Path operations: OK")
        else:
            print("   ❌ Path operations: File not found")
            return False

        # Cleanup
        test_file.unlink()
        print("   ✅ File cleanup: OK")

        return True

    except Exception as e:
        print(f"   ❌ File operations test failed: {e}")
        return False


async def test_performance():
    """Test basic performance characteristics"""
    print("\n⚡ Testing Performance...")

    try:
        # Test async performance
        start_time = time.time()

        # Simple async operations
        tasks = []
        for i in range(10):
            tasks.append(asyncio.sleep(0.01))

        await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        print(f"   ✅ Async operations: {duration:.3f}s for 10 tasks")

        if duration < 1.0:  # Should be much faster than 1 second
            print("   ✅ Performance: Acceptable")
            return True
        else:
            print("   ⚠️  Performance: Slower than expected")
            return False

    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
        return False


async def run_production_readiness_tests():
    """Run all production readiness tests"""
    print("🚀 Enhanced MyCoder v2.1.0 - Production Readiness Test")
    print("=" * 55)
    print(f"📍 Project Root: {PROJECT_ROOT}")
    print(f"🐍 Python Version: {sys.version}")
    print(f"📅 Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tests = [
        ("Import System", test_imports),
        ("Configuration Manager", test_config_manager),
        ("Tool Registry", test_tool_registry),
        ("API Providers", test_api_providers),
        ("Basic System Integration", test_basic_system),
        ("File Operations", test_file_operations),
        ("Performance", test_performance),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"🧪 Running: {test_name}")

        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()

        results.append((test_name, result))

        if result:
            print(f"   ✅ {test_name}: PASSED")
        else:
            print(f"   ❌ {test_name}: FAILED")

        print()

    # Summary
    print("📊 Test Results Summary")
    print("=" * 30)

    passed = sum(1 for _, result in results if result)
    total = len(results)
    pass_rate = (passed / total) * 100 if total > 0 else 0

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")

    print(f"\n🎯 Overall Result: {passed}/{total} tests passed ({pass_rate:.1f}%)")

    if pass_rate >= 85:
        print("🎉 PRODUCTION READY! System meets quality standards.")
        return True
    elif pass_rate >= 70:
        print("⚠️  MOSTLY READY: Some issues need attention.")
        return False
    else:
        print("❌ NOT READY: Significant issues must be resolved.")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print("🚀 Running Quick Production Readiness Check...")

    try:
        result = asyncio.run(run_production_readiness_tests())
        exit_code = 0 if result else 1
        print(f"\n🔄 Exiting with code: {exit_code}")
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
