#!/usr/bin/env python3
"""Test Claude API key availability and basic functionality."""

import os
import sys
import json
from typing import Dict, Any

def test_api_key_presence() -> bool:
    """Test if Claude API key is available."""
    api_key = os.getenv('CLAUDE_AUTO_SYNC_KEY')
    
    if not api_key:
        print("❌ CLAUDE_AUTO_SYNC_KEY environment variable not found")
        print("💡 Make sure the GitHub secret is set: CLAUDE_AUTO_SYNC_KEY")
        return False
    
    print("✅ CLAUDE_AUTO_SYNC_KEY found")
    print(f"🔑 Key format: {api_key[:8]}...{api_key[-4:] if len(api_key) >= 12 else '***'}")
    return True

def test_api_connectivity() -> bool:
    """Test basic API connectivity with a minimal request."""
    api_key = os.getenv('CLAUDE_AUTO_SYNC_KEY')
    
    if not api_key:
        return False
    
    try:
        import httpx
        
        print("🔄 Testing Claude API connectivity...")
        
        with httpx.Client() as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 10,
                    "messages": [{
                        "role": "user", 
                        "content": "Say 'API test successful' (exactly 3 words)"
                    }]
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [{}])[0].get("text", "")
                print(f"✅ API test successful: {content.strip()}")
                
                # Log usage info for monitoring
                usage = result.get("usage", {})
                print(f"📊 Usage: {usage.get('input_tokens', 0)} input + {usage.get('output_tokens', 0)} output tokens")
                return True
            else:
                print(f"❌ API request failed: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
                
    except ImportError:
        print("❌ httpx not available - install dependencies first")
        print("💡 Run: cd python && uv sync")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def generate_test_summary() -> Dict[str, Any]:
    """Generate test results summary for GitHub Actions."""
    api_key_available = test_api_key_presence()
    
    if not api_key_available:
        return {
            "api_key_available": False,
            "api_connectivity": False,
            "ready_for_auto_sync": False,
            "message": "API key not configured"
        }
    
    api_works = test_api_connectivity()
    
    return {
        "api_key_available": True,
        "api_connectivity": api_works,
        "ready_for_auto_sync": api_works,
        "message": "Ready for AI auto-sync" if api_works else "API key present but connectivity failed"
    }

def main():
    """Main test function."""
    print("🧪 Testing Claude API Key Setup")
    print("=" * 50)
    
    # Run tests
    results = generate_test_summary()
    
    # Output results
    print("\n📋 Test Summary:")
    print(f"  • API Key Available: {'✅' if results['api_key_available'] else '❌'}")
    print(f"  • API Connectivity: {'✅' if results['api_connectivity'] else '❌'}")
    print(f"  • Auto-sync Ready: {'✅' if results['ready_for_auto_sync'] else '❌'}")
    print(f"  • Status: {results['message']}")
    
    # Write results for GitHub Actions
    results_file = "api_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")
    
    # Set exit code
    exit_code = 0 if results['ready_for_auto_sync'] else 1
    print(f"\n🚪 Exit code: {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()