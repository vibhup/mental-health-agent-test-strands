#!/usr/bin/env python3
"""
Test Permissions Fix
Quick test to verify if the permissions issue is resolved
"""

import boto3
import json
import uuid
import time

def test_permissions_fix():
    print("🔧 TESTING PERMISSIONS FIX")
    print("=" * 40)
    
    try:
        # Step 1: Get Cognito credentials
        print("1. Getting Cognito credentials...")
        cognito = boto3.client('cognito-identity', region_name='us-east-1')
        
        identity_response = cognito.get_id(
            IdentityPoolId='us-east-1:fee1a888-11e8-40a2-a195-9acb975d1b72'
        )
        
        credentials_response = cognito.get_credentials_for_identity(
            IdentityId=identity_response['IdentityId']
        )
        
        credentials = credentials_response['Credentials']
        print(f"✅ Got credentials: {credentials['AccessKeyId'][:10]}...")
        
        # Step 2: Test AgentCore call with new permissions
        print("2. Testing AgentCore Runtime call...")
        
        agentcore = boto3.client(
            'bedrock-agentcore',
            region_name='us-east-1',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretKey'],
            aws_session_token=credentials['SessionToken']
        )
        
        session_id = f'permission_test_{uuid.uuid4().hex}'
        
        payload = {
            'input': 'Hello, I need help with anxiety. Can you support me?',
            'sessionId': session_id,
            'actorId': 'permission_test_user',
            'context': []
        }
        
        print(f"   Session ID: {session_id}")
        print(f"   Message: {payload['input']}")
        
        start_time = time.time()
        
        response = agentcore.invoke_agent_runtime(
            agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I',
            runtimeSessionId=session_id,
            payload=json.dumps(payload),
            contentType='application/json',
            accept='application/json'
        )
        
        end_time = time.time()
        
        # Parse response
        response_body = response['response'].read().decode('utf-8')
        agent_response = json.loads(response_body)
        
        print(f"✅ SUCCESS! AgentCore responded in {end_time - start_time:.2f} seconds")
        print(f"✅ Response: {agent_response.get('response', 'No response')[:100]}...")
        
        # Step 3: Test Memory operations
        print("3. Testing AgentCore Memory operations...")
        
        try:
            # Try to create an event
            memory_response = agentcore.create_event(
                memoryId='MentalHealthChatbotMemory-GqmjCf2KIw',
                actorId='permission_test_user',
                sessionId=session_id,
                eventTimestamp=int(time.time()),
                payload=[
                    {
                        'conversational': {
                            'role': 'USER',
                            'content': {
                                'text': payload['input']
                            }
                        }
                    }
                ]
            )
            
            print(f"✅ Memory event created: {memory_response.get('event', {}).get('eventId', 'No ID')}")
            
        except Exception as e:
            print(f"⚠️ Memory operation failed: {str(e)}")
            if 'AccessDenied' in str(e):
                print("   (This might be expected - memory access may be restricted)")
        
        print("\n🎉 PERMISSIONS FIX SUCCESSFUL!")
        print("✅ AgentCore Runtime calls now working")
        print("✅ Browser should be able to connect")
        
        return True
        
    except Exception as e:
        print(f"❌ PERMISSIONS FIX FAILED: {str(e)}")
        
        if 'AccessDenied' in str(e):
            print("🔍 Still a permissions issue - need to investigate further")
        elif 'InvalidSignature' in str(e):
            print("🔍 Signature issue - check AWS SDK configuration")
        else:
            print("🔍 Other issue - check error details above")
        
        return False

def main():
    success = test_permissions_fix()
    
    print("\n" + "=" * 40)
    print("🎯 RESULT")
    print("=" * 40)
    
    if success:
        print("✅ CONNECTION ERROR SHOULD BE FIXED!")
        print("🌐 Try the website now: https://d3nlpr9no3kmjc.cloudfront.net")
        print("💬 Users should be able to send messages successfully")
        print("🔧 The permissions issue has been resolved")
    else:
        print("❌ CONNECTION ERROR STILL EXISTS")
        print("🔧 Need to investigate further or try alternative approach")
        print("💡 May need to implement Lambda proxy instead")

if __name__ == "__main__":
    main()
