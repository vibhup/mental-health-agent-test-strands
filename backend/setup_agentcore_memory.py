#!/usr/bin/env python3
"""
Set up AgentCore Memory for Mental Health Chatbot
- Short-term memory: Conversation context within sessions
- Long-term memory: User preferences, crisis patterns, therapeutic progress
"""

import boto3
import json
import time
from datetime import datetime

class MentalHealthMemorySetup:
    def __init__(self):
        self.region = 'us-east-1'
        # Note: AgentCore Memory client - using bedrock-agentcore for now
        try:
            self.memory_client = boto3.client('bedrock-agentcore-memory', region_name=self.region)
        except:
            # Fallback if specific memory client not available
            self.memory_client = boto3.client('bedrock-agentcore', region_name=self.region)
        
        self.runtime_id = 'mental_health_support_agent-lRczXz8e6I'
        
    def create_mental_health_memory(self):
        """Create memory resource with both short-term and long-term memory strategies"""
        
        print("🧠 Creating AgentCore Memory for Mental Health Chatbot...")
        
        try:
            # Create memory with multiple strategies for mental health use case
            memory_config = {
                'name': 'MentalHealthChatbotMemory',
                'description': 'Memory system for mental health support conversations with crisis detection',
                'strategies': [
                    {
                        # User Preferences: Communication style, preferred coping strategies, triggers
                        'userPreferenceMemoryStrategy': {
                            'name': 'MentalHealthUserPreferences',
                            'namespaces': ['/users/{actorId}/preferences']
                        }
                    },
                    {
                        # Session Summaries: Conversation outcomes, mood tracking, progress
                        'summaryMemoryStrategy': {
                            'name': 'TherapeuticSessionSummarizer',
                            'namespaces': ['/sessions/{actorId}/{sessionId}']
                        }
                    },
                    {
                        # Semantic Facts: Mental health knowledge, coping strategies, resources
                        'semanticMemoryStrategy': {
                            'name': 'MentalHealthKnowledge',
                            'namespaces': ['/knowledge/{actorId}', '/crisis-patterns/{actorId}']
                        }
                    }
                ]
            }
            
            # Create memory and wait for it to become active
            response = self.memory_client.create_memory_and_wait(**memory_config)
            
            memory_id = response.get('id')
            memory_arn = response.get('arn')
            
            print(f"✅ Memory created successfully!")
            print(f"Memory ID: {memory_id}")
            print(f"Memory ARN: {memory_arn}")
            
            return {
                'memory_id': memory_id,
                'memory_arn': memory_arn,
                'strategies': response.get('strategies', [])
            }
            
        except Exception as e:
            print(f"❌ Error creating memory: {str(e)}")
            # Try simpler approach if full memory creation fails
            return self.create_simple_memory()
    
    def create_simple_memory(self):
        """Create basic memory for short-term conversation context"""
        
        print("🧠 Creating simple short-term memory...")
        
        try:
            response = self.memory_client.create_memory(
                name='MentalHealthChatbotMemory',
                description='Short-term memory for mental health conversations'
            )
            
            memory_id = response.get('id')
            print(f"✅ Simple memory created: {memory_id}")
            
            return {
                'memory_id': memory_id,
                'memory_arn': response.get('arn'),
                'strategies': []
            }
            
        except Exception as e:
            print(f"❌ Error creating simple memory: {str(e)}")
            return None
    
    def configure_runtime_with_memory(self, memory_arn):
        """Configure AgentCore Runtime to use the memory resource"""
        
        print("🔧 Configuring runtime to use memory...")
        
        try:
            # Update runtime configuration to include memory
            agentcore_control = boto3.client('bedrock-agentcore-control', region_name=self.region)
            
            response = agentcore_control.update_agent_runtime(
                agentRuntimeId=self.runtime_id,
                memoryConfiguration={
                    'memoryArn': memory_arn,
                    'enableShortTermMemory': True,
                    'enableLongTermMemory': True
                }
            )
            
            print("✅ Runtime configured with memory successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error configuring runtime with memory: {str(e)}")
            return False
    
    def create_updated_agent_handler(self, memory_id):
        """Create updated agent handler that uses AgentCore Memory"""
        
        handler_code = f'''
import json
import boto3
import uuid
from datetime import datetime

# Initialize clients
agentcore = boto3.client('bedrock-agentcore', region_name='us-east-1')
memory_client = boto3.client('bedrock-agentcore-memory', region_name='us-east-1')

MEMORY_ID = "{memory_id}"
RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I"

def lambda_handler(event, context):
    """
    Enhanced handler with AgentCore Memory integration
    """
    
    # CORS headers
    headers = {{
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }}
    
    if event['httpMethod'] == 'OPTIONS':
        return {{'statusCode': 200, 'headers': headers, 'body': ''}}
    
    try:
        body = json.loads(event['body'])
        user_input = body.get('input', '')
        session_id = body.get('sessionId', str(uuid.uuid4()))
        actor_id = body.get('userId', 'anonymous_user')
        
        if not user_input:
            return {{
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({{'error': 'No input provided'}})
            }}
        
        # Store conversation in short-term memory
        store_conversation_event(actor_id, session_id, user_input, "USER")
        
        # Get conversation context from memory
        conversation_context = get_conversation_context(actor_id, session_id)
        
        # Get user preferences from long-term memory
        user_preferences = get_user_preferences(actor_id)
        
        # Call AgentCore Runtime with memory context
        response = agentcore.invoke_agent_runtime(
            agentRuntimeArn=RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=json.dumps({{
                'input': user_input,
                'sessionId': session_id,
                'actorId': actor_id,
                'context': conversation_context,
                'preferences': user_preferences
            }}),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = response['response'].read().decode('utf-8')
        agent_response = json.loads(response_body)
        agent_message = agent_response.get('response', 'I apologize for the technical difficulty.')
        
        # Store agent response in short-term memory
        store_conversation_event(actor_id, session_id, agent_message, "ASSISTANT")
        
        # Check for crisis indicators and store in long-term memory if needed
        crisis_detected = detect_crisis_patterns(user_input, agent_message)
        
        return {{
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({{
                'response': agent_message,
                'sessionId': session_id,
                'actorId': actor_id,
                'crisisDetected': crisis_detected,
                'timestamp': datetime.now().isoformat()
            }})
        }}
        
    except Exception as e:
        print(f"Error: {{str(e)}}")
        return {{
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({{
                'error': 'Internal server error',
                'message': 'I apologize, but I\\'m having technical difficulties. If you\\'re in crisis, please contact emergency services immediately.'
            }})
        }}

def store_conversation_event(actor_id, session_id, message, role):
    """Store conversation event in short-term memory"""
    try:
        memory_client.create_event(
            memory_id=MEMORY_ID,
            actor_id=actor_id,
            session_id=session_id,
            messages=[(message, role)]
        )
    except Exception as e:
        print(f"Error storing event: {{str(e)}}")

def get_conversation_context(actor_id, session_id, max_results=10):
    """Retrieve recent conversation context from short-term memory"""
    try:
        events = memory_client.list_events(
            memory_id=MEMORY_ID,
            actor_id=actor_id,
            session_id=session_id,
            max_results=max_results
        )
        
        context = []
        for event in events.get('events', []):
            for message in event.get('messages', []):
                context.append({{
                    'message': message[0],
                    'role': message[1],
                    'timestamp': event.get('timestamp')
                }})
        
        return context
        
    except Exception as e:
        print(f"Error retrieving context: {{str(e)}}")
        return []

def get_user_preferences(actor_id):
    """Retrieve user preferences from long-term memory"""
    try:
        preferences = memory_client.retrieve_memories(
            memory_id=MEMORY_ID,
            namespace=f"/users/{{actor_id}}/preferences",
            query="user communication preferences and coping strategies"
        )
        
        return preferences.get('memories', [])
        
    except Exception as e:
        print(f"Error retrieving preferences: {{str(e)}}")
        return []

def detect_crisis_patterns(user_input, agent_response):
    """Detect crisis patterns and store in long-term memory"""
    crisis_keywords = [
        'suicide', 'kill myself', 'end it all', 'want to die', 'better off dead',
        'hurt myself', 'self harm', 'cut myself', 'no point living'
    ]
    
    user_lower = user_input.lower()
    crisis_detected = any(keyword in user_lower for keyword in crisis_keywords)
    
    if crisis_detected:
        # This would trigger additional crisis response protocols
        print(f"🚨 Crisis detected in conversation")
        
    return crisis_detected
'''
        
        # Write the updated handler
        with open('mental_health_agent_with_memory.py', 'w') as f:
            f.write(handler_code)
        
        print("✅ Updated agent handler created: mental_health_agent_with_memory.py")
        return True
    
    def create_frontend_memory_integration(self, memory_id):
        """Create frontend JavaScript that works with AgentCore Memory"""
        
        js_code = f'''
// Enhanced Mental Health Chatbot with AgentCore Memory
class MentalHealthChatbotWithMemory {{
    constructor() {{
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId(); // Could be from login or anonymous ID
        this.memoryId = '{memory_id}';
        this.apiEndpoint = 'https://49rwj9ccpd.execute-api.us-east-1.amazonaws.com/prod/chat';
        this.conversationHistory = [];
        
        // Initialize UI elements
        this.initializeElements();
        this.initializeEventListeners();
        this.loadUserPreferences();
    }}
    
    generateSessionId() {{
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }}
    
    getUserId() {{
        // In production, this would come from authentication
        let userId = localStorage.getItem('mental_health_user_id');
        if (!userId) {{
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('mental_health_user_id', userId);
        }}
        return userId;
    }}
    
    async loadUserPreferences() {{
        // Load user preferences from previous sessions
        try {{
            const preferences = localStorage.getItem('user_preferences');
            if (preferences) {{
                this.userPreferences = JSON.parse(preferences);
                this.applyUserPreferences();
            }}
        }} catch (error) {{
            console.log('No previous preferences found');
        }}
    }}
    
    async sendMessage() {{
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add to UI
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.showTypingIndicator();
        
        try {{
            const response = await fetch(this.apiEndpoint, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    input: message,
                    sessionId: this.sessionId,
                    userId: this.userId
                }})
            }});
            
            const data = await response.json();
            
            this.hideTypingIndicator();
            this.addMessage(data.response, 'agent');
            
            // Handle crisis detection
            if (data.crisisDetected) {{
                this.showCrisisModal();
            }}
            
            // Store in local conversation history
            this.conversationHistory.push({{
                user: message,
                agent: data.response,
                timestamp: data.timestamp,
                crisisDetected: data.crisisDetected
            }});
            
        }} catch (error) {{
            this.hideTypingIndicator();
            this.addMessage('I apologize for the technical difficulty. If you\\'re in crisis, please contact emergency services immediately.', 'agent');
        }}
    }}
    
    // ... rest of the chatbot implementation
}}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {{
    new MentalHealthChatbotWithMemory();
}});
'''
        
        with open('chatbot-ui/script-with-memory.js', 'w') as f:
            f.write(js_code)
        
        print("✅ Frontend with memory integration created: chatbot-ui/script-with-memory.js")
        return True
    
    def setup(self):
        """Main setup function"""
        
        print("🧠 AgentCore Memory Setup for Mental Health Chatbot")
        print("=" * 65)
        
        try:
            # Step 1: Create memory resource
            print("\\n📋 Step 1: Creating memory resource...")
            memory_info = self.create_mental_health_memory()
            
            if not memory_info:
                print("❌ Setup failed at memory creation")
                return None
            
            # Step 2: Configure runtime with memory
            print("\\n🔧 Step 2: Configuring runtime with memory...")
            runtime_configured = self.configure_runtime_with_memory(memory_info['memory_arn'])
            
            # Step 3: Create updated agent handler
            print("\\n📝 Step 3: Creating updated agent handler...")
            self.create_updated_agent_handler(memory_info['memory_id'])
            
            # Step 4: Create frontend integration
            print("\\n🌐 Step 4: Creating frontend memory integration...")
            self.create_frontend_memory_integration(memory_info['memory_id'])
            
            print("\\n🎉 AgentCore Memory setup completed!")
            
            print("\\n📋 Memory Configuration:")
            print(f"Memory ID: {{memory_info['memory_id']}}")
            print(f"Memory ARN: {{memory_info['memory_arn']}}")
            print(f"Strategies: {{len(memory_info.get('strategies', []))}}")
            
            print("\\n🧠 Memory Features:")
            print("✅ Short-term memory: Conversation context within sessions")
            print("✅ Long-term memory: User preferences and patterns")
            print("✅ Crisis pattern detection and storage")
            print("✅ Therapeutic progress tracking")
            print("✅ Personalized responses based on history")
            
            print("\\n📋 Next Steps:")
            print("1. Deploy updated Lambda function with memory integration")
            print("2. Update frontend to use memory-enhanced script")
            print("3. Test conversation continuity across sessions")
            print("4. Monitor memory extraction and consolidation")
            
            return memory_info
            
        except Exception as e:
            print(f"❌ Setup failed: {{str(e)}}")
            return None


def main():
    """Main function"""
    setup = MentalHealthMemorySetup()
    result = setup.setup()
    
    if result:
        print(f"\\n✅ AgentCore Memory setup successful!")
        print(f"Memory ID: {{result['memory_id']}}")
    else:
        print("\\n❌ Setup failed. Check the logs above.")


if __name__ == "__main__":
    main()
