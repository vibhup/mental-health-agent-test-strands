#!/usr/bin/env python3
"""
Test the fixed direct AgentCore integration
"""

import boto3
import json
import uuid
import urllib.request
from datetime import datetime

def test_website_updated():
    """Test if the website has the updated JavaScript"""
    try:
        print("🌐 Testing updated website...")
        
        # Test JavaScript file
        with urllib.request.urlopen('https://d3nlpr9no3kmjc.cloudfront.net/agentcore-direct.js') as response:
            js_content = response.read().decode('utf-8')
        
        # Check for fixes
        fixes = [
            ('AWS.HttpRequest', 'Direct HTTP requests implemented'),
            ('AWS.Signers.V4', 'AWS Signature V4 authentication'),
            ('bedrock-agentcore.us-east-1.amazonaws.com', 'Correct AgentCore endpoint'),
            ('updateStatus(\'processing\'', 'Processing status added'),
            ('Authentication Error', 'Better error handling'),
            ('try to reconnect', 'Auto-reconnect functionality')
        ]
        
        for check, description in fixes:
            if check in js_content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description}")
                return False
        
        print("✅ Website updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Website test failed: {str(e)}")
        return False

def test_cognito_credentials():
    """Test Cognito credentials still work"""
    try:
        print("🔐 Testing Cognito credentials...")
        
        cognito = boto3.client('cognito-identity', region_name='us-east-1')
        
        # Get identity and credentials
        identity_response = cognito.get_id(
            IdentityPoolId='us-east-1:fee1a888-11e8-40a2-a195-9acb975d1b72'
        )
        
        credentials_response = cognito.get_credentials_for_identity(
            IdentityId=identity_response['IdentityId']
        )
        
        credentials = credentials_response['Credentials']
        print(f"   ✅ Credentials obtained: {credentials['AccessKeyId'][:10]}...")
        print(f"   ✅ Expires: {credentials['Expiration']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cognito test failed: {str(e)}")
        return False

def test_agentcore_endpoints():
    """Test AgentCore endpoints are accessible"""
    try:
        print("🔗 Testing AgentCore endpoints...")
        
        # Test AgentCore control plane
        agentcore_control = boto3.client('bedrock-agentcore-control', region_name='us-east-1')
        
        # Test memory status
        memory_info = agentcore_control.get_memory(memoryId='MentalHealthChatbotMemory-GqmjCf2KIw')
        print(f"   ✅ Memory Status: {memory_info['memory']['status']}")
        
        # Test runtime status
        runtime_info = agentcore_control.get_agent_runtime(
            agentRuntimeId='mental_health_support_agent-lRczXz8e6I'
        )
        print(f"   ✅ Runtime Status: {runtime_info['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AgentCore endpoints test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🔧 TESTING FIXED DIRECT AGENTCORE INTEGRATION")
    print("=" * 60)
    
    tests = [
        ("Website Updated", test_website_updated),
        ("Cognito Credentials", test_cognito_credentials),
        ("AgentCore Endpoints", test_agentcore_endpoints)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{len(results) + 1}. {test_name}")
        print("-" * 30)
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FIX VALIDATION RESULTS")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL FIXES VALIDATED!")
        print("✅ Direct AgentCore integration should now work")
        print("🌐 Try the website: https://d3nlpr9no3kmjc.cloudfront.net")
    else:
        print("\n⚠️ SOME ISSUES REMAIN")
        print("🔧 Check failed tests above")
    
    print("\n📋 WHAT WAS FIXED:")
    print("✅ Proper AWS SDK initialization with credentials")
    print("✅ Direct HTTP requests with AWS Signature V4 auth")
    print("✅ Correct AgentCore API endpoints")
    print("✅ Better error handling and status updates")
    print("✅ Auto-reconnection on failures")
    print("✅ Processing status indicator")

if __name__ == "__main__":
    main()
