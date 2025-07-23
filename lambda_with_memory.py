import json
import boto3
import uuid
from datetime import datetime

# Initialize clients
agentcore = boto3.client('bedrock-agentcore', region_name='us-east-1')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Configuration
MEMORY_ID = "MentalHealthChatbotMemory-GqmjCf2KIw"
RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"  # Use available model

def lambda_handler(event, context):
    """Enhanced Lambda with AgentCore Memory"""
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }
    
    if event['httpMethod'] == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        body = json.loads(event['body'])
        user_input = body.get('input', '')
        session_id = body.get('sessionId', str(uuid.uuid4()))
        actor_id = body.get('userId', f'user_{uuid.uuid4().hex[:8]}')
        
        if not user_input:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'No input provided'})
            }
        
        # Store user message in memory
        store_event(actor_id, session_id, user_input, "USER")
        
        # Get conversation context
        context_messages = get_context(actor_id, session_id)
        
        # Detect crisis
        crisis_detected = detect_crisis(user_input)
        
        # Generate response with context
        agent_response = generate_response(user_input, context_messages, crisis_detected)
        
        # Store agent response
        store_event(actor_id, session_id, agent_response, "ASSISTANT")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': agent_response,
                'sessionId': session_id,
                'actorId': actor_id,
                'crisisDetected': crisis_detected,
                'contextUsed': len(context_messages),
                'memoryEnabled': True,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': 'I apologize for the technical difficulty. If you are in crisis, please contact emergency services immediately.'
            })
        }

def store_event(actor_id, session_id, message, role):
    """Store event in AgentCore Memory"""
    try:
        agentcore.create_event(
            memoryId=MEMORY_ID,
            actorId=actor_id,
            sessionId=session_id,
            eventTimestamp=datetime.now().isoformat(),
            payload={
                'message': message,
                'role': role,
                'timestamp': datetime.now().isoformat()
            }
        )
        print(f"✅ Stored {role} message in memory")
    except Exception as e:
        print(f"⚠️ Memory storage failed: {str(e)}")

def get_context(actor_id, session_id):
    """Get conversation context from memory"""
    try:
        response = agentcore.list_events(
            memoryId=MEMORY_ID,
            actorId=actor_id,
            sessionId=session_id,
            maxResults=10
        )
        
        messages = []
        for event in response.get('events', []):
            payload = event.get('payload', {})
            messages.append({
                'message': payload.get('message', ''),
                'role': payload.get('role', ''),
                'timestamp': payload.get('timestamp', '')
            })
        
        print(f"📚 Retrieved {len(messages)} context messages")
        return messages[-6:]  # Last 6 messages for context
        
    except Exception as e:
        print(f"⚠️ Context retrieval failed: {str(e)}")
        return []

def detect_crisis(message):
    """Detect crisis keywords"""
    crisis_keywords = [
        'suicide', 'kill myself', 'end it all', 'want to die', 'better off dead',
        'hurt myself', 'self harm', 'no point living', 'give up'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in crisis_keywords)

def generate_response(user_input, context, crisis_detected):
    """Generate response with memory context"""
    
    # Build context string
    context_str = ""
    if context:
        context_str = "\n\nRecent conversation:\n"
        for msg in context:
            role = "User" if msg['role'] == 'USER' else "Assistant"
            context_str += f"{role}: {msg['message']}\n"
    
    # Crisis response
    if crisis_detected:
        return "I'm very concerned about what you're sharing. Your life has value and there are people who want to help. Please reach out to the National Suicide Prevention Lifeline at 988 or emergency services at 911 immediately. You don't have to go through this alone."
    
    # Build prompt with context
    prompt = f"""You are a compassionate mental health support agent. Provide empathetic, supportive responses.

{context_str}

Current user message: {user_input}

Respond with empathy and support. Be warm, non-judgmental, and reference previous conversation when relevant. Keep responses concise but meaningful.

Response:"""

    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text'].strip()
        
    except Exception as e:
        print(f"❌ Model error: {str(e)}")
        return "I'm here to listen and support you. While I'm having technical difficulties, please know that your feelings are valid and help is available. If you're in crisis, please contact a mental health professional immediately."
