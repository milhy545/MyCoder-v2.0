#!/usr/bin/env python3
"""
Test script for MyCoder v2.1.0 integration with claude-cli-auth module.
"""

import asyncio
import sys
from pathlib import Path

# Test basic imports
try:
    print("Testing imports...")
    
    # Test core claude-cli-auth imports
    from claude_cli_auth import (
        ClaudeAuthManager,
        AuthManager,
        CLIInterface,
        ClaudeAuthError,
    )
    print("✅ Core claude-cli-auth imports successful")
    
    # Test MyCoder imports from local package
    from mycoder import (
        AdaptiveModeManager,
        OperationalMode,
        MCPConnector,
        MCPToolRouter,
        MyCoder,
        EnhancedMyCoder,
    )
    print("✅ MyCoder-specific imports successful")
    
    # Test local package structure
    from mycoder.adaptive_modes import AdaptiveModeManager, OperationalMode
    from mycoder.mycoder import MyCoder
    from mycoder.enhanced_mycoder import EnhancedMyCoder
    print("✅ Local module imports successful")
    
    print("\n🎉 All imports successful! Integration working correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

async def test_basic_functionality():
    """Test basic MyCoder functionality."""
    try:
        print("\nTesting basic functionality...")
        
        # Test adaptive mode manager
        manager = AdaptiveModeManager()
        current_mode = manager.current_mode
        print(f"✅ Adaptive mode manager initialized. Current mode: {current_mode}")
        
        # Test MyCoder initialization
        mycoder = MyCoder()
        print("✅ MyCoder initialized successfully")
        
        # Test EnhancedMyCoder initialization
        enhanced = EnhancedMyCoder()
        print("✅ EnhancedMyCoder initialized successfully")
        
        print("\n🎉 Basic functionality test passed!")
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("MyCoder v2.1.0 Integration Test")
    print("=" * 50)
    
    # Run async test
    asyncio.run(test_basic_functionality())
    
    print("\n✅ Integration test completed successfully!")
    print("MyCoder v2.1.0 is ready to use with claude-cli-auth dependency!")