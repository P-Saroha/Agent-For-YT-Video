#!/usr/bin/env python3
"""
Test CORS with simple server on port 8001
"""

import requests

def test_simple_cors():
    """Test CORS with simple server"""
    
    base_url = "http://127.0.0.1:8003"
    
    print("🧪 Testing simple server CORS...")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Health check: {response.status_code}")
        print(f"   CORS headers: {response.headers.get('access-control-allow-origin', 'Not present')}")
        
        if response.status_code == 200:
            print("   ✅ Simple server is working!")
        else:
            print(f"   ❌ Simple server failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Simple server test failed: {e}")
    
    # Test OPTIONS
    try:
        response = requests.options(
            f"{base_url}/langchain/process-video",
            headers={
                "Origin": "chrome-extension://test-extension-id",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        print(f"   OPTIONS request: {response.status_code}")
        print(f"   CORS headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("   ✅ OPTIONS request successful!")
        else:
            print(f"   ❌ OPTIONS request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ OPTIONS request failed: {e}")

if __name__ == "__main__":
    test_simple_cors()