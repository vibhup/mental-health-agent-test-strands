import json
import boto3
import uuid
from datetime import datetime, timedelta

# Initialize clients with available services
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Configuration
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I"

# Use DynamoDB for memory storage (create table if needed)
try:
    memory_table = dynamodb.Table('MentalHealthChatMemory')
except:
    memory_table = None

def lambda_handler(event, context):
    """Enhanced Lambda with memory functionality"""
    
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
        store_message(actor_id, session_id, user_input, "USER")
        
        # Get conversation context
        context_messages = get_conversation_context(actor_id, session_id)
        
        # Detect crisis
        crisis_detected = detect_crisis(user_input)
        
        # Generate response with context
        agent_response = generate_response_with_context(user_input, context_messages, crisis_detected)
        
        # Store agent response
        store_message(actor_id, session_id, agent_response, "ASSISTANT")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': agent_response,
                'sessionId': session_id,
                'actorId': actor_id,
                'crisisDetected': crisis_detected,
                'contextUsed': len(context_messages),
                'memoryEnabled': memory_table is not None,
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

def store_message(actor_id, session_id, message, role):
    """Store message in memory (DynamoDB or in-memory fallback)"""
    try:
        if memory_table:
            memory_table.put_item(
                Item={
                    'pk': f"{actor_id}#{session_id}",
                    'sk': f"{datetime.now().isoformat()}#{role}",
                    'actor_id': actor_id,
                    'session_id': session_id,
                    'message': message,
                    'role': role,
                    'timestamp': datetime.now().isoformat(),
                    'ttl': int((datetime.now() + timedelta(days=30)).timestamp())
                }
            )
            print(f"✅ Stored {role} message in DynamoDB")
        else:
            print(f"⚠️ Memory storage not available, message stored in logs only")
    except Exception as e:
        print(f"⚠️ Memory storage failed: {str(e)}")

def get_conversation_context(actor_id, session_id, limit=6):
    """Get recent conversation context"""
    try:
        if memory_table:
            response = memory_table.query(
                KeyConditionExpression='pk = :pk',
                ExpressionAttributeValues={':pk': f"{actor_id}#{session_id}"},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            messages = []
            for item in reversed(response.get('Items', [])):  # Reverse to chronological order
                messages.append({
                    'message': item.get('message', ''),
                    'role': item.get('role', ''),
                    'timestamp': item.get('timestamp', '')
                })
            
            print(f"📚 Retrieved {len(messages)} context messages from DynamoDB")
            return messages
        else:
            print("⚠️ No memory storage available")
            return []
            
    except Exception as e:
        print(f"⚠️ Context retrieval failed: {str(e)}")
        return []

def detect_crisis(message):
    """Detect crisis keywords"""
    crisis_keywords = [
        'suicide', 'kill myself', 'end it all', 'want to die', 'better off dead',
        'hurt myself', 'self harm', 'no point living', 'give up', 'hopeless'
    ]
    
    message_lower = message.lower()
    detected = any(keyword in message_lower for keyword in crisis_keywords)
    
    if detected:
        print(f"🚨 CRISIS DETECTED in message: {message[:50]}...")
    
    return detected

def generate_response_with_context(user_input, context, crisis_detected):
    """Generate response with conversation context"""
    
    # Crisis response takes priority
    if crisis_detected:
        return "I'm very concerned about what you're sharing. Your life has value and there are people who want to help. Please reach out to the National Suicide Prevention Lifeline at 988 or emergency services at 911 immediately. You don't have to go through this alone."
    
    # Build context string
    context_str = ""
    if context:
        context_str = "\\n\\nRecent conversation context:\\n"
        for msg in context[-4:]:  # Last 4 messages
            role = "User" if msg['role'] == 'USER' else "Assistant"
            context_str += f"{role}: {msg['message']}\\n"
    
    # Enhanced prompt with context
    prompt = f"""You are a compassionate mental health support agent. Provide empathetic, supportive responses.

{context_str}

Current user message: {user_input}

Guidelines:
- Be warm, empathetic, and non-judgmental
- Reference previous conversation when relevant
- Ask thoughtful follow-up questions
- Validate their feelings
- Provide hope and encouragement
- Keep responses concise but meaningful
- Suggest professional help when appropriate

Response:"""

    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        generated_response = result['content'][0]['text'].strip()
        
        print(f"✅ Generated response with context: {len(context)} messages")
        return generated_response
        
    except Exception as e:
        print(f"❌ Model error: {str(e)}")
        
        # Fallback responses based on context
        if context:
            return "I'm here to continue supporting you. While I'm having technical difficulties with my response generation, I remember our conversation and I'm still here to listen. If you're in crisis, please contact a mental health professional immediately."
        else:
            return "I'm here to listen and support you. While I'm having technical difficulties, please know that your feelings are valid and help is available. If you're in crisis, please contact a mental health professional immediately."
