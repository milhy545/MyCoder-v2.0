# Basic Usage Examples

This guide provides practical examples of using Enhanced MyCoder v2.0 in various scenarios.

## Quick Start Example

```python
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path
import asyncio

async def basic_example():
    # Basic configuration
    config = {
        "claude_oauth": {"enabled": True},
        "ollama_local": {"enabled": True},
        "thermal": {"enabled": True, "max_temp": 75}
    }
    
    # Initialize MyCoder
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config
    )
    
    try:
        # Initialize the system
        await mycoder.initialize()
        
        # Simple query
        response = await mycoder.process_request(
            "What is the current date and time?"
        )
        
        print(f"Response: {response['content']}")
        print(f"Provider: {response['provider']}")
        print(f"Cost: ${response['cost']:.4f}")
        
    finally:
        await mycoder.shutdown()

# Run the example
if __name__ == "__main__":
    asyncio.run(basic_example())
```

## File Analysis Example

```python
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path
import asyncio

async def analyze_files():
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config={"claude_oauth": {"enabled": True}}
    )
    
    try:
        await mycoder.initialize()
        
        # Analyze a Python file
        response = await mycoder.process_request(
            "Analyze this Python file for potential improvements and bugs",
            files=[Path("example.py")]
        )
        
        print("Analysis Results:")
        print(response['content'])
        
        # Get system status
        status = await mycoder.get_system_status()
        print(f"\nSystem Status: {status['status']}")
        print(f"Active Sessions: {status['active_sessions']}")
        
    finally:
        await mycoder.shutdown()

if __name__ == "__main__":
    asyncio.run(analyze_files())
```

## Session Management Example

```python
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path
import asyncio

async def session_example():
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config={"claude_oauth": {"enabled": True}}
    )
    
    try:
        await mycoder.initialize()
        
        session_id = "my_coding_session"
        
        # First interaction
        response1 = await mycoder.process_request(
            "Help me create a Python function that calculates fibonacci numbers",
            session_id=session_id
        )
        
        print("Response 1:")
        print(response1['content'])
        print(f"Session ID: {response1['session_id']}")
        
        # Continue the session
        response2 = await mycoder.process_request(
            "Now add error handling and optimization to that function",
            session_id=session_id,
            continue_session=True
        )
        
        print("\nResponse 2:")
        print(response2['content'])
        
        # Third interaction in same session
        response3 = await mycoder.process_request(
            "Create unit tests for the fibonacci function",
            session_id=session_id,
            continue_session=True
        )
        
        print("\nResponse 3:")
        print(response3['content'])
        
    finally:
        await mycoder.shutdown()

if __name__ == "__main__":
    asyncio.run(session_example())
```

## Configuration Examples

### Environment Variable Configuration

```python
import os
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path

# Set environment variables
os.environ['MYCODER_DEBUG'] = '1'
os.environ['MYCODER_PREFERRED_PROVIDER'] = 'claude_oauth'
os.environ['MYCODER_THERMAL_MAX_TEMP'] = '70'

# MyCoder will automatically use environment variables
mycoder = EnhancedMyCoderV2(working_directory=Path("."))
```

### JSON Configuration File

```python
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from config_manager import ConfigManager
from pathlib import Path
import asyncio

async def config_file_example():
    # Load configuration from file
    config_manager = ConfigManager("mycoder_config.json")
    config = config_manager.load_config()
    
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config.dict()
    )
    
    try:
        await mycoder.initialize()
        
        # Update configuration at runtime
        config_manager.update_provider_config("ollama_local", {
            "model": "llama2:7b",
            "timeout_seconds": 120
        })
        
        # Save updated configuration
        config_manager.save_config("updated_config.json")
        
        response = await mycoder.process_request(
            "Test with updated configuration"
        )
        
        print(response['content'])
        
    finally:
        await mycoder.shutdown()

if __name__ == "__main__":
    asyncio.run(config_file_example())
```

## Error Handling Examples

### Basic Error Handling

```python
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path
import asyncio

async def error_handling_example():
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config={"claude_oauth": {"enabled": True}}
    )
    
    try:
        await mycoder.initialize()
        
        response = await mycoder.process_request(
            "Analyze this file that might not exist",
            files=[Path("nonexistent.py")]
        )
        
        if response['success']:
            print(f"Success: {response['content']}")
        else:
            print(f"Request failed: {response['error']}")
            
            # Check for recovery suggestions
            if 'recovery_suggestions' in response:
                print("Recovery suggestions:")
                for suggestion in response['recovery_suggestions']:
                    print(f"- {suggestion}")
        
    except Exception as e:
        print(f"System error: {e}")
        
        # Get system status for debugging
        try:
            status = await mycoder.get_system_status()
            print(f"System status: {status}")
        except:
            print("Could not get system status")
    
    finally:
        await mycoder.shutdown()

if __name__ == "__main__":
    asyncio.run(error_handling_example())
```

### Provider Fallback Example

```python
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path
import asyncio

async def fallback_example():
    # Configure multiple providers with fallback
    config = {
        "claude_anthropic": {"enabled": True, "timeout_seconds": 10},
        "claude_oauth": {"enabled": True, "timeout_seconds": 20},
        "gemini": {"enabled": True, "timeout_seconds": 15},
        "ollama_local": {"enabled": True, "timeout_seconds": 30},
        "fallback_enabled": True
    }
    
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config,
        preferred_provider="claude_anthropic"  # Try this first
    )
    
    try:
        await mycoder.initialize()
        
        # This will try providers in fallback order if preferred fails
        response = await mycoder.process_request(
            "Test fallback system with a simple request"
        )
        
        print(f"Response: {response['content']}")
        print(f"Used Provider: {response['provider']}")
        
        # Check which providers are healthy
        status = await mycoder.get_system_status()
        print("\nProvider Status:")
        for provider, info in status['providers'].items():
            print(f"- {provider}: {info['status']}")
        
    finally:
        await mycoder.shutdown()

if __name__ == "__main__":
    asyncio.run(fallback_example())
```

## Thermal Management Example (Q9550)

```python
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path
import asyncio

async def thermal_management_example():
    # Enable thermal management for Q9550
    config = {
        "claude_oauth": {"enabled": True},
        "thermal": {
            "enabled": True,
            "max_temp": 75.0,
            "critical_temp": 85.0,
            "check_interval": 30,
            "performance_script": "/path/to/performance_manager.sh"
        }
    }
    
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config
    )
    
    try:
        await mycoder.initialize()
        
        # Process a heavy request that might generate heat
        response = await mycoder.process_request(
            "Analyze this large codebase and provide detailed recommendations",
            files=[Path("large_project")]
        )
        
        print(f"Response: {response['content']}")
        
        # Check thermal status
        status = await mycoder.get_system_status()
        thermal_status = status.get('thermal', {})
        
        print(f"\nThermal Status:")
        print(f"- Temperature: {thermal_status.get('current_temp', 'N/A')}°C")
        print(f"- Safe Operation: {thermal_status.get('safe_operation', 'N/A')}")
        print(f"- Throttling Active: {thermal_status.get('throttling_active', 'N/A')}")
        
    finally:
        await mycoder.shutdown()

if __name__ == "__main__":
    asyncio.run(thermal_management_example())
```

## Batch Processing Example

```python
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path
import asyncio

async def batch_processing_example():
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config={"claude_oauth": {"enabled": True}}
    )
    
    try:
        await mycoder.initialize()
        
        # List of files to analyze
        files_to_analyze = [
            Path("src/main.py"),
            Path("src/utils.py"),
            Path("src/config.py"),
            Path("tests/test_main.py")
        ]
        
        session_id = "batch_analysis_session"
        results = []
        
        for i, file_path in enumerate(files_to_analyze):
            print(f"Analyzing {file_path}...")
            
            response = await mycoder.process_request(
                f"Analyze this file for code quality and suggest improvements",
                files=[file_path],
                session_id=session_id,
                continue_session=i > 0  # Continue session after first file
            )
            
            results.append({
                'file': str(file_path),
                'analysis': response['content'],
                'provider': response['provider'],
                'cost': response['cost']
            })
        
        # Summary analysis
        summary_response = await mycoder.process_request(
            "Based on the previous file analyses, provide an overall summary of the codebase quality and main recommendations",
            session_id=session_id,
            continue_session=True
        )
        
        print("\n" + "="*50)
        print("BATCH ANALYSIS RESULTS")
        print("="*50)
        
        total_cost = 0
        for result in results:
            print(f"\nFile: {result['file']}")
            print(f"Provider: {result['provider']}")
            print(f"Cost: ${result['cost']:.4f}")
            print(f"Analysis: {result['analysis'][:200]}...")
            total_cost += result['cost']
        
        print(f"\nOverall Summary:")
        print(summary_response['content'])
        print(f"\nTotal Cost: ${total_cost:.4f}")
        
    finally:
        await mycoder.shutdown()

if __name__ == "__main__":
    asyncio.run(batch_processing_example())
```

## Integration with Web Framework

```python
from flask import Flask, request, jsonify
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path
import asyncio
import threading

app = Flask(__name__)

# Global MyCoder instance
mycoder = None

def initialize_mycoder():
    global mycoder
    config = {
        "claude_oauth": {"enabled": True},
        "ollama_local": {"enabled": True}
    }
    
    mycoder = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config
    )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mycoder.initialize())

# Initialize in separate thread
init_thread = threading.Thread(target=initialize_mycoder)
init_thread.start()
init_thread.join()

@app.route('/analyze', methods=['POST'])
def analyze_code():
    try:
        data = request.json
        prompt = data.get('prompt', 'Analyze this code')
        code = data.get('code', '')
        
        # Create temporary file
        temp_file = Path('/tmp/temp_code.py')
        temp_file.write_text(code)
        
        # Process with MyCoder
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(
            mycoder.process_request(
                prompt,
                files=[temp_file]
            )
        )
        
        # Clean up
        temp_file.unlink()
        
        return jsonify({
            'success': response['success'],
            'content': response['content'],
            'provider': response['provider'],
            'cost': response['cost']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        status = loop.run_until_complete(mycoder.get_system_status())
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## Testing Integration

```python
import pytest
import asyncio
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path

@pytest.fixture
async def mycoder():
    config = {
        "claude_oauth": {"enabled": True},
        "thermal": {"enabled": False}  # Disable for tests
    }
    
    instance = EnhancedMyCoderV2(
        working_directory=Path("."),
        config=config
    )
    
    await instance.initialize()
    yield instance
    await instance.shutdown()

@pytest.mark.asyncio
async def test_basic_functionality(mycoder):
    response = await mycoder.process_request(
        "What is 2+2?"
    )
    
    assert response['success'] is True
    assert 'content' in response
    assert response['cost'] >= 0

@pytest.mark.asyncio
async def test_file_analysis(mycoder):
    # Create test file
    test_file = Path('/tmp/test.py')
    test_file.write_text('def hello(): return "world"')
    
    try:
        response = await mycoder.process_request(
            "Analyze this function",
            files=[test_file]
        )
        
        assert response['success'] is True
        assert 'function' in response['content'].lower()
        
    finally:
        test_file.unlink()

@pytest.mark.asyncio
async def test_session_persistence(mycoder):
    session_id = "test_session"
    
    # First request
    response1 = await mycoder.process_request(
        "Remember: my favorite color is blue",
        session_id=session_id
    )
    
    # Second request in same session
    response2 = await mycoder.process_request(
        "What is my favorite color?",
        session_id=session_id,
        continue_session=True
    )
    
    assert response1['success'] is True
    assert response2['success'] is True
    assert response1['session_id'] == response2['session_id']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Common Patterns

### Initialization Pattern

```python
# Always use try/finally for proper cleanup
async def safe_mycoder_usage():
    mycoder = EnhancedMyCoderV2(...)
    
    try:
        await mycoder.initialize()
        # Your code here
    finally:
        await mycoder.shutdown()
```

### Configuration Pattern

```python
# Load configuration from multiple sources
config = {
    # Base configuration
    "claude_oauth": {"enabled": True},
}

# Override with environment variables
import os
if os.getenv('MYCODER_PREFERRED_PROVIDER'):
    config['preferred_provider'] = os.getenv('MYCODER_PREFERRED_PROVIDER')

# Override with file configuration
from config_manager import ConfigManager
if Path('mycoder_config.json').exists():
    file_config = ConfigManager('mycoder_config.json').load_config()
    config.update(file_config.dict())
```

### Error Recovery Pattern

```python
async def robust_request(mycoder, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await mycoder.process_request(prompt)
            if response['success']:
                return response
            else:
                print(f"Attempt {attempt + 1} failed: {response['error']}")
        except Exception as e:
            print(f"Attempt {attempt + 1} error: {e}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return {'success': False, 'error': 'Max retries exceeded'}
```

These examples demonstrate the key patterns and use cases for Enhanced MyCoder v2.0. For more advanced usage, see the [API documentation](../api/) and [advanced examples](../../examples/).