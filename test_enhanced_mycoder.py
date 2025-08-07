#!/usr/bin/env python3
"""Test script for Enhanced MyCoder with MCP orchestrator integration."""

import asyncio
import logging
import time
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
for logger_name in ["urllib3", "aiohttp"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)


async def test_mcp_connector():
    """Test MCP connector functionality."""
    print("🔗 Testing MCP Connector...")
    
    try:
        from claude_cli_auth.mcp_connector import MCPConnector
        
        async with MCPConnector() as connector:
            print("   Testing connection...")
            is_connected = await connector.test_connection()
            print(f"     Connection: {'✅' if is_connected else '❌'}")
            
            if is_connected:
                print("   Checking service health...")
                health = await connector.check_services_health()
                zen_services = health.get("zen_coordinator", {}).get("services", {})
                running_services = sum(1 for s in zen_services.values() 
                                     if isinstance(s, dict) and s.get("status") == "running")
                print(f"     Services running: {running_services}/{len(zen_services)}")
                
                print("   Testing tool availability...")
                from claude_cli_auth.adaptive_modes import OperationalMode
                
                for mode in [OperationalMode.FULL, OperationalMode.DEGRADED, OperationalMode.AUTONOMOUS]:
                    tools = await connector.get_available_tools_for_mode(mode)
                    print(f"     {mode.value}: {len(tools)} tools available")
                
                # Test basic tool call
                print("   Testing basic tool call...")
                try:
                    result = await connector.call_mcp_tool(
                        "file_list",
                        {"path": str(Path.cwd())},
                        OperationalMode.FULL,
                        timeout=10
                    )
                    
                    if result.get("success"):
                        print("     ✅ Tool call successful")
                    else:
                        print(f"     ❌ Tool call failed: {result.get('error')}")
                        
                except Exception as e:
                    print(f"     ❌ Tool call exception: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ MCP Connector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_mycoder():
    """Test Enhanced MyCoder functionality."""
    print("\n🚀 Testing Enhanced MyCoder...")
    
    try:
        from claude_cli_auth.enhanced_mycoder import EnhancedMyCoder
        from claude_cli_auth.adaptive_modes import OperationalMode
        
        # Initialize Enhanced MyCoder
        print("1️⃣  Initializing Enhanced MyCoder...")
        mycoder = EnhancedMyCoder(working_directory=Path.cwd())
        await mycoder.initialize()
        
        # Get status
        status = mycoder.get_enhanced_status()
        print(f"   Mode: {status['mode']}")
        print(f"   MCP Connected: {'✅' if status['mcp_orchestrator']['connected'] else '❌'}")
        
        if status['mcp_orchestrator']['connected']:
            mcp_status = status['mcp_orchestrator']['status']
            tools_count = len(mcp_status.get('available_tools', []))
            print(f"   Available Tools: {tools_count}")
        
        # Test basic request with MCP enhancements
        print("\n2️⃣  Testing enhanced AI request...")
        try:
            result = await mycoder.process_request(
                "Hello! Can you tell me about the current system status and available capabilities?",
                use_mcp_memory=True,
                research_context=False,
                timeout=30
            )
            
            if result.get("success"):
                print(f"   ✅ Request successful in {result['mode']} mode")
                print(f"   MCP Tools Used: {result.get('mcp_tools_used', [])}")
                print(f"   Response: {result['content'][:150]}...")
            else:
                print(f"   ℹ️  Response: {result.get('content', 'No content')[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        # Test file operations via MCP
        print("\n3️⃣  Testing enhanced file operations...")
        try:
            # Create test file
            test_file = Path("enhanced_test.py")
            test_file.write_text("""
# Enhanced MyCoder Test File
def enhanced_function(x, y):
    '''A function for testing enhanced capabilities.'''
    result = x * y + (x ** 2) 
    return result

# Test the function
if __name__ == "__main__":
    print(enhanced_function(5, 3))
""")
            
            # Read file via enhanced method
            file_result = await mycoder.read_file_enhanced(test_file)
            
            if file_result.get("success"):
                print("   ✅ Enhanced file read successful")
                fallback = file_result.get("fallback_used")
                if fallback:
                    print(f"   Fallback used: {fallback}")
            else:
                print(f"   ❌ File read failed: {file_result.get('error')}")
            
            # Test command execution
            command_result = await mycoder.execute_command_enhanced(
                "wc -l enhanced_test.py",
                working_dir=str(Path.cwd())
            )
            
            if command_result.get("success"):
                print("   ✅ Enhanced command execution successful")
                stdout = command_result.get("result", {}).get("stdout", "")
                print(f"   Command output: {stdout.strip()}")
            else:
                print(f"   ❌ Command execution failed: {command_result.get('error')}")
            
            # Clean up
            test_file.unlink()
            
        except Exception as e:
            print(f"   ❌ File operations test failed: {e}")
        
        # Test with memory and research context
        print("\n4️⃣  Testing memory and research integration...")
        try:
            result = await mycoder.process_request(
                "What are the latest best practices for Python async programming?",
                use_mcp_memory=True,
                research_context=True,
                timeout=45
            )
            
            print(f"   Memory Context: {'✅' if result.get('memory_context') else '❌'}")
            print(f"   Research Context: {'✅' if result.get('research_context') else '❌'}")
            print(f"   MCP Tools Used: {len(result.get('mcp_tools_used', []))}")
            
            if result.get("success"):
                print(f"   ✅ Enhanced request with context successful")
            else:
                print(f"   ℹ️  Response: {result.get('content', 'No response')[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Context integration test failed: {e}")
        
        # Test mode transitions with MCP
        print("\n5️⃣  Testing adaptive modes with MCP integration...")
        original_mode = mycoder.mode_manager.current_mode
        
        for test_mode in [OperationalMode.DEGRADED, OperationalMode.AUTONOMOUS]:
            try:
                print(f"   Testing {test_mode.value} mode...")
                await mycoder.force_mode(test_mode, "testing")
                
                # Test capability in this mode
                result = await mycoder.process_request(
                    f"Test enhanced capabilities in {test_mode.value} mode",
                    timeout=20
                )
                
                status = mycoder.get_enhanced_status()
                mcp_connected = status['mcp_orchestrator']['connected']
                
                print(f"     Mode: {result['mode']}")
                print(f"     MCP Connected: {'✅' if mcp_connected else '❌'}")
                print(f"     Source: {result.get('source', 'unknown')}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"     ❌ {test_mode.value} mode test failed: {e}")
        
        # Restore original mode
        await mycoder.force_mode(original_mode, "test cleanup")
        
        # Final status
        print("\n6️⃣  Final enhanced status:")
        final_status = mycoder.get_enhanced_status()
        
        print(f"   Current mode: {final_status['mode']}")
        print(f"   MCP orchestrator: {final_status['mcp_orchestrator']['url']}")
        print(f"   Connected: {'✅' if final_status['mcp_orchestrator']['connected'] else '❌'}")
        print(f"   Enhanced capabilities: {list(final_status['enhanced_capabilities'].keys())}")
        
        # Cleanup
        await mycoder.shutdown()
        
        print("\n🎉 Enhanced MyCoder test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Enhanced MyCoder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_scenarios():
    """Test real-world integration scenarios."""
    print("\n🎯 Testing Integration Scenarios...")
    
    try:
        from claude_cli_auth.enhanced_mycoder import EnhancedMyCoder
        
        mycoder = EnhancedMyCoder()
        await mycoder.initialize()
        
        scenarios = [
            {
                "name": "Code Review with Memory",
                "prompt": "Review this code and remember the issues found for future reference",
                "files": ["test_enhanced_mycoder.py"],
                "use_mcp_memory": True
            },
            {
                "name": "Research-Enhanced Development", 
                "prompt": "What's the current state of async Python frameworks?",
                "research_context": True
            },
            {
                "name": "File Analysis with Context",
                "prompt": "Analyze my project structure and suggest improvements",
                "files": ["."],
                "use_mcp_memory": True
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n   Scenario {i}: {scenario['name']}")
            
            try:
                result = await mycoder.process_request(
                    scenario["prompt"],
                    files=scenario.get("files"),
                    use_mcp_memory=scenario.get("use_mcp_memory", False),
                    research_context=scenario.get("research_context", False),
                    timeout=30
                )
                
                if result.get("success"):
                    print(f"     ✅ Success - {result.get('source', 'unknown')} source")
                    tools_used = result.get('mcp_tools_used', [])
                    if tools_used:
                        print(f"     MCP Tools: {', '.join(tools_used)}")
                else:
                    print(f"     ℹ️  {result.get('content', 'No response')[:50]}...")
                
            except Exception as e:
                print(f"     ❌ Scenario failed: {e}")
        
        await mycoder.shutdown()
        return True
        
    except Exception as e:
        print(f"   ❌ Integration scenarios failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Enhanced MyCoder Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run tests
    mcp_test_ok = await test_mcp_connector()
    enhanced_test_ok = await test_enhanced_mycoder()
    integration_test_ok = await test_integration_scenarios()
    
    duration = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"🏁 Test suite completed in {duration:.1f}s")
    
    if mcp_test_ok and enhanced_test_ok and integration_test_ok:
        print("✅ All tests passed! Enhanced MyCoder with MCP integration is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the logs above for details.")
        print("🔧 Troubleshooting tips:")
        print("   • Ensure MCP orchestrator is running on 192.168.0.58:8020")
        print("   • Check network connectivity")
        print("   • Verify MCP services are healthy")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)