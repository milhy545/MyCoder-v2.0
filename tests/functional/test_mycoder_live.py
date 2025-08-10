"""
Functional Tests for Enhanced MyCoder v2.0 Live Testing

These tests are designed to be run in a tmux session for interactive
verification of the complete MyCoder system functionality.

Run with: pytest tests/functional/test_mycoder_live.py -v -s --tb=short
Or: python tests/functional/test_mycoder_live.py
"""

import asyncio
import pytest
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Fix for relative imports when running as script
if __name__ == "__main__":
    import importlib.util
    
    # Load enhanced_mycoder_v2 module
    spec = importlib.util.spec_from_file_location(
        "enhanced_mycoder_v2", 
        Path(__file__).parent.parent.parent / "src" / "enhanced_mycoder_v2.py"
    )
    enhanced_mycoder_v2 = importlib.util.module_from_spec(spec)
    sys.modules["enhanced_mycoder_v2"] = enhanced_mycoder_v2
    spec.loader.exec_module(enhanced_mycoder_v2)
    
    # Load config_manager module
    spec = importlib.util.spec_from_file_location(
        "config_manager",
        Path(__file__).parent.parent.parent / "src" / "config_manager.py"
    )
    config_manager = importlib.util.module_from_spec(spec)
    sys.modules["config_manager"] = config_manager
    spec.loader.exec_module(config_manager)
    
    # Load api_providers module
    spec = importlib.util.spec_from_file_location(
        "api_providers",
        Path(__file__).parent.parent.parent / "src" / "api_providers.py"
    )
    api_providers = importlib.util.module_from_spec(spec)
    sys.modules["api_providers"] = api_providers
    spec.loader.exec_module(api_providers)
    
    EnhancedMyCoderV2 = enhanced_mycoder_v2.EnhancedMyCoderV2
    ConfigManager = config_manager.ConfigManager
    APIProviderType = api_providers.APIProviderType
else:
    from enhanced_mycoder_v2 import EnhancedMyCoderV2
    from config_manager import ConfigManager
    from api_providers import APIProviderType


class TestMyCoderLiveFunctionality:
    """Live functional tests for MyCoder system"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.working_dir = Path(self.temp_dir.name)
        
        # Create realistic test configuration
        self.config = {
            "claude_anthropic": {
                "enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
                "timeout_seconds": 30
            },
            "claude_oauth": {
                "enabled": True,
                "timeout_seconds": 45
            },
            "gemini": {
                "enabled": bool(os.getenv("GEMINI_API_KEY")),
                "timeout_seconds": 30
            },
            "ollama_local": {
                "enabled": True,
                "base_url": "http://localhost:11434",
                "model": "tinyllama",
                "timeout_seconds": 60
            },
            "thermal": {
                "enabled": True,
                "max_temp": 75,
                "check_interval": 30
            },
            "system": {
                "log_level": "INFO",
                "enable_tool_registry": True,
                "enable_mcp_integration": True
            },
            "debug_mode": True
        }
        
        print(f"\n🔧 Test setup complete. Working directory: {self.working_dir}")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.temp_dir.cleanup()
        print("🧹 Test cleanup complete.")
    
    @pytest.mark.asyncio
    async def test_system_initialization_live(self):
        """Test complete system initialization with live feedback"""
        print("\n" + "="*60)
        print("🚀 LIVE TEST: System Initialization")
        print("="*60)
        
        mycoder = EnhancedMyCoderV2(
            working_directory=self.working_dir,
            config=self.config
        )
        
        print("⏳ Initializing Enhanced MyCoder v2.0...")
        start_time = time.time()
        
        await mycoder.initialize()
        
        init_time = time.time() - start_time
        print(f"✅ Initialization completed in {init_time:.2f}s")
        
        # Verify initialization
        assert mycoder._initialized is True
        print("✅ System marked as initialized")
        
        assert mycoder.provider_router is not None
        print("✅ API provider router created")
        
        assert mycoder.tool_registry is not None
        print("✅ Tool registry configured")
        
        # Get system status
        print("\n📊 Getting system status...")
        status = await mycoder.get_system_status()
        
        print(f"📁 Working directory: {status['working_directory']}")
        print(f"🔄 Active sessions: {status['active_sessions']}")
        print(f"🛠️  Available tools: {status['tools']['total_tools']}")
        
        # Display provider status
        print("\n🌐 Provider Status:")
        for provider_name, provider_info in status['providers'].items():
            status_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unavailable': '❌',
                'error': '🔥'
            }.get(provider_info['status'], '❓')
            
            print(f"  {status_emoji} {provider_name}: {provider_info['status']}")
        
        # Display thermal status if available
        if status.get('thermal'):
            thermal = status['thermal']
            temp_emoji = '🟢' if thermal.get('safe_operation', True) else '🔥'
            print(f"\n🌡️  Thermal Status: {temp_emoji}")
            if 'cpu_temp' in thermal:
                print(f"  Temperature: {thermal['cpu_temp']}°C")
            print(f"  Safe operation: {thermal.get('safe_operation', 'unknown')}")
        
        print("\n✅ System initialization test completed successfully!")
        
        await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_basic_query_live(self):
        """Test basic query functionality with live providers"""
        print("\n" + "="*60)
        print("💬 LIVE TEST: Basic Query Functionality")
        print("="*60)
        
        mycoder = EnhancedMyCoderV2(
            working_directory=self.working_dir,
            config=self.config
        )
        
        await mycoder.initialize()
        
        # Test basic query
        print("🤔 Sending basic query...")
        test_query = "Hello! Can you respond with a brief greeting?"
        
        start_time = time.time()
        response = await mycoder.process_request(test_query)
        response_time = time.time() - start_time
        
        print(f"⏱️  Response time: {response_time:.2f}s")
        print(f"✅ Success: {response['success']}")
        print(f"🤖 Provider: {response.get('provider', 'unknown')}")
        print(f"💰 Cost: ${response.get('cost', 0):.6f}")
        
        if response['success']:
            print(f"📝 Response: {response['content'][:200]}...")
            if len(response['content']) > 200:
                print("    (truncated)")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
            
            # Show recovery suggestions
            if 'recovery_suggestions' in response:
                print("\n🔧 Recovery suggestions:")
                for suggestion in response['recovery_suggestions']:
                    print(f"  • {suggestion}")
        
        print("\n✅ Basic query test completed!")
        await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_file_operations_live(self):
        """Test file operations with real files"""
        print("\n" + "="*60)
        print("📁 LIVE TEST: File Operations")
        print("="*60)
        
        # Create test files
        test_files = []
        
        # Python file
        python_file = self.working_dir / "example.py"
        python_content = '''def hello_world():
    """A simple greeting function."""
    return "Hello, World from MyCoder!"

def calculate_fibonacci(n):
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

if __name__ == "__main__":
    print(hello_world())
    print(f"Fibonacci(10) = {calculate_fibonacci(10)}")
'''
        python_file.write_text(python_content)
        test_files.append(python_file)
        
        # JSON configuration file
        json_file = self.working_dir / "config.json"
        json_content = '''{
    "app_name": "MyCoder Test App",
    "version": "2.0.0",
    "settings": {
        "debug": true,
        "max_connections": 100,
        "timeout": 30
    },
    "features": ["multi_api", "thermal_management", "tool_registry"]
}'''
        json_file.write_text(json_content)
        test_files.append(json_file)
        
        # Markdown documentation
        md_file = self.working_dir / "README.md"
        md_content = '''# MyCoder v2.0 Test Project

This is a test project for MyCoder v2.0 functionality.

## Features

- Multi-API provider support
- Thermal management for Q9550
- FEI-inspired architecture
- Comprehensive testing

## Usage

```python
from mycoder import EnhancedMyCoderV2
mycoder = EnhancedMyCoderV2()
await mycoder.initialize()
```

## Files

- `example.py` - Python code example
- `config.json` - Configuration file
- `README.md` - This documentation
'''
        md_file.write_text(md_content)
        test_files.append(md_file)
        
        print(f"📝 Created {len(test_files)} test files:")
        for file in test_files:
            print(f"  • {file.name} ({file.stat().st_size} bytes)")
        
        # Initialize MyCoder
        mycoder = EnhancedMyCoderV2(
            working_directory=self.working_dir,
            config=self.config
        )
        
        await mycoder.initialize()
        
        # Test file analysis
        print("\n🔍 Analyzing files with MyCoder...")
        query = """Please analyze these files and provide:
1. A brief summary of what each file contains
2. Any potential improvements you notice
3. How these files work together as a project"""
        
        response = await mycoder.process_request(
            query,
            files=test_files,
            session_id="file_analysis_session"
        )
        
        print(f"✅ Analysis success: {response['success']}")
        print(f"🤖 Provider used: {response.get('provider', 'unknown')}")
        
        if response['success']:
            print(f"\n📄 File Analysis Result:")
            print("-" * 40)
            print(response['content'])
            print("-" * 40)
        else:
            print(f"❌ Analysis failed: {response.get('error', 'Unknown error')}")
        
        # Test file-specific query
        print("\n🔍 Testing file-specific query...")
        specific_query = "Can you explain the fibonacci function in the Python file and suggest an optimization?"
        
        response2 = await mycoder.process_request(
            specific_query,
            files=[python_file],
            session_id="file_analysis_session",
            continue_session=True
        )
        
        if response2['success']:
            print(f"\n🐍 Python Analysis Result:")
            print("-" * 40)
            print(response2['content'])
            print("-" * 40)
        else:
            print(f"❌ Python analysis failed: {response2.get('error')}")
        
        print("\n✅ File operations test completed!")
        await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_session_management_live(self):
        """Test session management and continuity"""
        print("\n" + "="*60)
        print("🔄 LIVE TEST: Session Management")
        print("="*60)
        
        mycoder = EnhancedMyCoderV2(
            working_directory=self.working_dir,
            config=self.config
        )
        
        await mycoder.initialize()
        
        session_id = f"test_session_{int(time.time())}"
        print(f"🆔 Using session ID: {session_id}")
        
        # First message in session
        print("\n1️⃣ Starting conversation...")
        response1 = await mycoder.process_request(
            "Hello! I'm starting a conversation about Python development. Can you remember this context?",
            session_id=session_id
        )
        
        print(f"✅ Message 1: {response1['success']}")
        if response1['success']:
            print(f"   Response preview: {response1['content'][:100]}...")
        
        # Second message continuing session
        print("\n2️⃣ Continuing conversation...")
        response2 = await mycoder.process_request(
            "Based on our previous discussion about Python development, can you suggest some best practices?",
            session_id=session_id,
            continue_session=True
        )
        
        print(f"✅ Message 2: {response2['success']}")
        if response2['success']:
            print(f"   Response preview: {response2['content'][:100]}...")
        
        # Third message with context switch
        print("\n3️⃣ Switching topics within session...")
        response3 = await mycoder.process_request(
            "Now let's switch topics. What can you tell me about thermal management in computers?",
            session_id=session_id,
            continue_session=True
        )
        
        print(f"✅ Message 3: {response3['success']}")
        if response3['success']:
            print(f"   Response preview: {response3['content'][:100]}...")
        
        # Check session storage
        if session_id in mycoder.session_store:
            session_data = mycoder.session_store[session_id]
            print(f"\n📊 Session Statistics:")
            print(f"  • Total interactions: {session_data['total_interactions']}")
            print(f"  • Last provider: {session_data['last_response']['provider']}")
            print(f"  • Session mode: {session_data.get('mode', 'unknown')}")
            
            if 'thermal_status' in session_data:
                thermal = session_data['thermal_status']
                if thermal and 'cpu_temp' in thermal:
                    print(f"  • Last thermal reading: {thermal['cpu_temp']}°C")
        
        print("\n✅ Session management test completed!")
        await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_provider_fallback_live(self):
        """Test provider fallback in realistic scenarios"""
        print("\n" + "="*60)
        print("🔄 LIVE TEST: Provider Fallback Chain")
        print("="*60)
        
        # Create config with multiple providers
        fallback_config = self.config.copy()
        fallback_config["claude_anthropic"]["enabled"] = False  # Force fallback
        fallback_config["gemini"]["enabled"] = False  # Force fallback
        
        mycoder = EnhancedMyCoderV2(
            working_directory=self.working_dir,
            config=fallback_config
        )
        
        await mycoder.initialize()
        
        # Get available providers
        status = await mycoder.get_system_status()
        available_providers = [name for name, info in status['providers'].items() 
                             if info['status'] in ['healthy', 'degraded']]
        
        print(f"🌐 Available providers: {', '.join(available_providers)}")
        
        # Test multiple requests to see provider selection
        queries = [
            "What is Python?",
            "How does machine learning work?",
            "Explain quantum computing briefly.",
            "What are the benefits of open source software?"
        ]
        
        print(f"\n🧪 Testing {len(queries)} queries to observe provider behavior...")
        
        for i, query in enumerate(queries, 1):
            print(f"\n{i}️⃣ Query: {query}")
            
            start_time = time.time()
            response = await mycoder.process_request(
                query,
                session_id="fallback_test_session"
            )
            duration = time.time() - start_time
            
            if response['success']:
                print(f"   ✅ Success ({duration:.2f}s)")
                print(f"   🤖 Provider: {response.get('provider', 'unknown')}")
                print(f"   📝 Response: {response['content'][:80]}...")
            else:
                print(f"   ❌ Failed ({duration:.2f}s)")
                print(f"   🚨 Error: {response.get('error', 'Unknown')}")
                
                # Test fallback to next provider
                if 'recovery_suggestions' in response:
                    print("   💡 Recovery suggestions available")
        
        print("\n✅ Provider fallback test completed!")
        await mycoder.shutdown()
    
    @pytest.mark.skipif(
        not Path("/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh").exists(),
        reason="Q9550 thermal system not available"
    )
    @pytest.mark.asyncio
    async def test_thermal_management_live(self):
        """Test thermal management integration with Q9550 system"""
        print("\n" + "="*60)
        print("🌡️ LIVE TEST: Q9550 Thermal Management")
        print("="*60)
        
        # Enable thermal management
        thermal_config = self.config.copy()
        thermal_config["thermal"]["enabled"] = True
        thermal_config["thermal"]["max_temp"] = 75
        
        mycoder = EnhancedMyCoderV2(
            working_directory=self.working_dir,
            config=thermal_config
        )
        
        await mycoder.initialize()
        
        # Check thermal status
        print("🌡️ Checking thermal status...")
        thermal_status = await mycoder._get_thermal_status()
        
        print(f"📊 Thermal Status:")
        print(f"  • Temperature: {thermal_status.get('cpu_temp', 'unknown')}°C")
        print(f"  • Status: {thermal_status.get('status', 'unknown')}")
        print(f"  • Safe operation: {thermal_status.get('safe_operation', 'unknown')}")
        
        # Test thermal-aware query
        print("\n🧠 Testing thermal-aware AI operation...")
        thermal_query = """Generate a detailed explanation of how neural networks work, 
        including backpropagation, gradient descent, and various activation functions. 
        Make it comprehensive but accessible."""
        
        start_time = time.time()
        response = await mycoder.process_request(
            thermal_query,
            session_id="thermal_test_session"
        )
        duration = time.time() - start_time
        
        print(f"⏱️ Operation completed in {duration:.2f}s")
        print(f"✅ Success: {response['success']}")
        print(f"🤖 Provider: {response.get('provider', 'unknown')}")
        
        if response['success']:
            print(f"📄 Response length: {len(response['content'])} characters")
            print(f"📝 Preview: {response['content'][:150]}...")
        else:
            print(f"❌ Error: {response.get('error')}")
            
            # Check if thermal limits caused failure
            if 'thermal' in response.get('error', '').lower():
                print("🔥 Operation blocked due to thermal limits")
                print("   This is expected behavior for Q9550 protection")
        
        # Check thermal status after operation
        print("\n🌡️ Post-operation thermal check...")
        post_thermal = await mycoder._get_thermal_status()
        
        if post_thermal.get('cpu_temp') and thermal_status.get('cpu_temp'):
            temp_change = post_thermal['cpu_temp'] - thermal_status['cpu_temp']
            print(f"🌡️ Temperature change: {temp_change:+.1f}°C")
        
        print("\n✅ Thermal management test completed!")
        await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_tool_registry_live(self):
        """Test tool registry functionality with real operations"""
        print("\n" + "="*60)
        print("🛠️ LIVE TEST: Tool Registry Operations")
        print("="*60)
        
        mycoder = EnhancedMyCoderV2(
            working_directory=self.working_dir,
            config=self.config
        )
        
        await mycoder.initialize()
        
        # Get tool registry stats
        registry_stats = mycoder.tool_registry.get_registry_stats()
        print(f"📊 Tool Registry Statistics:")
        print(f"  • Total tools: {registry_stats['total_tools']}")
        print(f"  • Categories: {list(registry_stats['categories'].keys())}")
        print(f"  • Total executions: {registry_stats['total_executions']}")
        
        # Test file operations through tool registry
        print("\n📁 Testing file operations...")
        
        # Create test file for operations
        test_file = self.working_dir / "tool_test.txt"
        test_content = f"Tool registry test file\nCreated at: {datetime.now()}\nMyCoder v2.0 functional test"
        
        from tool_registry import ToolExecutionContext
        context = ToolExecutionContext(
            mode="FULL",
            working_directory=self.working_dir,
            session_id="tool_test_session"
        )
        
        # Test file write
        print("✏️ Writing test file...")
        write_result = await mycoder.tool_registry.execute_tool(
            "file_write",
            context,
            operation="write",
            path="tool_test.txt",
            content=test_content
        )
        
        print(f"✅ Write result: {write_result.success}")
        if write_result.success:
            print(f"   📝 {write_result.data}")
        
        # Test file read
        print("📖 Reading test file...")
        read_result = await mycoder.tool_registry.execute_tool(
            "file_read",
            context,
            operation="read",
            path="tool_test.txt"
        )
        
        print(f"✅ Read result: {read_result.success}")
        if read_result.success:
            print(f"   📄 Content: {read_result.data[:100]}...")
        
        # Test file existence check
        print("🔍 Checking file existence...")
        exists_result = await mycoder.tool_registry.execute_tool(
            "file_read",
            context,
            operation="exists",
            path="tool_test.txt"
        )
        
        print(f"✅ Exists result: {exists_result.success}")
        if exists_result.success:
            print(f"   📂 File exists: {exists_result.data}")
        
        # Test directory listing
        print("📋 Listing directory contents...")
        list_result = await mycoder.tool_registry.execute_tool(
            "file_list",
            context,
            operation="list",
            path="."
        )
        
        print(f"✅ List result: {list_result.success}")
        if list_result.success:
            files = list_result.data
            print(f"   📁 Found {len(files)} items:")
            for file in files[:5]:  # Show first 5
                print(f"     • {Path(file).name}")
            if len(files) > 5:
                print(f"     ... and {len(files) - 5} more")
        
        print("\n✅ Tool registry test completed!")
        await mycoder.shutdown()
    
    @pytest.mark.asyncio
    async def test_performance_benchmark_live(self):
        """Test system performance with realistic workloads"""
        print("\n" + "="*60)
        print("⚡ LIVE TEST: Performance Benchmark")
        print("="*60)
        
        mycoder = EnhancedMyCoderV2(
            working_directory=self.working_dir,
            config=self.config
        )
        
        await mycoder.initialize()
        
        # Performance test scenarios
        test_scenarios = [
            {
                "name": "Quick Response",
                "query": "What is 2 + 2?",
                "expected_time": 5.0
            },
            {
                "name": "Code Analysis",
                "query": "Explain what this code does: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
                "expected_time": 10.0
            },
            {
                "name": "Complex Explanation",
                "query": "Explain the difference between supervised and unsupervised machine learning with examples.",
                "expected_time": 15.0
            }
        ]
        
        results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}️⃣ Testing: {scenario['name']}")
            print(f"   Query: {scenario['query'][:60]}...")
            print(f"   Expected time: <{scenario['expected_time']}s")
            
            start_time = time.time()
            response = await mycoder.process_request(
                scenario['query'],
                session_id=f"perf_test_{i}"
            )
            duration = time.time() - start_time
            
            result = {
                "name": scenario['name'],
                "duration": duration,
                "success": response['success'],
                "provider": response.get('provider', 'unknown'),
                "within_expected": duration <= scenario['expected_time']
            }
            results.append(result)
            
            status_emoji = "✅" if result['success'] and result['within_expected'] else "⚠️"
            print(f"   {status_emoji} Result: {duration:.2f}s ({'✓' if result['within_expected'] else '✗'} expected)")
            print(f"   🤖 Provider: {result['provider']}")
            
            if not response['success']:
                print(f"   ❌ Error: {response.get('error')}")
        
        # Performance summary
        print(f"\n📊 Performance Summary:")
        successful = [r for r in results if r['success']]
        within_expected = [r for r in results if r['within_expected']]
        
        print(f"  • Successful requests: {len(successful)}/{len(results)}")
        print(f"  • Within expected time: {len(within_expected)}/{len(results)}")
        
        if successful:
            avg_time = sum(r['duration'] for r in successful) / len(successful)
            print(f"  • Average response time: {avg_time:.2f}s")
            
            fastest = min(successful, key=lambda x: x['duration'])
            slowest = max(successful, key=lambda x: x['duration'])
            print(f"  • Fastest: {fastest['name']} ({fastest['duration']:.2f}s)")
            print(f"  • Slowest: {slowest['name']} ({slowest['duration']:.2f}s)")
        
        print("\n✅ Performance benchmark completed!")
        await mycoder.shutdown()


def interactive_menu():
    """Interactive menu for running specific tests"""
    tests = {
        '1': ('System Initialization', 'test_system_initialization_live'),
        '2': ('Basic Query', 'test_basic_query_live'),
        '3': ('File Operations', 'test_file_operations_live'),
        '4': ('Session Management', 'test_session_management_live'),
        '5': ('Provider Fallback', 'test_provider_fallback_live'),
        '6': ('Thermal Management', 'test_thermal_management_live'),
        '7': ('Tool Registry', 'test_tool_registry_live'),
        '8': ('Performance Benchmark', 'test_performance_benchmark_live'),
        '9': ('Run All Tests', 'all')
    }
    
    print("\n" + "="*60)
    print("🧪 MyCoder v2.0 Live Functional Tests")
    print("="*60)
    print("Choose a test to run:")
    print()
    
    for key, (name, _) in tests.items():
        print(f"  {key}. {name}")
    
    print("\n  0. Exit")
    print("="*60)
    
    while True:
        choice = input("\nEnter your choice (0-9): ").strip()
        
        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice in tests:
            test_name, method_name = tests[choice]
            print(f"\n🚀 Running: {test_name}")
            
            if method_name == 'all':
                # Run all tests
                tester = TestMyCoderLiveFunctionality()
                for _, (_, method) in tests.items():
                    if method != 'all':
                        print(f"\n🔄 Executing {method}...")
                        tester.setup_method()
                        try:
                            asyncio.run(getattr(tester, method)())
                        finally:
                            tester.teardown_method()
            else:
                # Run specific test
                tester = TestMyCoderLiveFunctionality()
                tester.setup_method()
                try:
                    asyncio.run(getattr(tester, method_name)())
                finally:
                    tester.teardown_method()
        else:
            print("❌ Invalid choice. Please enter 0-9.")


if __name__ == "__main__":
    """Run interactive test menu when called directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MyCoder v2.0 Live Functional Tests")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    parser.add_argument("--test", "-t", type=str,
                       help="Run specific test method")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_menu()
    elif args.test:
        # Run specific test
        tester = TestMyCoderLiveFunctionality()
        tester.setup_method()
        try:
            if hasattr(tester, args.test):
                asyncio.run(getattr(tester, args.test)())
            else:
                print(f"❌ Test method '{args.test}' not found")
        finally:
            tester.teardown_method()
    else:
        print("🧪 MyCoder v2.0 Live Functional Tests")
        print("Use --interactive or -i for interactive mode")
        print("Use --test <method_name> to run specific test")
        print("Or run with pytest: pytest tests/functional/test_mycoder_live.py -v -s")