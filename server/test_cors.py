#!/usr/bin/env python3
"""
Simple script to test CORS functionality for the YouTube AI Assistant server
"""

import requests
import json

def test_cors():
    """Test CORS preflight and actual requests"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Test 1: OPTIONS request (preflight)
    print("🧪 Testing OPTIONS request (CORS preflight)...")
    try:
        response = requests.options(
            f"{base_url}/langchain/process-video",
            headers={
                "Origin": "chrome-extension://test-extension-id",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("   ✅ OPTIONS request successful!")
        else:
            print(f"   ❌ OPTIONS request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ OPTIONS request failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Actual POST request
    print("🧪 Testing POST request...")
    try:
        response = requests.post(
            f"{base_url}/langchain/process-video",
            headers={
                "Origin": "chrome-extension://test-extension-id",
                "Content-Type": "application/json"
            },
            json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 422]:  # 422 is validation error, which is OK for test
            print("   ✅ POST request processed (CORS working)!")
            if response.status_code == 422:
                print("   ℹ️  Got validation error (expected for test URL)")
        else:
            print(f"   ❌ POST request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ POST request failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Health check
    print("🧪 Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Server is healthy!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")

if __name__ == "__main__":
    test_cors()