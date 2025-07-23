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
                
                // Wait for credentials to be obtained
                await new Promise((resolve, reject) => {
                    AWS.config.credentials.get((err) => {
                        if (err) {
                            console.error('Credentials error:', err);
                            reject(err);
                        } else {
                            console.log('✅ AWS credentials obtained');
                            resolve();
                        }
                    });
                });
                
                // Initialize the correct client for AgentCore
                // Note: We'll use direct HTTP calls since AWS SDK for browser may not have AgentCore client
                this.updateStatus('online', 'Connected to AgentCore');
                this.isConnected = true;
                
                console.log('✅ AWS SDK initialized successfully');
                
            } else {
                throw new Error('AWS SDK not loaded');
            }
        } catch (error) {
            console.error('AWS initialization failed:', error);
            this.updateStatus('error', 'Connection Error');
            this.isConnected = false;
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
            this.updateStatus('processing', 'Processing...');
            
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
            
            this.updateStatus('online', 'Connected to AgentCore');
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            
            // Show specific error message
            let errorMessage = 'I apologize, but I\'m having technical difficulties right now. ';
            
            if (error.message.includes('403') || error.message.includes('AccessDenied')) {
                errorMessage += 'There seems to be an authentication issue. ';
                this.updateStatus('error', 'Authentication Error');
            } else if (error.message.includes('404')) {
                errorMessage += 'The service endpoint could not be found. ';
                this.updateStatus('error', 'Service Not Found');
            } else if (error.message.includes('500')) {
                errorMessage += 'The service is temporarily unavailable. ';
                this.updateStatus('error', 'Service Error');
            } else {
                errorMessage += 'Please try again in a moment. ';
                this.updateStatus('error', 'Connection Error');
            }
            
            errorMessage += 'If you\'re in crisis, please contact emergency services or a crisis hotline immediately.';
            
            this.addMessage(errorMessage, 'agent');
            
            // Try to reconnect after a delay
            setTimeout(() => {
                this.initializeAWS();
            }, 5000);
        }
    }
    
    async storeInMemory(message, role) {
        try {
            console.log(`📝 Storing ${role} message in AgentCore Memory...`);
            
            // Prepare the payload in correct format
            const payload = [
                {
                    conversational: {
                        role: role,
                        content: {
                            text: message
                        }
                    }
                }
            ];
            
            const requestBody = {
                actorId: this.userId,
                sessionId: this.sessionId,
                eventTimestamp: Math.floor(Date.now() / 1000),
                payload: payload
            };
            
            // Use AWS SDK to make signed request
            const endpoint = `https://bedrock-agentcore.${this.config.region}.amazonaws.com/memories/${this.config.memoryId}/events`;
            
            const request = new AWS.HttpRequest(endpoint, this.config.region);
            request.method = 'POST';
            request.headers['Content-Type'] = 'application/json';
            request.body = JSON.stringify(requestBody);
            
            const signer = new AWS.Signers.V4(request, 'bedrock-agentcore');
            signer.addAuthorization(AWS.config.credentials, new Date());
            
            const response = await fetch(request.endpoint.href, {
                method: request.method,
                headers: request.headers,
                body: request.body
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log(`✅ Stored ${role} message successfully`);
                return true;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
        } catch (error) {
            console.warn('Memory storage failed:', error);
            return false;
        }
    }
    
    async getConversationContext() {
        try {
            console.log('📚 Retrieving conversation context...');
            
            // Use AWS SDK to make signed request
            const endpoint = `https://bedrock-agentcore.${this.config.region}.amazonaws.com/memories/${this.config.memoryId}/events?actorId=${this.userId}&sessionId=${this.sessionId}&maxResults=10`;
            
            const request = new AWS.HttpRequest(endpoint, this.config.region);
            request.method = 'GET';
            request.headers['Content-Type'] = 'application/json';
            
            const signer = new AWS.Signers.V4(request, 'bedrock-agentcore');
            signer.addAuthorization(AWS.config.credentials, new Date());
            
            const response = await fetch(request.endpoint.href, {
                method: request.method,
                headers: request.headers
            });
            
            if (response.ok) {
                const result = await response.json();
                const events = result.events || [];
                
                const context = [];
                for (const event of events) {
                    const payload = event.payload || [];
                    if (payload.length > 0 && payload[0].conversational) {
                        const conv = payload[0].conversational;
                        context.push({
                            message: conv.content.text,
                            role: conv.role,
                            timestamp: event.eventTimestamp
                        });
                    }
                }
                
                console.log(`📚 Retrieved ${context.length} context messages`);
                return context.slice(-6); // Last 6 messages
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
        } catch (error) {
            console.warn('Context retrieval failed:', error);
            return [];
        }
    }
    
    async callAgentCoreRuntime(message, context) {
        try {
            console.log('🤖 Calling AgentCore Runtime...');
            
            const requestBody = JSON.stringify({
                input: message,
                sessionId: this.sessionId,
                actorId: this.userId,
                context: context
            });
            
            // Use correct AgentCore Runtime API endpoint format
            const endpoint = `https://bedrock-agentcore.${this.config.region}.amazonaws.com/runtimes/${encodeURIComponent(this.config.runtimeArn)}/invocations`;
            
            const request = new AWS.HttpRequest(endpoint, this.config.region);
            request.method = 'POST';
            request.headers['Content-Type'] = 'application/json';
            request.headers['Accept'] = 'application/json';
            request.headers['X-Amzn-Bedrock-AgentCore-Runtime-Session-Id'] = this.sessionId;
            request.body = requestBody;
            
            const signer = new AWS.Signers.V4(request, 'bedrock-agentcore');
            signer.addAuthorization(AWS.config.credentials, new Date());
            
            const response = await fetch(request.endpoint.href, {
                method: request.method,
                headers: request.headers,
                body: request.body
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ AgentCore Runtime responded successfully');
                
                return {
                    response: result.response || result.output || 'I\'m here to support you.',
                    sessionId: this.sessionId,
                    status: 'success'
                };
            } else {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
        } catch (error) {
            console.error('AgentCore Runtime call failed:', error);
            throw error;
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
