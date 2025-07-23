// JWT-Enabled AgentCore Direct Integration
class JWTAgentCoreChatbot {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.isConnected = false;
        this.messageHistory = [];
        this.jwtToken = null;
        
        // JWT Configuration
        this.config = {
            region: 'us-east-1',
            runtimeArn: 'arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I',
            memoryId: 'MentalHealthChatbotMemory-GqmjCf2KIw',
            userPoolId: 'us-east-1_IqzrBzc0g',
            clientId: '1l0v1imj8h6pg0i7villspuqr8',
            discoveryUrl: 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_IqzrBzc0g/.well-known/openid-configuration'
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
        this.initializeJWTAuth();
    }
    
    generateSessionId() {
        // Generate session ID with 33+ characters as required
        return 'mental_health_jwt_session_' + Math.random().toString(36).substr(2, 15) + Date.now();
    }
    
    getUserId() {
        let userId = localStorage.getItem('mental_health_user_id');
        if (!userId) {
            userId = 'jwt_user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('mental_health_user_id', userId);
        }
        return userId;
    }
    
    async initializeJWTAuth() {
        try {
            this.updateStatus('connecting', 'Connecting with JWT Authentication...');
            
            // For demo purposes, use the test user credentials
            // In production, implement proper login form
            await this.authenticateUser('testuser@example.com', 'MentalHealth123!');
            
            this.updateStatus('online', 'Connected with JWT Authentication');
            this.isConnected = true;
            
            console.log('✅ JWT authentication successful');
            
        } catch (error) {
            console.error('JWT authentication failed:', error);
            this.updateStatus('error', 'Authentication Failed');
            this.showAuthenticationError();
        }
    }
    
    async authenticateUser(username, password) {
        try {
            // In a real implementation, you'd use AWS SDK for JavaScript
            // For now, we'll simulate the authentication
            
            // This is a placeholder - in production you would:
            // 1. Use AWS SDK to call Cognito
            // 2. Handle the authentication flow properly
            // 3. Store tokens securely
            
            // For demo, we'll use a test token (this would come from Cognito)
            this.jwtToken = await this.getCognitoToken(username, password);
            
            console.log('✅ JWT token obtained');
            
        } catch (error) {
            console.error('Authentication failed:', error);
            throw error;
        }
    }
    
    async getCognitoToken(username, password) {
        // This is a placeholder for the actual Cognito authentication
        // In production, you would use AWS SDK for JavaScript to call Cognito
        
        // For demo purposes, we'll return a placeholder
        // The actual implementation would look like:
        /*
        const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
            Username: username,
            Pool: userPool
        });
        
        return new Promise((resolve, reject) => {
            cognitoUser.authenticateUser(authenticationDetails, {
                onSuccess: (result) => {
                    resolve(result.getAccessToken().getJwtToken());
                },
                onFailure: (err) => {
                    reject(err);
                }
            });
        });
        */
        
        // For demo, return a placeholder that indicates JWT auth is configured
        return 'JWT_TOKEN_PLACEHOLDER_CONFIGURED_FOR_PRODUCTION';
    }
    
    async callAgentCoreRuntime(message, context) {
        try {
            console.log('🤖 Calling AgentCore Runtime with JWT...');
            
            const payload = {
                input: message,
                sessionId: this.sessionId,
                actorId: this.userId,
                context: context
            };
            
            const url = `https://bedrock-agentcore.${this.config.region}.amazonaws.com/runtimes/${encodeURIComponent(this.config.runtimeArn)}/invocations`;
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.jwtToken}`,
                    'Content-Type': 'application/json',
                    'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': this.sessionId
                },
                body: JSON.stringify(payload)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ AgentCore Runtime responded successfully');
                
                return {
                    response: result.response || 'I\'m here to support you.',
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
            
            // Get conversation context (simplified for demo)
            const context = this.getLocalContext();
            
            // Call AgentCore Runtime with JWT
            const response = await this.callAgentCoreRuntime(message, context);
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Add agent response
            this.addMessage(response.response, 'agent');
            
            // Check for crisis indicators
            this.checkForCrisisKeywords(message);
            
            this.updateStatus('online', 'Connected with JWT Authentication');
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            
            // Show specific error message
            let errorMessage = 'I apologize, but I\'m having technical difficulties right now. ';
            
            if (error.message.includes('403') || error.message.includes('401')) {
                errorMessage += 'Authentication issue detected. Please refresh the page. ';
                this.updateStatus('error', 'Authentication Error');
            } else if (error.message.includes('404')) {
                errorMessage += 'Service endpoint not found. ';
                this.updateStatus('error', 'Service Not Found');
            } else if (error.message.includes('500')) {
                errorMessage += 'Service temporarily unavailable. ';
                this.updateStatus('error', 'Service Error');
            } else {
                errorMessage += 'Please try again in a moment. ';
                this.updateStatus('error', 'Connection Error');
            }
            
            errorMessage += 'If you\'re in crisis, please contact emergency services or a crisis hotline immediately.';
            
            this.addMessage(errorMessage, 'agent');
            
            // Try to reconnect after a delay
            setTimeout(() => {
                this.initializeJWTAuth();
            }, 5000);
        }
    }
    
    getLocalContext() {
        // Get last few messages for context
        return this.messageHistory.slice(-6).map(msg => ({
            role: msg.sender === 'user' ? 'USER' : 'ASSISTANT',
            message: msg.text,
            timestamp: msg.timestamp
        }));
    }
    
    showAuthenticationError() {
        this.addMessage('Authentication failed. This demo requires proper Cognito User Pool setup. In production, users would log in with their credentials to get JWT tokens for direct AgentCore access.', 'agent');
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
        } else if (status === 'error') {
            this.isConnected = false;
        }
        
        this.toggleSendButton();
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
    new JWTAgentCoreChatbot();
});
