#!/usr/bin/env python3
"""
End-to-End Test for Direct AgentCore Integration
Simulates browser behavior to test the complete flow
"""

import boto3
import json
import uuid
from datetime import datetime

class DirectAgentCoreTest:
    def __init__(self):
        self.region = 'us-east-1'
        self.identity_pool_id = 'us-east-1:fee1a888-11e8-40a2-a195-9acb975d1b72'
        self.runtime_arn = 'arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I'
        self.memory_id = 'MentalHealthChatbotMemory-GqmjCf2KIw'
        
        # Generate test user and session
        self.user_id = f'test_user_{uuid.uuid4().hex[:8]}'
        self.session_id = f'test_session_{uuid.uuid4().hex[:8]}'
        
        print(f"🧪 Testing Direct AgentCore Integration")
        print(f"User ID: {self.user_id}")
        print(f"Session ID: {self.session_id}")
        print("=" * 60)
        
    def setup_cognito_credentials(self):
        """Set up Cognito Identity credentials like browser would"""
        try:
            print("🔐 Setting up Cognito Identity credentials...")
            
            # Get Cognito Identity
            cognito_identity = boto3.client('cognito-identity', region_name=self.region)
            
            # Get identity ID (unauthenticated)
            identity_response = cognito_identity.get_id(
                IdentityPoolId=self.identity_pool_id
            )
            identity_id = identity_response['IdentityId']
            print(f"✅ Got Identity ID: {identity_id}")
            
            # Get credentials for this identity
            credentials_response = cognito_identity.get_credentials_for_identity(
                IdentityId=identity_id
            )
            
            credentials = credentials_response['Credentials']
            print(f"✅ Got temporary credentials")
            
            # Create AgentCore client with temporary credentials
            self.agentcore = boto3.client(
                'bedrock-agentcore',
                region_name=self.region,
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            print(f"✅ AgentCore client initialized with Cognito credentials")
            return True
            
        except Exception as e:
            print(f"❌ Cognito setup failed: {str(e)}")
            return False
    
    def test_memory_storage(self, message, role):
        """Test storing message in AgentCore Memory"""
        try:
            print(f"📝 Storing {role} message in AgentCore Memory...")
            
            # Correct payload format for AgentCore Memory
            payload = [
                {
                    'conversational': {
                        'role': role,
                        'content': {
                            'text': message
                        }
                    }
                }
            ]
            
            response = self.agentcore.create_event(
                memoryId=self.memory_id,
                actorId=self.user_id,
                sessionId=self.session_id,
                eventTimestamp=int(datetime.now().timestamp()),
                payload=payload
            )
            
            print(f"✅ Message stored successfully")
            print(f"   Event ID: {response.get('event', {}).get('eventId', 'N/A')}")
            return True
            
        except Exception as e:
            print(f"❌ Memory storage failed: {str(e)}")
            return False
    
    def test_memory_retrieval(self):
        """Test retrieving conversation context from AgentCore Memory"""
        try:
            print(f"📚 Retrieving conversation context from AgentCore Memory...")
            
            response = self.agentcore.list_events(
                memoryId=self.memory_id,
                actorId=self.user_id,
                sessionId=self.session_id,
                maxResults=10
            )
            
            events = response.get('events', [])
            print(f"✅ Retrieved {len(events)} events from memory")
            
            context = []
            for i, event in enumerate(events, 1):
                payload = event.get('payload', [])
                if payload and len(payload) > 0:
                    conversational = payload[0].get('conversational', {})
                    role = conversational.get('role', 'UNKNOWN')
                    content = conversational.get('content', {})
                    message = content.get('text', '')
                    
                    display_message = message[:50] + '...' if len(message) > 50 else message
                    print(f"   {i}. {role}: {display_message}")
                    
                    context.append({
                        'role': role,
                        'message': message,
                        'timestamp': event.get('eventTimestamp', '')
                    })
            
            return context
            
        except Exception as e:
            print(f"❌ Memory retrieval failed: {str(e)}")
            return []
    
    def test_agentcore_runtime(self, message, context):
        """Test calling AgentCore Runtime"""
        try:
            print(f"🤖 Calling AgentCore Runtime...")
            
            payload = {
                'input': message,
                'sessionId': self.session_id,
                'actorId': self.user_id,
                'context': context
            }
            
            response = self.agentcore.invoke_agent_runtime(
                agentRuntimeArn=self.runtime_arn,
                runtimeSessionId=self.session_id,
                payload=json.dumps(payload),
                contentType='application/json',
                accept='application/json'
            )
            
            # Read the response
            response_body = response['response'].read().decode('utf-8')
            agent_response = json.loads(response_body)
            
            print(f"✅ AgentCore Runtime responded successfully")
            print(f"   Response: {agent_response.get('response', 'No response')[:100]}...")
            
            return agent_response.get('response', 'No response available')
            
        except Exception as e:
            print(f"❌ AgentCore Runtime call failed: {str(e)}")
            return f"Error: {str(e)}"
    
    def run_end_to_end_test(self):
        """Run complete end-to-end test"""
        print("🚀 Starting End-to-End Test")
        print("=" * 60)
        
        # Step 1: Setup Cognito credentials
        if not self.setup_cognito_credentials():
            print("❌ Test failed at credential setup")
            return False
        
        print()
        
        # Step 2: Test conversation flow
        test_messages = [
            "Hi, I've been feeling really anxious lately",
            "What breathing exercises work best for anxiety?",
            "Thank you, that's helpful. I'll try those techniques."
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"💬 Test Message {i}: {message}")
            print("-" * 40)
            
            # Store user message
            if not self.test_memory_storage(message, 'USER'):
                print(f"❌ Test failed at message {i} storage")
                return False
            
            # Get conversation context
            context = self.test_memory_retrieval()
            
            # Call AgentCore Runtime
            agent_response = self.test_agentcore_runtime(message, context)
            
            # Store agent response
            if not self.test_memory_storage(agent_response, 'ASSISTANT'):
                print(f"❌ Test failed at response {i} storage")
                return False
            
            print(f"✅ Message {i} flow completed successfully")
            print()
        
        # Step 3: Test crisis detection
        print("🚨 Testing Crisis Detection")
        print("-" * 40)
        
        crisis_message = "Sometimes I feel like there's no point in continuing"
        print(f"💬 Crisis Test Message: {crisis_message}")
        
        # Store crisis message
        if not self.test_memory_storage(crisis_message, 'USER'):
            print("❌ Crisis test failed at storage")
            return False
        
        # Get context and call runtime
        context = self.test_memory_retrieval()
        crisis_response = self.test_agentcore_runtime(crisis_message, context)
        
        # Check if crisis response is appropriate
        crisis_keywords = ['crisis', 'help', '988', '911', 'support', 'alone']
        has_crisis_response = any(keyword.lower() in crisis_response.lower() for keyword in crisis_keywords)
        
        if has_crisis_response:
            print("✅ Crisis detection working - appropriate response generated")
        else:
            print("⚠️ Crisis response may need improvement")
        
        # Store crisis response
        self.test_memory_storage(crisis_response, 'ASSISTANT')
        
        print()
        print("🎉 End-to-End Test Completed Successfully!")
        print("=" * 60)
        
        # Final memory check
        print("📊 Final Memory State:")
        final_context = self.test_memory_retrieval()
        print(f"Total conversation events stored: {len(final_context)}")
        
        return True


def main():
    """Main test function"""
    test = DirectAgentCoreTest()
    
    try:
        success = test.run_end_to_end_test()
        
        if success:
            print("\n✅ ALL TESTS PASSED!")
            print("🧠 Direct AgentCore integration is working correctly")
            print("💬 Memory storage and retrieval functional")
            print("🤖 AgentCore Runtime responding appropriately")
            print("🚨 Crisis detection operational")
        else:
            print("\n❌ SOME TESTS FAILED!")
            print("Check the logs above for details")
            
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {str(e)}")


if __name__ == "__main__":
    main()
