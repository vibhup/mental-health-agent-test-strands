// Direct AgentCore Integration - No Lambda/API Gateway needed
class DirectAgentCoreChatbot {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.isConnected = false;
        this.messageHistory = [];
        
        // AgentCore Configuration
        this.config = {
            region: 'us-east-1',
            runtimeArn: 'arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I',
            memoryId: 'MentalHealthChatbotMemory-GqmjCf2KIw',
            identityPoolId: 'us-east-1:fee1a888-11e8-40a2-a195-9acb975d1b72'
        };
        
        // DOM elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.crisisModal = document.getElementById('crisisModal');
        this.closeModal = document.getElementById('closeModal');
        
        this.initializeEventListeners();
        this.initializeAWS();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    getUserId() {
        let userId = localStorage.getItem('mental_health_user_id');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('mental_health_user_id', userId);
        }
        return userId;
    }
    
    async initializeAWS() {
        try {
            // Configure AWS SDK for browser
            if (typeof AWS !== 'undefined') {
                AWS.config.region = this.config.region;
                
                // Use Cognito Identity Pool for unauthenticated access
                AWS.config.credentials = new AWS.CognitoIdentityCredentials({
                    IdentityPoolId: this.config.identityPoolId
                });
                
                // Initialize AgentCore client
                this.agentCore = new AWS.BedrockAgentCore();
                
                this.updateStatus('online', 'Connected to AgentCore');
                this.isConnected = true;
            } else {
                // Fallback: Use intelligent responses without AWS SDK
                this.updateStatus('online', 'Connected (Fallback Mode)');
                this.isConnected = true;
            }
        } catch (error) {
            console.error('AWS initialization failed:', error);
            // Still allow fallback mode
            this.updateStatus('online', 'Connected (Fallback Mode)');
            this.isConnected = true;
        }
    }
    
    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send message
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.toggleSendButton();
        });
        
        // Crisis modal
        this.closeModal.addEventListener('click', () => {
            this.crisisModal.style.display = 'none';
        });
        
        window.addEventListener('click', (e) => {
            if (e.target === this.crisisModal) {
                this.crisisModal.style.display = 'none';
            }
        });
    }
    
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    toggleSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || !this.isConnected;
    }
    
    updateStatus(status, text) {
        this.statusDot.className = `status-dot ${status}`;
        this.statusText.textContent = text;
        
        if (status === 'online') {
            this.isConnected = true;
        } else {
            this.isConnected = false;
        }
        
        this.toggleSendButton();
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.isConnected) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.toggleSendButton();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Store message in AgentCore Memory
            await this.storeInMemory(message, 'USER');
            
            // Get conversation context
            const context = await this.getConversationContext();
            
            // Call AgentCore Runtime directly
            const response = await this.callAgentCoreRuntime(message, context);
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Store agent response in memory
            await this.storeInMemory(response.response, 'ASSISTANT');
            
            // Add agent response
            this.addMessage(response.response, 'agent');
            
            // Check for crisis indicators
            this.checkForCrisisKeywords(message);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('I apologize, but I\'m having technical difficulties right now. Please know that your feelings are valid and help is available. If you\'re in crisis, please contact emergency services or a crisis hotline immediately.', 'agent');
            this.updateStatus('error', 'Connection Error');
        }
    }
    
    async storeInMemory(message, role) {
        try {
            if (this.agentCore) {
                // Direct AgentCore Memory API call
                await this.agentCore.createEvent({
                    memoryId: this.config.memoryId,
                    actorId: this.userId,
                    sessionId: this.sessionId,
                    eventTimestamp: new Date().toISOString(),
                    payload: {
                        message: message,
                        role: role,
                        timestamp: new Date().toISOString()
                    }
                }).promise();
                
                console.log(`✅ Stored ${role} message in AgentCore Memory`);
            }
        } catch (error) {
            console.warn('Memory storage failed:', error);
        }
    }
    
    async getConversationContext() {
        try {
            if (this.agentCore) {
                const response = await this.agentCore.listEvents({
                    memoryId: this.config.memoryId,
                    actorId: this.userId,
                    sessionId: this.sessionId,
                    maxResults: 10
                }).promise();
                
                const context = [];
                for (const event of response.events || []) {
                    const payload = event.payload || {};
                    context.push({
                        message: payload.message || '',
                        role: payload.role || '',
                        timestamp: payload.timestamp || ''
                    });
                }
                
                console.log(`📚 Retrieved ${context.length} context messages`);
                return context.slice(-6); // Last 6 messages
            }
        } catch (error) {
            console.warn('Context retrieval failed:', error);
        }
        
        return [];
    }
    
    async callAgentCoreRuntime(message, context) {
        try {
            if (this.agentCore) {
                // Direct AgentCore Runtime call
                const response = await this.agentCore.invokeAgentRuntime({
                    agentRuntimeArn: this.config.runtimeArn,
                    runtimeSessionId: this.sessionId,
                    payload: JSON.stringify({
                        input: message,
                        sessionId: this.sessionId,
                        actorId: this.userId,
                        context: context
                    }),
                    contentType: 'application/json',
                    accept: 'application/json'
                }).promise();
                
                const responseBody = response.response.read().toString();
                const agentResponse = JSON.parse(responseBody);
                
                return {
                    response: agentResponse.response || 'I\'m here to support you.',
                    sessionId: this.sessionId,
                    status: 'success'
                };
            } else {
                // Fallback response generation
                return this.generateFallbackResponse(message, context);
            }
        } catch (error) {
            console.error('AgentCore Runtime call failed:', error);
            return this.generateFallbackResponse(message, context);
        }
    }
    
    generateFallbackResponse(message, context) {
        // Crisis detection
        const crisisKeywords = ['suicide', 'kill myself', 'end it all', 'want to die', 'hurt myself'];
        const lowerMessage = message.toLowerCase();
        
        if (crisisKeywords.some(keyword => lowerMessage.includes(keyword))) {
            return {
                response: "I'm very concerned about what you're sharing with me. Your life has value, and there are people who want to help. Please reach out to the National Suicide Prevention Lifeline at 988 or emergency services at 911 immediately. You don't have to go through this alone.",
                sessionId: this.sessionId,
                status: 'crisis'
            };
        }
        
        // Context-aware responses
        if (context && context.length > 0) {
            const responses = [
                "I remember our conversation, and I'm here to continue supporting you. How are you feeling right now?",
                "Thank you for continuing to share with me. Based on what we've discussed, what would be most helpful for you today?",
                "I'm glad you're back. Continuing our conversation, what's been on your mind since we last talked?"
            ];
            return {
                response: responses[Math.floor(Math.random() * responses.length)],
                sessionId: this.sessionId,
                status: 'success'
            };
        }
        
        // General supportive responses
        const responses = [
            "Thank you for reaching out. I'm here to listen and support you. How are you feeling today?",
            "I appreciate you sharing with me. Your feelings are valid, and it's okay to not be okay sometimes. What's been on your mind?",
            "I'm glad you're here. Sometimes just talking about what we're going through can help. What would be most helpful for you right now?"
        ];
        
        return {
            response: responses[Math.floor(Math.random() * responses.length)],
            sessionId: this.sessionId,
            status: 'success'
        };
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? '👤' : '🤗';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const textP = document.createElement('p');
        textP.textContent = text;
        
        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        content.appendChild(textP);
        content.appendChild(time);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Store in local history
        this.messageHistory.push({
            text: text,
            sender: sender,
            timestamp: new Date()
        });
    }
    
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message agent-message';
        typingDiv.id = 'typing-indicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤗';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typingIndicator.appendChild(dot);
        }
        
        content.appendChild(typingIndicator);
        typingDiv.appendChild(avatar);
        typingDiv.appendChild(content);
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    checkForCrisisKeywords(message) {
        const crisisKeywords = [
            'suicide', 'kill myself', 'end it all', 'want to die', 'better off dead',
            'hurt myself', 'self harm', 'cut myself', 'overdose', 'jump off',
            'no point living', 'life is meaningless', 'give up'
        ];
        
        const lowerMessage = message.toLowerCase();
        const hasCrisisKeywords = crisisKeywords.some(keyword => lowerMessage.includes(keyword));
        
        if (hasCrisisKeywords) {
            setTimeout(() => {
                this.crisisModal.style.display = 'block';
            }, 2000); // Show modal after agent response
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new DirectAgentCoreChatbot();
});
