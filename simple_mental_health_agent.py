#!/usr/bin/env python3
"""
Simple Mental Health Support Agent that works without Strands
"""

import boto3
import json
import re
from datetime import datetime

class SimpleMentalHealthAgent:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.ses = boto3.client('ses', region_name='us-east-1')
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"  # Use available model
        self.admin_email = "admin.alerts.mh@example.com"
        
        # Crisis keywords
        self.crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'want to die', 'better off dead',
            'hurt myself', 'self harm', 'cut myself', 'overdose', 'jump off',
            'no point living', 'life is meaningless', 'hopeless', 'trapped',
            'can\'t go on', 'give up', 'worthless', 'burden'
        ]
        
        print("✅ Simple Mental Health Agent initialized")
    
    def detect_crisis(self, message):
        """Detect crisis indicators in user message"""
        message_lower = message.lower()
        
        detected_keywords = []
        for keyword in self.crisis_keywords:
            if keyword in message_lower:
                detected_keywords.append(keyword)
        
        if detected_keywords:
            return {
                'risk_level': 'HIGH',
                'indicators': detected_keywords,
                'alert_needed': True
            }
        
        # Check for moderate risk indicators
        moderate_keywords = ['depressed', 'anxious', 'panic', 'overwhelmed', 'scared', 'alone']
        moderate_detected = [kw for kw in moderate_keywords if kw in message_lower]
        
        if moderate_detected:
            return {
                'risk_level': 'MODERATE',
                'indicators': moderate_detected,
                'alert_needed': False
            }
        
        return {
            'risk_level': 'LOW',
            'indicators': [],
            'alert_needed': False
        }
    
    def send_crisis_alert(self, user_message, risk_assessment):
        """Send crisis alert email"""
        try:
            subject = f"MENTAL HEALTH CRISIS ALERT - {risk_assessment['risk_level']} RISK"
            
            body = f"""
URGENT: Mental Health Crisis Detected

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Risk Level: {risk_assessment['risk_level']}

CRISIS INDICATORS DETECTED:
{', '.join(risk_assessment['indicators'])}

USER MESSAGE:
"{user_message}"

IMMEDIATE ACTION REQUIRED:
- Review conversation immediately
- Consider emergency intervention
- Provide crisis resources
- Document incident

This is an automated alert from the Mental Health Support Agent.
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
    
    def generate_response(self, user_message, conversation_history):
        """Generate empathetic response using Claude"""
        
        # Build conversation context
        context = "You are a compassionate mental health support agent. Provide empathetic, supportive responses."
        
        if conversation_history:
            context += "\n\nPrevious conversation:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                context += f"User: {msg.get('user', '')}\nAgent: {msg.get('agent', '')}\n"
        
        prompt = f"""
{context}

Current user message: {user_message}

Please respond with empathy and support. Guidelines:
- Be warm and non-judgmental
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
    
    def chat(self, user_message, conversation_history=None):
        """Main chat function"""
        if conversation_history is None:
            conversation_history = []
        
        print(f"📥 Processing: {user_message}")
        
        # Detect crisis
        risk_assessment = self.detect_crisis(user_message)
        
        # Send alert if needed
        if risk_assessment['alert_needed']:
            self.send_crisis_alert(user_message, risk_assessment)
        
        # Generate response
        response = self.generate_response(user_message, conversation_history)
        
        # Add to conversation history
        conversation_history.append({
            'user': user_message,
            'agent': response,
            'timestamp': datetime.now().isoformat(),
            'risk_level': risk_assessment['risk_level']
        })
        
        print(f"📤 Response: {response[:100]}...")
        return response

# Test function
if __name__ == "__main__":
    agent = SimpleMentalHealthAgent()
    
    # Test messages
    test_messages = [
        "Hi, I've been feeling really anxious lately",
        "I can't cope anymore, I just want to end it all"
    ]
    
    conversation = []
    for msg in test_messages:
        response = agent.chat(msg, conversation)
        print(f"\nUser: {msg}")
        print(f"Agent: {response}")
        print("-" * 50)
