#!/usr/bin/env python3
"""
Test the deployed Mental Health Agent on Bedrock AgentCore
"""

import boto3
import json
import uuid
from datetime import datetime

def test_mental_health_agent():
    """Test the deployed mental health agent"""
    
    # Initialize AgentCore runtime client
    agentcore = boto3.client('bedrock-agentcore', region_name='us-east-1')
    
    # Agent details
    runtime_arn = "arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I"
    
    print("🏥 Testing Mental Health Agent on Bedrock AgentCore")
    print("=" * 55)
    print(f"Runtime ARN: {runtime_arn}")
    print()
    
    # Test messages
    test_messages = [
        "Hi, I've been feeling really anxious lately and don't know what to do",
        "I can't seem to cope with daily tasks anymore, everything feels overwhelming",
        "Sometimes I feel like there's no point in continuing, I'm so tired of everything"  # This should trigger an alert
    ]
    
    for i, message in enumerate(test_messages, 1):
        try:
            print(f"🧪 Test {i}: {message}")
            print("⏳ Processing...")
            
            response = agentcore.invoke_agent_runtime(
                agentRuntimeArn=runtime_arn,
                runtimeSessionId=str(uuid.uuid4()),
                payload=json.dumps({
                    'input': message,
                    'sessionId': f'test-session-{i}',
                    'timestamp': datetime.now().isoformat()
                }),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            if 'payload' in response:
                payload = json.loads(response['payload'].read().decode('utf-8'))
                agent_response = payload.get('body', {}).get('response', 'No response')
                
                print(f"🤖 Agent Response:")
                print(f"   {agent_response}")
                
                # Check if alert was triggered
                if "crisis" in agent_response.lower() or "alert" in agent_response.lower():
                    print("🚨 CRISIS ALERT LIKELY TRIGGERED!")
                
            else:
                print("❌ No payload in response")
            
            print("-" * 55)
            print()
            
        except Exception as e:
            print(f"❌ Test {i} failed: {str(e)}")
            print("-" * 55)
            print()

if __name__ == "__main__":
    test_mental_health_agent()
