import json
import boto3
import uuid
from datetime import datetime

def lambda_handler(event, context):
    """
    Lambda function to proxy chat requests to AgentCore Runtime
    """
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }
    
    # Handle preflight OPTIONS request
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_input = body.get('input', '')
        session_id = body.get('sessionId', str(uuid.uuid4()))
        
        if not user_input:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'No input provided'
                })
            }
        
        # Initialize AgentCore client
        agentcore = boto3.client('bedrock-agentcore', region_name='us-east-1')
        
        # Call AgentCore Runtime
        response = agentcore.invoke_agent_runtime(
            agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I',
            runtimeSessionId=str(uuid.uuid4()),
            payload=json.dumps({
                'input': user_input,
                'sessionId': session_id
            }),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse AgentCore response
        response_body = response['response'].read().decode('utf-8')
        agent_response = json.loads(response_body)
        
        # Return formatted response
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': agent_response.get('response', 'I apologize, but I encountered an error processing your request.'),
                'sessionId': session_id,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        
        # Return error response
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': 'I apologize, but I\'m having technical difficulties. If you\'re in crisis, please contact emergency services or a crisis hotline immediately.'
            })
        }
