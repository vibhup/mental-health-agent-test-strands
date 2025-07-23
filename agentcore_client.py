#!/usr/bin/env python3
"""
Client for interacting with deployed Mental Health Agent on Bedrock AgentCore Runtime
"""

import boto3
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime

class AgentCoreClient:
    def __init__(self, agent_id: str, alias_name: str = 'production', region: str = 'us-east-1'):
        self.bedrock_agent_core = boto3.client('bedrock-agentcore-runtime', region_name=region)
        self.agent_id = agent_id
        self.alias_name = alias_name
        self.session_id = str(uuid.uuid4())
        
    def chat(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """Send a message to the deployed agent"""
        
        if session_id:
            self.session_id = session_id
        
        try:
            response = self.bedrock_agent_core.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.alias_name,
                sessionId=self.session_id,
                inputText=message
            )
            
            # Process the response stream
            completion = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
            
            return {
                'response': completion,
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def start_conversation(self) -> str:
        """Start a new conversation session"""
        self.session_id = str(uuid.uuid4())
        return self.session_id
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session (if memory is enabled)"""
        
        try:
            response = self.bedrock_agent_core.get_agent_memory(
                agentId=self.agent_id,
                agentAliasId=self.alias_name,
                sessionId=session_id
            )
            
            return response.get('memoryContents', [])
            
        except Exception as e:
            print(f"Error retrieving session history: {str(e)}")
            return []


class WebInterface:
    """Simple web interface for the mental health agent"""
    
    def __init__(self, agent_id: str):
        self.client = AgentCoreClient(agent_id)
        
    def run_chat_interface(self):
        """Run interactive chat interface"""
        
        print("🤗 Mental Health Support Agent (AgentCore Runtime)")
        print("=" * 55)
        print("Connected to Bedrock AgentCore Runtime")
        print(f"Session ID: {self.client.session_id}")
        print("Type 'quit' to end the conversation.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nAgent: Take care of yourself. Remember, seeking help is a sign of strength. 💙")
                    break
                
                if not user_input:
                    continue
                
                # Send message to AgentCore
                print("Agent: ", end="", flush=True)
                response = self.client.chat(user_input)
                
                if 'error' in response:
                    print(f"Error: {response['error']}")
                else:
                    print(f"{response['response']}\n")
                
            except KeyboardInterrupt:
                print("\n\nAgent: Take care of yourself. Remember, you're not alone. 💙")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Agent: I'm having technical difficulties, but please know that help is available if you need it.\n")


def main():
    """Main function to run the AgentCore client"""
    
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python agentcore_client.py <agent_id>")
        print("Example: python agentcore_client.py ABCD1234EFGH")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    
    # Create and run the web interface
    interface = WebInterface(agent_id)
    interface.run_chat_interface()


if __name__ == "__main__":
    main()
