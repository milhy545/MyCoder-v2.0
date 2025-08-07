#!/usr/bin/env python3
"""Real-world test with Claude CLI query."""

import asyncio
import logging
from pathlib import Path

# Set minimal logging to see what's happening 
logging.basicConfig(level=logging.DEBUG)
for logger_name in ["claude_cli_auth"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

async def test_real_query():
    """Test real Claude CLI query."""
    print("🌟 Testing real Claude CLI query...")
    
    try:
        from claude_cli_auth import ClaudeAuthManager, AuthConfig
        
        # Create config with CLI-only mode
        config = AuthConfig(
            working_directory=Path.cwd(),
            timeout_seconds=30,
            use_sdk=False,
            allowed_tools=["Read", "Write"],
        )
        
        print("1️⃣  Initializing with CLI-only mode...")
        claude = ClaudeAuthManager(
            config=config,
            prefer_sdk=False,
            enable_fallback=False
        )
        print("   ✅ Manager initialized")
        
        print("2️⃣  Testing simple query...")
        response = await claude.query(
            prompt="Say 'Hello from Claude CLI Auth module!' briefly",
            timeout=30
        )
        
        print(f"   ✅ Query successful!")
        print(f"   Response: {response.content}")
        print(f"   Session ID: {response.session_id}")
        if response.cost > 0:
            print(f"   Cost: ${response.cost:.4f}")
        print(f"   Duration: {response.duration_ms}ms")
        
        print("3️⃣  Testing session info...")
        session = claude.get_session(response.session_id)
        if session:
            print(f"   Session status: {session.status.value}")
            print(f"   Total cost: ${session.total_cost:.4f}")
            print(f"   Total turns: {session.total_turns}")
        
        print("4️⃣  Cleaning up...")
        await claude.shutdown()
        
        print("\n🎉 Real-world test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Real-world test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_query())
    if success:
        print("\n✨ Claude CLI Auth module is working correctly!")
    else:
        print("\n💥 Module needs debugging")
        exit(1)