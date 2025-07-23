
import json
import os
from mental_health_agent import MentalHealthAgent

# Initialize the agent
agent = MentalHealthAgent()
conversation_histories = {}

def handler(event, context):
    """
    AgentCore Runtime handler for mental health agent
    """
    try:
        # Extract session information
        session_id = event.get('sessionId', 'default')
        user_input = event.get('input', '')
        
        print(f"Processing request for session: {session_id}")
        print(f"User input: {user_input}")
        
        # Get or create conversation history for this session
        if session_id not in conversation_histories:
            conversation_histories[session_id] = []
        
        # Process the user input through the mental health agent
        response = agent.chat(user_input, conversation_histories[session_id])
        
        # Return response in AgentCore format
        return {
            'statusCode': 200,
            'body': {
                'response': response,
                'sessionId': session_id,
                'timestamp': context.aws_request_id if context else None,
                'metadata': {
                    'model': 'claude-sonnet-4',
                    'framework': 'strands-agents',
                    'agent': 'mental-health-support'
                }
            }
        }
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'message': 'Internal server error in mental health agent'
            }
        }
