
import json
import os
import sys
import traceback
from mental_health_agent import MentalHealthAgent

# Initialize the agent
print("Initializing Mental Health Agent...")
try:
    agent = MentalHealthAgent()
    print("✅ Agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing agent: {str(e)}")
    traceback.print_exc()

conversation_histories = {}

def handler(event, context=None):
    """
    AgentCore Runtime handler for mental health agent
    """
    print(f"📥 Received event: {json.dumps(event, default=str)}")
    
    try:
        # Extract session information
        session_id = event.get('sessionId', 'default')
        user_input = event.get('input', '')
        
        if not user_input:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No input provided',
                    'message': 'Please provide an input message'
                })
            }
        
        print(f"Processing request for session: {session_id}")
        print(f"User input: {user_input}")
        
        # Get or create conversation history for this session
        if session_id not in conversation_histories:
            conversation_histories[session_id] = []
        
        # Process the user input through the mental health agent
        response = agent.chat(user_input, conversation_histories[session_id])
        
        print(f"Agent response: {response}")
        
        # Return response in AgentCore format
        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': response,
                'sessionId': session_id,
                'timestamp': context.aws_request_id if context else None,
                'metadata': {
                    'model': 'claude-sonnet-4',
                    'framework': 'strands-agents',
                    'agent': 'mental-health-support'
                }
            })
        }
        
    except Exception as e:
        print(f"❌ Error processing request: {str(e)}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Internal server error in mental health agent'
            })
        }

# For testing locally
if __name__ == "__main__":
    test_event = {
        'input': 'Hello, I need some help with anxiety',
        'sessionId': 'test-session'
    }
    result = handler(test_event)
    print("Test result:", json.dumps(result, indent=2))
