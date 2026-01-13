#!/usr/bin/env python3
"""
Test script for DeepSeek integration in MyCoder
Verifies that the DeepSeek optimization works correctly
"""

import asyncio
import sys
import json
from mycoder.ollama_integration import OllamaClient, CodeGenerationProvider

async def test_deepseek_integration():
    """Test the complete DeepSeek integration."""
    print("🧪 Testing DeepSeek Integration for MyCoder")
    print("=" * 50)
    
    # Test 1: Ollama Connection
    print("\n1️⃣ Testing Ollama Connection...")
    async with OllamaClient() as client:
        if await client.is_available():
            print("✅ Ollama is available")
        else:
            print("❌ Ollama is not available - please start Ollama service")
            return False
        
        # Test 2: List Available Models
        print("\n2️⃣ Checking Available Models...")
        models = await client.list_models()
        print(f"📋 Found {len(models)} models:")
        
        deepseek_available = False
        for model in models:
            name = model.get('name', 'unknown')
            print(f"   • {name}")
            if 'deepseek' in name.lower():
                deepseek_available = True
        
        if not deepseek_available:
            print("⚠️  No DeepSeek models found. Testing with available models...")
        else:
            print("✅ DeepSeek models detected")
        
        # Test 3: CodeGenerationProvider
        print("\n3️⃣ Testing Code Generation Provider...")
        provider = CodeGenerationProvider(client)
        
        if await provider.is_ready():
            best_model = await provider.get_available_model()
            print(f"✅ Code generation ready with model: {best_model}")
            
            if 'deepseek' in best_model.lower():
                print("🎯 Using DeepSeek model as expected!")
            else:
                print(f"⚠️  Using fallback model: {best_model}")
            
            # Test 4: Code Generation
            print("\n4️⃣ Testing Code Generation...")
            test_prompts = [
                ("Create a Python function that calculates fibonacci numbers", "python"),
                ("Write a JavaScript function to validate email addresses", "javascript"),
                ("Generate a simple REST API endpoint in Python using FastAPI", "python")
            ]
            
            for i, (prompt, language) in enumerate(test_prompts, 1):
                print(f"\n   Test {i}: {language.title()} code generation")
                print(f"   Prompt: {prompt[:50]}...")
                
                result = await provider.generate_code(prompt, language=language)
                
                if result.get('error'):
                    print(f"   ❌ Failed: {result.get('content')}")
                else:
                    content = result.get('content', '')
                    model = result.get('model', 'unknown')
                    tokens = result.get('tokens_used', 0)
                    time_taken = result.get('generation_time', 0)
                    
                    print(f"   ✅ Generated {len(content)} characters")
                    print(f"   📊 Model: {model}")
                    print(f"   🔢 Tokens: {tokens}")
                    print(f"   ⏱️  Time: {time_taken:.2f}s")
                    
                    # Show first few lines of generated code
                    lines = content.split('\n')[:3]
                    for line in lines:
                        if line.strip():
                            print(f"   💻 {line}")
                    print("   ...")
            
            # Test 5: Performance Check
            print("\n5️⃣ Performance Evaluation...")
            simple_prompt = "Create a simple hello world function"
            start_time = asyncio.get_event_loop().time()
            
            result = await provider.generate_code(simple_prompt, language="python")
            
            end_time = asyncio.get_event_loop().time()
            total_time = end_time - start_time
            
            if not result.get('error'):
                tokens = result.get('tokens_used', 0)
                tokens_per_sec = tokens / total_time if total_time > 0 else 0
                
                print(f"   ⏱️  Total time: {total_time:.2f}s")
                print(f"   🚀 Tokens/sec: {tokens_per_sec:.1f}")
                
                if tokens_per_sec > 10:
                    print("   ✅ Performance: Good")
                elif tokens_per_sec > 5:
                    print("   ⚠️  Performance: Acceptable")
                else:
                    print("   🐌 Performance: Slow")
            
            print("\n🎉 DeepSeek Integration Test Complete!")
            return True
            
        else:
            print("❌ Code generation provider not ready")
            return False

async def test_model_priority():
    """Test that DeepSeek models have priority in selection."""
    print("\n🔍 Testing Model Priority...")
    
    async with OllamaClient() as client:
        provider = CodeGenerationProvider(client)
        
        # Check model priority
        print("📋 Model priority order:")
        for i, model in enumerate([provider.model_name] + provider.fallback_models, 1):
            print(f"   {i}. {model}")
        
        # Verify DeepSeek is primary
        if 'deepseek' in provider.model_name.lower():
            print("✅ DeepSeek is set as primary model")
            return True
        else:
            print("❌ DeepSeek is not primary model")
            return False

def main():
    """Main test function."""
    print("🤖 MyCoder DeepSeek Integration Test")
    print("=" * 60)
    
    # Run tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test model priority first
        priority_ok = loop.run_until_complete(test_model_priority())
        
        if priority_ok:
            integration_ok = loop.run_until_complete(test_deepseek_integration())
            
            if integration_ok:
                print("\n🎉 ALL TESTS PASSED!")
                print("MyCoder is optimized for DeepSeek! 🚀")
                return 0
            else:
                print("\n❌ Integration tests failed")
                return 1
        else:
            print("\n❌ Model priority test failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        return 1
    finally:
        loop.close()

if __name__ == "__main__":
    sys.exit(main())
