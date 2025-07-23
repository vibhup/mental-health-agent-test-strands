#!/usr/bin/env python3
"""
Test the working Mental Health Agent on Bedrock AgentCore
"""

import boto3
import json
import uuid
from datetime import datetime

def test_mental_health_agent():
    """Test the deployed mental health agent"""
    
    # Initialize AgentCore runtime client
    client = boto3.client('bedrock-agentcore', region_name='us-east-1')
    
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
    
    session_id = str(uuid.uuid4())
    
    for i, message in enumerate(test_messages, 1):
        try:
            print(f"🧪 Test {i}: {message}")
            print("⏳ Processing...")
            
            response = client.invoke_agent_runtime(
                agentRuntimeArn=runtime_arn,
                runtimeSessionId=str(uuid.uuid4()),
                payload=json.dumps({
                    'input': message,
                    'sessionId': session_id
                }),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = response['response'].read().decode('utf-8')
            result = json.loads(response_body)
            
            agent_response = result.get('response', 'No response')
            
            print(f"🤖 Agent Response:")
            print(f"   {agent_response}")
            
            # Check if this might trigger crisis detection
            crisis_keywords = ['suicide', 'kill myself', 'end it all', 'no point', 'tired of everything']
            if any(keyword in message.lower() for keyword in crisis_keywords):
                print("🚨 CRISIS KEYWORDS DETECTED - Alert should be triggered!")
            
            print("-" * 55)
            print()
            
        except Exception as e:
            print(f"❌ Test {i} failed: {str(e)}")
            print("-" * 55)
            print()

if __name__ == "__main__":
    test_mental_health_agent()
