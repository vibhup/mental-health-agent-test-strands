#!/usr/bin/env python3
"""
Mental Health Agent with AgentCore Memory Integration
"""

import json
import boto3
import uuid
from datetime import datetime

class MentalHealthAgentWithMemory:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.agentcore = boto3.client('bedrock-agentcore', region_name='us-east-1')
        self.ses = boto3.client('ses', region_name='us-east-1')
        
        # AgentCore Memory configuration
        self.memory_id = 'MentalHealthChatbotMemory-GqmjCf2KIw'
        self.memory_arn = 'arn:aws:bedrock-agentcore:us-east-1:681007183786:memory/MentalHealthChatbotMemory-GqmjCf2KIw'
        
        # AgentCore Runtime configuration
        self.runtime_arn = 'arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I'
        
        # Model configuration
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        self.admin_email = "admin.alerts.mh@example.com"
        
        # Crisis detection keywords
        self.crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'want to die', 'better off dead',
            'hurt myself', 'self harm', 'cut myself', 'overdose', 'jump off',
            'no point living', 'life is meaningless', 'hopeless', 'trapped',
            'can\'t go on', 'give up', 'worthless', 'burden'
        ]
        
        print("✅ Mental Health Agent with Memory initialized")
    
    def store_conversation_event(self, actor_id, session_id, message, role):
        """Store conversation event in AgentCore Memory"""
        try:
            # Store event in short-term memory
            response = self.agentcore.create_event(
                memoryId=self.memory_id,
                actorId=actor_id,
                sessionId=session_id,
                messages=[(message, role)]
            )
            print(f"📝 Stored {role} message in memory")
            return True
            
        except Exception as e:
            print(f"⚠️ Could not store event in memory: {str(e)}")
            return False
    
    def get_conversation_context(self, actor_id, session_id, max_results=10):
        """Retrieve conversation context from AgentCore Memory"""
        try:
            # Get recent conversation events
            response = self.agentcore.list_events(
                memoryId=self.memory_id,
                actorId=actor_id,
                sessionId=session_id,
                maxResults=max_results
            )
            
            context = []
            for event in response.get('events', []):
                for message in event.get('messages', []):
                    context.append({
                        'message': message[0],
                        'role': message[1],
                        'timestamp': event.get('timestamp')
                    })
            
            print(f"📚 Retrieved {len(context)} context messages")
            return context
            
        except Exception as e:
            print(f"⚠️ Could not retrieve context: {str(e)}")
            return []
    
    def get_user_memory_insights(self, actor_id):
        """Get user insights from long-term memory (if available)"""
        try:
            # Try to retrieve user preferences and patterns
            response = self.agentcore.retrieve_memories(
                memoryId=self.memory_id,
                namespace=f"/users/{actor_id}",
                query="user preferences communication style coping strategies"
            )
            
            insights = response.get('memories', [])
            print(f"🧠 Retrieved {len(insights)} memory insights")
            return insights
            
        except Exception as e:
            print(f"⚠️ Could not retrieve memory insights: {str(e)}")
            return []
    
    def detect_crisis(self, message):
        """Enhanced crisis detection with memory context"""
        message_lower = message.lower()
        
        detected_keywords = []
        for keyword in self.crisis_keywords:
            if keyword in message_lower:
                detected_keywords.append(keyword)
        
        if detected_keywords:
            return {
                'risk_level': 'HIGH',
                'indicators': detected_keywords,
                'alert_needed': True,
                'timestamp': datetime.now().isoformat()
            }
        
        # Check for moderate risk indicators
        moderate_keywords = ['depressed', 'anxious', 'panic', 'overwhelmed', 'scared', 'alone']
        moderate_detected = [kw for kw in moderate_keywords if kw in message_lower]
        
        if moderate_detected:
            return {
                'risk_level': 'MODERATE',
                'indicators': moderate_detected,
                'alert_needed': False,
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'risk_level': 'LOW',
            'indicators': [],
            'alert_needed': False,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_memory_enhanced_response(self, user_message, context, insights):
        """Generate response using conversation context and user insights"""
        
        # Build enhanced prompt with memory context
        context_text = ""
        if context:
            context_text = "\\n\\nRecent conversation context:\\n"
            for msg in context[-5:]:  # Last 5 messages
                role = "User" if msg['role'] == 'USER' else "Assistant"
                context_text += f"{role}: {msg['message']}\\n"
        
        insights_text = ""
        if insights:
            insights_text = "\\n\\nUser insights from previous conversations:\\n"
            for insight in insights[:3]:  # Top 3 insights
                insights_text += f"- {insight.get('content', '')}\\n"
        
        prompt = f"""
You are a compassionate mental health support agent. Provide empathetic, supportive responses.

{context_text}

{insights_text}

Current user message: {user_message}

Please respond with empathy and support. Guidelines:
- Be warm and non-judgmental
- Reference previous conversation context when relevant
- Adapt to user's communication style from insights
- Ask thoughtful follow-up questions
- Validate their feelings
- Encourage professional help when appropriate
- Provide hope and support
- Keep responses concise but meaningful

Response:"""

        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text'].strip()
            
        except Exception as e:
            print(f"❌ Error generating response: {str(e)}")
            return "I'm here to listen and support you. While I'm having technical difficulties right now, please know that your feelings are valid and help is available. If you're in crisis, please contact a mental health professional or crisis hotline immediately."
    
    def send_crisis_alert(self, actor_id, user_message, risk_assessment):
        """Send crisis alert with memory context"""
        try:
            subject = f"MENTAL HEALTH CRISIS ALERT - {risk_assessment['risk_level']} RISK"
            
            body = f"""
URGENT: Mental Health Crisis Detected

Timestamp: {risk_assessment['timestamp']}
User ID: {actor_id}
Risk Level: {risk_assessment['risk_level']}

CRISIS INDICATORS DETECTED:
{', '.join(risk_assessment['indicators'])}

USER MESSAGE:
"{user_message}"

MEMORY CONTEXT:
This alert includes context from the user's conversation history stored in AgentCore Memory.
Memory ID: {self.memory_id}

IMMEDIATE ACTION REQUIRED:
- Review conversation immediately
- Consider emergency intervention
- Provide crisis resources
- Document incident
- Check user's conversation history in memory system

This is an automated alert from the Mental Health Support Agent with Memory.
"""
            
            # Note: This would fail without SES setup, but we'll catch the error
            response = self.ses.send_email(
                Source='noreply@example.com',
                Destination={'ToAddresses': [self.admin_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            print(f"🚨 Crisis alert sent! MessageId: {response.get('MessageId', 'N/A')}")
            
        except Exception as e:
            print(f"⚠️ Could not send email alert (SES not configured): {str(e)}")
            print(f"🚨 CRISIS DETECTED: {risk_assessment}")
    
    def chat_with_memory(self, user_message, actor_id, session_id):
        """Main chat function with memory integration"""
        
        print(f"📥 Processing message from {actor_id} in session {session_id}")
        print(f"Message: {user_message}")
        
        # Step 1: Store user message in memory
        self.store_conversation_event(actor_id, session_id, user_message, "USER")
        
        # Step 2: Get conversation context from memory
        context = self.get_conversation_context(actor_id, session_id)
        
        # Step 3: Get user insights from long-term memory
        insights = self.get_user_memory_insights(actor_id)
        
        # Step 4: Detect crisis
        risk_assessment = self.detect_crisis(user_message)
        
        # Step 5: Send alert if needed
        if risk_assessment['alert_needed']:
            self.send_crisis_alert(actor_id, user_message, risk_assessment)
        
        # Step 6: Generate memory-enhanced response
        response = self.generate_memory_enhanced_response(user_message, context, insights)
        
        # Step 7: Store agent response in memory
        self.store_conversation_event(actor_id, session_id, response, "ASSISTANT")
        
        print(f"📤 Response: {response[:100]}...")
        
        return {
            'response': response,
            'risk_assessment': risk_assessment,
            'context_used': len(context),
            'insights_used': len(insights),
            'memory_id': self.memory_id,
            'session_id': session_id,
            'actor_id': actor_id
        }


# Lambda handler for API Gateway integration
def lambda_handler(event, context):
    """
    Lambda handler with AgentCore Memory integration
    """
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }
    
    if event['httpMethod'] == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        # Initialize agent with memory
        agent = MentalHealthAgentWithMemory()
        
        # Parse request
        body = json.loads(event['body'])
        user_input = body.get('input', '')
        session_id = body.get('sessionId', str(uuid.uuid4()))
        actor_id = body.get('userId', 'anonymous_user')
        
        if not user_input:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'No input provided'})
            }
        
        # Process with memory
        result = agent.chat_with_memory(user_input, actor_id, session_id)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': result['response'],
                'sessionId': session_id,
                'actorId': actor_id,
                'crisisDetected': result['risk_assessment']['alert_needed'],
                'riskLevel': result['risk_assessment']['risk_level'],
                'memoryContext': {
                    'contextMessages': result['context_used'],
                    'insights': result['insights_used'],
                    'memoryId': result['memory_id']
                },
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': 'I apologize, but I am having technical difficulties. If you are in crisis, please contact emergency services immediately.'
            })
        }


# Test function
if __name__ == "__main__":
    agent = MentalHealthAgentWithMemory()
    
    # Test conversation with memory
    actor_id = "test_user_123"
    session_id = "test_session_456"
    
    test_messages = [
        "Hi, I've been feeling really anxious lately",
        "What breathing exercises work best?",
        "Sometimes I feel like there's no point in continuing"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\\n{'='*50}")
        print(f"Test Message {i}")
        print(f"{'='*50}")
        
        result = agent.chat_with_memory(message, actor_id, session_id)
        
        print(f"\\nUser: {message}")
        print(f"Agent: {result['response']}")
        print(f"Risk Level: {result['risk_assessment']['risk_level']}")
        print(f"Context Used: {result['context_used']} messages")
        print(f"Insights Used: {result['insights_used']} insights")
        
        if result['risk_assessment']['alert_needed']:
            print("🚨 CRISIS ALERT TRIGGERED!")
