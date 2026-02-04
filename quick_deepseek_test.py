#!/usr/bin/env python3
"""
Quick DeepSeek configuration test for MyCoder
Tests model priority without complex imports
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_deepseek_config():
    """Test DeepSeek configuration directly."""
    print("🧪 Quick DeepSeek Configuration Test")
    print("=" * 40)

    # Test 1: Check ollama_integration.py configuration
    print("1️⃣ Checking ollama_integration.py configuration...")

    try:
        with open("src/ollama_integration.py", "r") as f:
            content = f.read()

        # Check primary model
        if 'self.model_name = "deepseek-coder:1.3b-base-q4_0"' in content:
            print("✅ DeepSeek set as primary model")
        else:
            print("❌ DeepSeek not set as primary model")
            return False

        # Check fallback order
        if "deepseek-coder:1.3b-base-q4_0" in content and content.index(
            "deepseek-coder:1.3b-base-q4_0"
        ) < content.index("codestral"):
            print("✅ DeepSeek has priority over Codestral in fallbacks")
        else:
            print("❌ DeepSeek doesn't have proper priority")
            return False

        # Check DeepSeek-specific prompting
        if 'if "deepseek" in model.lower():' in content:
            print("✅ DeepSeek-specific prompting implemented")
        else:
            print("❌ DeepSeek-specific prompting missing")
            return False

    except FileNotFoundError:
        print("❌ src/ollama_integration.py not found")
        return False

    # Test 2: Check docker-entrypoint.sh
    print("\n2️⃣ Checking docker-entrypoint.sh configuration...")

    try:
        with open("docker-entrypoint.sh", "r") as f:
            content = f.read()

        if "deepseek-coder:1.3b-base-q4_0" in content:
            print("✅ DeepSeek model in Docker entrypoint")
        else:
            print("❌ DeepSeek model missing from Docker entrypoint")
            return False

        # Check DeepSeek is prioritized (no Codestral references)
        codestral_count = content.count("codestral")
        if codestral_count == 0:
            print(
                "✅ DeepSeek is prioritized (Codestral removed from Docker entrypoint)"
            )
        else:
            print("❌ Codestral still referenced in Docker entrypoint")
            return False

    except FileNotFoundError:
        print("❌ docker-entrypoint.sh not found")
        return False

    # Test 3: Check docker-compose.yml
    print("\n3️⃣ Checking docker-compose.yml configuration...")

    try:
        with open("docker-compose.yml", "r") as f:
            content = f.read()

        if "MYCODER_LLM_MODEL=deepseek-coder:1.3b-base-q4_0" in content:
            print("✅ DeepSeek set as default model in Docker Compose")
        else:
            print("❌ DeepSeek not set as default in Docker Compose")
            return False

    except FileNotFoundError:
        print("❌ docker-compose.yml not found")
        return False

    # Test 4: Check hardware requirements
    print("\n4️⃣ Checking hardware requirements update...")

    try:
        with open("HW_REQUIREMENTS.md", "r") as f:
            content = f.read()

        if "**🚀 DeepSeek**" in content:
            print("✅ DeepSeek scenario added to hardware requirements")
        else:
            print("❌ DeepSeek scenario missing from hardware requirements")
            return False

        if "Why DeepSeek?" in content:
            print("✅ DeepSeek benefits documented")
        else:
            print("❌ DeepSeek benefits not documented")
            return False

    except FileNotFoundError:
        print("❌ HW_REQUIREMENTS.md not found")
        return False

    print("\n🎉 All configuration checks passed!")
    print("🚀 MyCoder is successfully optimized for DeepSeek!")

    print("\n📋 Quick Start Commands:")
    print("   docker-compose up                    # Start MyCoder with DeepSeek")
    print("   ./docker-build.sh quick && docker-compose up")
    print("   python -m pytest tests/ -v          # Run tests")

    return True


def show_deepseek_summary():
    """Show summary of DeepSeek optimization."""
    print("\n" + "=" * 50)
    print("🎯 DeepSeek Optimization Summary")
    print("=" * 50)

    print("\n🔧 Configuration Changes:")
    print("   • Primary model: deepseek-coder:1.3b-base-q4_0")
    print("   • Docker pulls DeepSeek first")
    print("   • Optimized prompting for DeepSeek")
    print("   • Environment variable updated")

    print("\n📊 Benefits:")
    print("   • RAM requirement: 32GB → 4-8GB")
    print("   • Model size: 13GB → 750MB")
    print("   • Startup time: Much faster")
    print("   • Hardware compatibility: Excellent")

    print("\n🚀 Ready to use MyCoder with DeepSeek!")


def main():
    """Main test function."""
    if test_deepseek_config():
        show_deepseek_summary()
        return 0
    else:
        print("\n❌ Configuration test failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
