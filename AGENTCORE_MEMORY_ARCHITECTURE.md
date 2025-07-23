# 🧠 AgentCore Memory Architecture for Mental Health Chatbot

## 🏗️ **Complete Application Flow with Memory**

### **Architecture Overview**
```
User Browser → CloudFront → S3 Static Website → AgentCore Memory → AgentCore Runtime → Mental Health Agent
                                                      ↓
                                              Short-term Memory (Events)
                                                      ↓
                                              Long-term Memory (Extracted Insights)
```

## 📋 **Deployment Steps**

### **Step 1: Create AgentCore Memory Resource**
```python
# Create memory with multiple strategies for mental health
memory = client.create_memory_and_wait(
    name='MentalHealthChatbotMemory',
    strategies=[
        {
            # User communication preferences, coping strategies, triggers
            'userPreferenceMemoryStrategy': {
                'name': 'MentalHealthUserPreferences',
                'namespaces': ['/users/{actorId}/preferences']
            }
        },
        {
            # Session summaries, mood tracking, therapeutic progress
            'summaryMemoryStrategy': {
                'name': 'TherapeuticSessionSummarizer', 
                'namespaces': ['/sessions/{actorId}/{sessionId}']
            }
        },
        {
            # Mental health knowledge, crisis patterns, resources
            'semanticMemoryStrategy': {
                'name': 'MentalHealthKnowledge',
                'namespaces': ['/knowledge/{actorId}', '/crisis-patterns/{actorId}']
            }
        }
    ]
)
```

### **Step 2: Configure AgentCore Runtime with Memory**
```python
# Link memory to our existing runtime
agentcore_control.update_agent_runtime(
    agentRuntimeId='mental_health_support_agent-lRczXz8e6I',
    memoryConfiguration={
        'memoryArn': memory_arn,
        'enableShortTermMemory': True,
        'enableLongTermMemory': True
    }
)
```

### **Step 3: Update Lambda Function (or Direct Integration)**
```python
# Enhanced handler with memory integration
def lambda_handler(event, context):
    # Store user message in short-term memory
    memory_client.create_event(
        memory_id=MEMORY_ID,
        actor_id=user_id,
        session_id=session_id,
        messages=[(user_input, "USER")]
    )
    
    # Get conversation context
    context = memory_client.list_events(
        memory_id=MEMORY_ID,
        actor_id=user_id,
        session_id=session_id
    )
    
    # Get user preferences from long-term memory
    preferences = memory_client.retrieve_memories(
        memory_id=MEMORY_ID,
        namespace=f"/users/{user_id}/preferences",
        query="communication style and coping strategies"
    )
    
    # Call AgentCore with enriched context
    response = agentcore.invoke_agent_runtime(
        agentRuntimeArn=RUNTIME_ARN,
        runtimeSessionId=session_id,
        payload=json.dumps({
            'input': user_input,
            'context': context,
            'preferences': preferences
        })
    )
```

### **Step 4: Update Frontend for Memory Integration**
```javascript
class MentalHealthChatbotWithMemory {
    async sendMessage() {
        // Send message with user ID for memory tracking
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            body: JSON.stringify({
                input: message,
                sessionId: this.sessionId,
                userId: this.userId  // For memory actor_id
            })
        });
        
        // Handle memory-enhanced responses
        const data = await response.json();
        
        // Display personalized response
        this.addMessage(data.response, 'agent');
        
        // Handle crisis detection from memory patterns
        if (data.crisisDetected) {
            this.showCrisisModal();
        }
    }
}
```

## 🔄 **Complete User Interaction Flow**

### **1. User Opens Website**
```
User → https://d3nlpr9no3kmjc.cloudfront.net
├── CloudFront serves static files
├── JavaScript initializes with user ID
├── Loads previous session preferences (if any)
└── Ready for conversation
```

### **2. First Message in New Session**
```
User: "Hi, I've been feeling really anxious lately"
├── Frontend sends to API with userId + sessionId
├── Lambda stores message in short-term memory
├── No previous context for this session
├── Checks long-term memory for user preferences
├── AgentCore processes with available context
└── Response: Personalized based on any known preferences
```

### **3. Continuing Conversation (Short-term Memory)**
```
User: "What breathing exercises work best?"
├── Lambda retrieves recent conversation from short-term memory
├── Context: Previous anxiety discussion
├── AgentCore has full conversation context
├── Response: Builds on previous discussion
└── Stores new exchange in short-term memory
```

### **4. Crisis Detection & Long-term Storage**
```
User: "Sometimes I feel like there's no point in continuing"
├── Crisis keywords detected
├── Stored in short-term memory as critical event
├── Long-term memory extracts crisis pattern
├── Semantic strategy stores in /crisis-patterns/{userId}
├── Immediate crisis response triggered
└── Admin alert sent + crisis resources shown
```

### **5. Return User (Long-term Memory)**
```
User returns after 1 week: "Hi, I'm back"
├── Same userId, new sessionId
├── Short-term memory: Empty (new session)
├── Long-term memory retrieved:
│   ├── User preferences: Prefers breathing exercises
│   ├── Session summaries: Previous anxiety discussions
│   └── Crisis patterns: Monitor for recurring themes
├── AgentCore personalizes response based on history
└── Response: "Welcome back! How have the breathing exercises been working?"
```

## 🧠 **Memory Strategies for Mental Health**

### **Short-term Memory (Raw Conversations)**
- **Purpose**: Maintain context within single session
- **Storage**: Raw conversation events
- **Retention**: Session-based
- **Use Cases**:
  - Follow-up questions in same conversation
  - Referencing earlier topics in session
  - Maintaining therapeutic flow

### **Long-term Memory Strategies**

#### **1. User Preferences Strategy**
```
Namespace: /users/{actorId}/preferences
Extracts:
- Communication style preferences
- Effective coping strategies
- Triggers and stressors
- Preferred therapeutic approaches
- Crisis warning signs
```

#### **2. Session Summary Strategy**
```
Namespace: /sessions/{actorId}/{sessionId}
Extracts:
- Session outcomes and progress
- Mood changes during conversation
- Coping strategies discussed
- Action items or homework
- Crisis risk assessment
```

#### **3. Semantic Memory Strategy**
```
Namespace: /knowledge/{actorId}, /crisis-patterns/{actorId}
Extracts:
- Mental health facts and insights
- Personal crisis patterns
- Effective intervention strategies
- Relationship patterns
- Progress indicators
```

## 🔐 **Security & Privacy with Memory**

### **Data Protection**
- **Encryption**: All memory data encrypted at rest and in transit
- **Access Control**: Memory tied to specific runtime and user
- **Retention**: Configurable retention policies
- **Anonymization**: User IDs can be anonymized

### **HIPAA Considerations**
- **Audit Trails**: All memory access logged
- **Data Minimization**: Only therapeutic insights stored
- **User Control**: Users can request memory deletion
- **Compliance**: Built on AWS HIPAA-eligible services

## 📊 **Memory Performance & Optimization**

### **Short-term Memory**
- **Latency**: Synchronous, immediate storage/retrieval
- **Capacity**: Unlimited events per session
- **Performance**: Optimized for recent conversation context

### **Long-term Memory**
- **Processing**: Asynchronous extraction (2-3 minutes)
- **Search**: Semantic search for relevant memories
- **Consolidation**: Automatic merging of related insights
- **Optimization**: Intelligent memory consolidation

## 🎯 **Benefits of AgentCore Memory**

### **🚀 Enhanced User Experience**
- **Personalization**: Responses tailored to user history
- **Continuity**: Seamless conversation across sessions
- **Progress Tracking**: Therapeutic progress over time
- **Crisis Prevention**: Pattern recognition for early intervention

### **🔧 Simplified Architecture**
- **Native Integration**: Built for AgentCore
- **No External Databases**: Managed memory service
- **Automatic Scaling**: Handles memory growth
- **Built-in Analytics**: Memory insights and patterns

### **💰 Cost Efficiency**
- **Pay-per-Use**: Only pay for memory operations
- **No Infrastructure**: Fully managed service
- **Efficient Storage**: Intelligent memory consolidation
- **Reduced Complexity**: Fewer components to manage

## 📋 **Implementation Timeline**

### **Phase 1: Memory Setup (30 minutes)**
1. Create AgentCore Memory resource
2. Configure memory strategies
3. Link to existing runtime

### **Phase 2: Code Updates (1 hour)**
1. Update Lambda function with memory calls
2. Enhance frontend for user tracking
3. Add memory-aware error handling

### **Phase 3: Testing (30 minutes)**
1. Test short-term memory in conversations
2. Verify long-term memory extraction
3. Test crisis pattern detection

### **Phase 4: Deployment (15 minutes)**
1. Deploy updated Lambda function
2. Update frontend files in S3
3. Invalidate CloudFront cache

## 🎉 **Final Result**

A **memory-enhanced mental health chatbot** that:

- 🧠 **Remembers conversations** across sessions
- 🎯 **Personalizes responses** based on user history  
- 🚨 **Detects crisis patterns** over time
- 📈 **Tracks therapeutic progress** automatically
- 🔒 **Maintains privacy** with secure memory storage
- ⚡ **Provides continuity** for better mental health support

**This transforms our chatbot from a stateless Q&A system into an intelligent, memory-aware therapeutic companion!** 🚀

---

**Next Step**: Run `python setup_agentcore_memory.py` to implement this architecture!
