#!/usr/bin/env python3

import requests
import json

def test_chatbot():
    base_url = "http://localhost:5000"
    
    print("Testing Testcase Failure Chatbot...")
    
    # Test 0: Load data first
    try:
        response = requests.get(f"{base_url}/api/testcases")
        data = response.json()
        print(f"✅ Data loaded: {data.get('filtered_cases', 0)} testcases")
    except Exception as e:
        print(f"❌ Data loading error: {e}")
    
    # Test 1: Check if data is available
    try:
        response = requests.get(f"{base_url}/api/chatbot/data")
        data = response.json()
        print(f"✅ Data endpoint: {data.get('data_available', False)}")
        print(f"   Records: {data.get('total_records', 0)}")
    except Exception as e:
        print(f"❌ Data endpoint error: {e}")
    
    # Test 2: Test a simple query
    try:
        response = requests.post(f"{base_url}/api/chatbot", 
                               json={"query": "How many testcase failures are there?"})
        data = response.json()
        print(f"✅ Query test: {data.get('response', 'No response')[:50]}...")
    except Exception as e:
        print(f"❌ Query test error: {e}")
    
    # Test 3: Test suggestions endpoint
    try:
        response = requests.get(f"{base_url}/api/chatbot/suggestions")
        data = response.json()
        print(f"✅ Suggestions: {len(data.get('suggestions', []))} suggestions available")
    except Exception as e:
        print(f"❌ Suggestions error: {e}")

if __name__ == "__main__":
    test_chatbot() 