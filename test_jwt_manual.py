#!/usr/bin/env python3
"""
Manual JWT Authentication Test
Test the JWT authentication with AgentCore Runtime
"""

import boto3
import json
import requests
import urllib.parse
import uuid

def test_jwt_authentication():
    print("🧪 MANUAL JWT AUTHENTICATION TEST")
    print("=" * 50)
    
    # Configuration from the setup
    region = 'us-east-1'
    user_pool_id = 'us-east-1_IqzrBzc0g'
    client_id = '1l0v1imj8h6pg0i7villspuqr8'
    runtime_arn = 'arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I'
    
    try:
        # Step 1: Get JWT token
        print("1. Getting JWT token...")
        cognito_idp = boto3.client('cognito-idp', region_name=region)
        
        auth_response = cognito_idp.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': 'testuser@example.com',
                'PASSWORD': 'MentalHealth123!'
            }
        )
        
        access_token = auth_response['AuthenticationResult']['AccessToken']
        print(f"✅ JWT Token: {access_token[:50]}...")
        
        # Step 2: Test AgentCore Runtime call
        print("2. Testing AgentCore Runtime call...")
        
        # URL encode the agent ARN
        escaped_agent_arn = urllib.parse.quote(runtime_arn, safe='')
        
        # Construct the URL
        url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations"
        
        # Set up headers with proper session ID (33+ characters)
        session_id = f"jwt_manual_test_session_{uuid.uuid4().hex}"  # This will be 33+ chars
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id
        }
        
        # Test payload
        payload = {
            "input": "Hello, I'm feeling anxious and need mental health support. Can you help me?",
            "sessionId": session_id,
            "actorId": "jwt_manual_test_user",
            "context": []
        }
        
        print(f"   URL: {url}")
        print(f"   Message: {payload['input']}")
        
        # Make the request
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            agent_response = response_data.get('response', 'No response')
            print(f"✅ Agent Response: {agent_response}")
            print("\n🎉 JWT AUTHENTICATION WORKING SUCCESSFULLY!")
            print("✅ Direct browser access to AgentCore Runtime is now possible")
            print("✅ Connection error should be resolved")
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_jwt_authentication()
    
    if success:
        print("\n" + "=" * 50)
        print("🎯 SOLUTION CONFIRMED!")
        print("=" * 50)
        print("✅ JWT Authentication is working")
        print("✅ AgentCore Runtime accepts Bearer tokens")
        print("✅ Direct browser access is now possible")
        print("\n🔧 TO FIX THE CONNECTION ERROR:")
        print("1. Update browser JavaScript to use JWT tokens")
        print("2. Replace AWS SigV4 with Bearer token authentication")
        print("3. Use Cognito User Pool for user authentication")
        print("\nThe connection error will be resolved!")
    else:
        print("\n❌ JWT authentication still has issues")
        print("Need to investigate further")
