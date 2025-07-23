#!/usr/bin/env python3
"""
Mental Health Support Agent using Strands Agents SDK
This agent chats with users about mental health and alerts admin when needed.
"""

import os
import json
import re
from typing import Dict, Any, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from strands_agents import Agent, BedrockModelProvider
from strands_agents.tools import Tool


class MentalHealthAgent:
    def __init__(self):
        # Initialize AWS clients
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.ses_client = boto3.client('ses', region_name='us-east-1')
        
        # Admin email
        self.admin_email = "admin.alerts.mh@example.com"
        
        # Mental health risk indicators
        self.risk_indicators = [
            # High risk indicators
            "suicide", "kill myself", "end my life", "want to die", "better off dead",
            "self harm", "cut myself", "hurt myself", "no point living",
            "everyone would be better without me", "can't go on", "hopeless",
            
            # Medium risk indicators  
            "severely depressed", "can't cope", "overwhelming anxiety", 
            "panic attacks daily", "can't function", "completely alone",
            "nothing matters", "feel empty", "numb inside", "lost all hope",
            
            # Concerning patterns
            "drinking heavily", "using drugs to cope", "stopped eating",
            "can't sleep for days", "isolating completely", "gave up"
        ]
        
        # Initialize the Strands agent
        self.setup_agent()
    
    def setup_agent(self):
        """Setup the Strands agent with Claude Sonnet 4"""
        
        # Create model provider for Claude Sonnet 4
        model_provider = BedrockModelProvider(
            model_id="anthropic.claude-sonnet-4-20250514-v1:0",
            region="us-east-1"
        )
        
        # Create email alert tool
        email_tool = Tool(
            name="send_admin_alert",
            description="Send an alert email to admin when user shows signs of mental health crisis",
            function=self.send_admin_alert
        )
        
        # System prompt for mental health support
        system_prompt = """You are a compassionate mental health support agent. Your role is to:

1. Engage users in supportive conversation about their mental health
2. Listen actively and respond with empathy
3. Ask thoughtful follow-up questions to understand their situation
4. Provide general emotional support and coping strategies
5. Encourage professional help when appropriate

IMPORTANT GUIDELINES:
- You are NOT a replacement for professional mental health care
- Always encourage users to seek professional help for serious concerns
- Be warm, non-judgmental, and supportive
- Ask open-ended questions to encourage sharing
- Validate their feelings and experiences
- If you detect signs of crisis or severe distress, you will alert the admin

CRISIS INDICATORS to watch for:
- Mentions of suicide, self-harm, or wanting to die
- Expressions of hopelessness or feeling trapped
- Severe depression or anxiety that's impacting daily function
- Substance abuse as coping mechanism
- Complete social isolation
- Inability to cope with daily activities

Remember: Your goal is to provide support while ensuring user safety."""

        # Create the agent
        self.agent = Agent(
            name="MentalHealthSupportAgent",
            model_provider=model_provider,
            system_prompt=system_prompt,
            tools=[email_tool],
            max_iterations=10
        )
    
    def analyze_risk_level(self, conversation_text: str) -> Dict[str, Any]:
        """Analyze the conversation for mental health risk indicators"""
        
        text_lower = conversation_text.lower()
        high_risk_found = []
        medium_risk_found = []
        
        # Check for risk indicators
        for indicator in self.risk_indicators:
            if indicator in text_lower:
                if any(high_risk in indicator for high_risk in 
                      ["suicide", "kill myself", "end my life", "want to die", "self harm"]):
                    high_risk_found.append(indicator)
                else:
                    medium_risk_found.append(indicator)
        
        # Determine overall risk level
        if high_risk_found:
            risk_level = "HIGH"
        elif len(medium_risk_found) >= 2:
            risk_level = "MEDIUM"
        elif medium_risk_found:
            risk_level = "LOW"
        else:
            risk_level = "NONE"
        
        return {
            "risk_level": risk_level,
            "high_risk_indicators": high_risk_found,
            "medium_risk_indicators": medium_risk_found,
            "requires_alert": risk_level in ["HIGH", "MEDIUM"]
        }
    
    def send_admin_alert(self, user_message: str, risk_analysis: Dict[str, Any], 
                        conversation_history: List[str]) -> str:
        """Send alert email to admin about user in distress"""
        
        try:
            # Prepare email content
            subject = f"MENTAL HEALTH ALERT - Risk Level: {risk_analysis['risk_level']}"
            
            body = f"""
MENTAL HEALTH SUPPORT AGENT ALERT

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Risk Level: {risk_analysis['risk_level']}

RISK INDICATORS DETECTED:
High Risk: {', '.join(risk_analysis['high_risk_indicators']) if risk_analysis['high_risk_indicators'] else 'None'}
Medium Risk: {', '.join(risk_analysis['medium_risk_indicators']) if risk_analysis['medium_risk_indicators'] else 'None'}

LATEST USER MESSAGE:
{user_message}

CONVERSATION HISTORY:
{chr(10).join(conversation_history[-5:])}  # Last 5 messages

RECOMMENDED ACTIONS:
- Review full conversation for context
- Consider immediate outreach if high risk
- Provide appropriate mental health resources
- Document incident per protocol

This is an automated alert from the Mental Health Support Agent system.
"""

            # Send email via SES
            response = self.ses_client.send_email(
                Source='noreply@yourdomain.com',  # Replace with verified SES email
                Destination={'ToAddresses': [self.admin_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            
            return f"Admin alert sent successfully. Message ID: {response['MessageId']}"
            
        except ClientError as e:
            error_msg = f"Failed to send admin alert: {str(e)}"
            print(error_msg)
            return error_msg
    
    def chat(self, user_input: str, conversation_history: List[str] = None) -> str:
        """Main chat function that processes user input and returns response"""
        
        if conversation_history is None:
            conversation_history = []
        
        # Add user input to conversation history
        conversation_history.append(f"User: {user_input}")
        
        # Analyze risk level
        full_conversation = "\n".join(conversation_history)
        risk_analysis = self.analyze_risk_level(full_conversation)
        
        # Send alert if needed
        if risk_analysis["requires_alert"]:
            alert_result = self.send_admin_alert(user_input, risk_analysis, conversation_history)
            print(f"ALERT SENT: {alert_result}")
        
        # Get agent response
        try:
            response = self.agent.run(
                input_text=user_input,
                context={"conversation_history": conversation_history[-10:]}  # Last 10 messages
            )
            
            # Add agent response to history
            conversation_history.append(f"Agent: {response}")
            
            return response
            
        except Exception as e:
            error_response = "I'm sorry, I'm having trouble processing your message right now. Please know that your feelings are valid and if you're in crisis, please reach out to a mental health professional or crisis hotline immediately."
            conversation_history.append(f"Agent: {error_response}")
            return error_response


def main():
    """Main function to run the mental health agent"""
    
    print("🤗 Mental Health Support Agent")
    print("=" * 50)
    print("I'm here to listen and provide support. Feel free to share what's on your mind.")
    print("Type 'quit' to end the conversation.\n")
    
    # Initialize agent
    agent = MentalHealthAgent()
    conversation_history = []
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nAgent: Take care of yourself. Remember, seeking help is a sign of strength. 💙")
                break
            
            if not user_input:
                continue
            
            # Get agent response
            response = agent.chat(user_input, conversation_history)
            print(f"\nAgent: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nAgent: Take care of yourself. Remember, you're not alone. 💙")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Agent: I'm having technical difficulties, but please know that help is available if you need it.\n")


if __name__ == "__main__":
    main()
