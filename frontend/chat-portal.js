// Chat Portal with Authentication Check and Debug Logging
class DebugLogger {
    constructor(pageType) {
        this.logContainer = document.getElementById('debugLog');
        this.isMinimized = false;
        this.logCount = 0;
        this.startTime = Date.now();
        this.pageType = pageType;
        
        this.log('INFO', `Debug system initialized for ${pageType}`);
        this.log('INFO', `Page: ${pageType}`);
        this.log('INFO', 'Flow Step: 3 - Chat Portal');
    }
    
    log(level, message) {
        const timestamp = new Date().toLocaleTimeString();
        const elapsed = ((Date.now() - this.startTime) / 1000).toFixed(1);
        
        const logEntry = document.createElement('div');
        logEntry.className = `debug-log debug-level-${level.toLowerCase()}`;
        logEntry.innerHTML = `
            <span class="debug-timestamp">[${timestamp}] [+${elapsed}s]</span>
            <strong>[${level}]</strong> ${message}
        `;
        
        this.logContainer.appendChild(logEntry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
        
        // Also log to console
        console.log(`[DEBUG] [${level}] ${message}`);
        
        this.logCount++;
        if (this.logCount > 100) {
            // Remove old entries to prevent memory issues
            const firstChild = this.logContainer.firstChild;
            if (firstChild) {
                this.logContainer.removeChild(firstChild);
            }
        }
    }
}

// Debug window toggle
function toggleDebug() {
    const content = document.getElementById('debugContent');
    const button = document.querySelector('.debug-toggle');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        button.textContent = 'Minimize';
    } else {
        content.style.display = 'none';
        button.textContent = 'Expand';
    }
}

// Chat Portal with Debug Logging
class ChatPortal {
    constructor() {
        this.debug = new DebugLogger('Chat Portal');
        
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.isConnected = false;
        this.isAuthenticated = false;
        this.messageHistory = [];
        this.jwtToken = null;
        this.userEmail = null;
        
        this.debug.log('INFO', `Session ID generated: ${this.sessionId}`);
        this.debug.log('INFO', `User ID: ${this.userId}`);
        
        // Configuration
        this.config = {
            region: 'us-east-1',
            runtimeArn: 'arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I',
            memoryId: 'MentalHealthChatbotMemory-GqmjCf2KIw',
            userPoolId: 'us-east-1_IqzrBzc0g',
            clientId: '1l0v1imj8h6pg0i7villspuqr8',
            agentCoreEndpoint: 'https://bedrock-agentcore.us-east-1.amazonaws.com',
            loginPageUrl: 'login.html'
        };
        
        this.debug.log('INFO', 'Configuration loaded:');
        this.debug.log('INFO', `  Runtime ARN: ${this.config.runtimeArn.split('/').pop()}`);
        this.debug.log('INFO', `  Memory ID: ${this.config.memoryId}`);
        this.debug.log('INFO', `  AgentCore Endpoint: ${this.config.agentCoreEndpoint}`);
        
        // Crisis detection keywords
        this.crisisKeywords = [
            'suicide', 'kill myself', 'end it all', 'want to die', 'better off dead',
            'hurt myself', 'self harm', 'cut myself', 'overdose', 'jump off',
            'no point living', 'life is meaningless', 'give up', 'end my life'
        ];
        
        this.debug.log('INFO', `Crisis keywords loaded: ${this.crisisKeywords.length} keywords`);
        
        // Initialize the chat portal
        this.initializeChatPortal();
    }
    
    generateSessionId() {
        const sessionId = 'mental_health_chat_session_' + Math.random().toString(36).substr(2, 15) + Date.now();
        return sessionId;
    }
    
    getUserId() {
        let userId = localStorage.getItem('mental_health_user_id');
        if (!userId) {
            userId = 'chat_user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('mental_health_user_id', userId);
        }
        return userId;
    }
    
    async initializeChatPortal() {
        this.debug.log('INFO', 'Initializing Chat Portal...');
        
        // Get DOM elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.crisisModal = document.getElementById('crisisModal');
        this.closeModal = document.getElementById('closeModal');
        this.authRequiredModal = document.getElementById('authRequiredModal');
        this.logoutButton = document.getElementById('logoutButton');
        this.userEmailElement = document.getElementById('userEmail');
        
        this.debug.log('INFO', 'DOM elements retrieved');
        
        // Set up event listeners
        this.initializeEventListeners();
        this.debug.log('INFO', 'Event listeners registered');
        
        // Check authentication first
        this.debug.log('INFO', 'Starting authentication check...');
        const isAuthenticated = await this.checkAuthentication();
        
        if (!isAuthenticated) {
            this.debug.log('ERROR', 'Authentication failed - redirecting to login');
            this.redirectToLogin();
            return;
        }
        
        this.debug.log('SUCCESS', 'Authentication successful - initializing chat');
        // Initialize chat functionality
        this.initializeChat();
    }
    
    async checkAuthentication() {
        try {
            this.debug.log('INFO', 'Checking stored authentication data...');
            this.updateStatus('connecting', 'Checking authentication...');
            
            // Get stored authentication data
            const jwtToken = localStorage.getItem('mental_health_jwt_token');
            const tokenExpiry = localStorage.getItem('mental_health_token_expiry');
            const userEmail = localStorage.getItem('mental_health_user_email');
            
            this.debug.log('INFO', `JWT token found: ${!!jwtToken}`);
            this.debug.log('INFO', `Token expiry found: ${!!tokenExpiry}`);
            this.debug.log('INFO', `User email found: ${!!userEmail}`);
            
            if (!jwtToken || !tokenExpiry || !userEmail) {
                this.debug.log('ERROR', 'Missing authentication data');
                return false;
            }
            
            // Check if token is expired
            const expiryTime = new Date(tokenExpiry);
            const now = new Date();
            
            this.debug.log('INFO', `Token expires: ${expiryTime.toLocaleString()}`);
            this.debug.log('INFO', `Current time: ${now.toLocaleString()}`);
            
            if (expiryTime <= now) {
                this.debug.log('ERROR', 'JWT token expired');
                this.clearAuthenticationData();
                return false;
            }
            
            // Validate token format
            const tokenParts = jwtToken.split('.');
            if (tokenParts.length !== 3) {
                this.debug.log('ERROR', `Invalid JWT token format (${tokenParts.length} parts)`);
                this.clearAuthenticationData();
                return false;
            }
            
            this.debug.log('SUCCESS', 'JWT token format valid (3 parts)');
            
            // Store authentication data
            this.jwtToken = jwtToken;
            this.userEmail = userEmail;
            this.isAuthenticated = true;
            
            // Update UI with user info
            if (this.userEmailElement) {
                this.userEmailElement.textContent = userEmail;
                this.debug.log('INFO', `User email displayed: ${userEmail}`);
            }
            
            this.debug.log('SUCCESS', 'Authentication validation complete');
            return true;
            
        } catch (error) {
            this.debug.log('ERROR', `Authentication check failed: ${error.message}`);
            return false;
        }
    }
    
    initializeChat() {
        this.debug.log('INFO', 'Initializing chat functionality...');
        
        this.updateStatus('online', 'Connected - Ready to Chat');
        this.isConnected = true;
        
        // Enable chat input
        if (this.messageInput) {
            this.messageInput.disabled = false;
            this.messageInput.placeholder = 'Type your message here...';
            this.debug.log('INFO', 'Message input enabled');
        }
        
        this.toggleSendButton();
        
        // Show welcome message
        this.showWelcomeMessage();
        this.debug.log('SUCCESS', 'Chat initialization complete');
    }
    
    showWelcomeMessage() {
        const welcomeMessage = `Hello! I'm your mental health support agent powered by AWS AgentCore and Claude Sonnet 4. I'm here to listen and provide support. How are you feeling today?`;
        this.addMessage(welcomeMessage, 'agent');
        this.debug.log('INFO', 'Welcome message displayed');
    }
    
    initializeEventListeners() {
        // Send button click
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => {
                this.debug.log('INFO', 'Send button clicked');
                this.sendMessage();
            });
        }
        
        // Enter key press
        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    this.debug.log('INFO', 'Enter key pressed - sending message');
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            this.messageInput.addEventListener('input', () => this.toggleSendButton());
        }
        
        // Crisis modal close
        if (this.closeModal) {
            this.closeModal.addEventListener('click', () => {
                this.debug.log('INFO', 'Crisis modal closed');
                this.closeCrisisModal();
            });
        }
        
        // Logout button
        if (this.logoutButton) {
            this.logoutButton.addEventListener('click', () => {
                this.debug.log('INFO', 'Logout button clicked');
                this.handleLogout();
            });
        }
        
        // Click outside modal to close crisis modal
        window.addEventListener('click', (e) => {
            if (e.target === this.crisisModal) {
                this.debug.log('INFO', 'Crisis modal closed (clicked outside)');
                this.closeCrisisModal();
            }
        });
        
        // Track page visibility
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.debug.log('INFO', 'Page hidden (user switched tabs)');
            } else {
                this.debug.log('INFO', 'Page visible (user returned)');
            }
        });
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        this.debug.log('INFO', `Attempting to send message: "${message}"`);
        this.debug.log('INFO', `Connected: ${this.isConnected}, Authenticated: ${this.isAuthenticated}`);
        
        if (!message || !this.isConnected || !this.isAuthenticated) {
            this.debug.log('WARN', 'Message send blocked - missing requirements');
            return;
        }
        
        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.toggleSendButton();
        
        this.debug.log('INFO', 'User message added to chat');
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            this.updateStatus('processing', 'Processing...');
            this.debug.log('INFO', 'Starting message processing...');
            
            // Check for crisis keywords first
            this.checkForCrisisKeywords(message);
            
            // Get conversation context
            const context = this.getLocalContext();
            this.debug.log('INFO', `Context prepared: ${context.length} previous messages`);
            
            // Call AgentCore Runtime with JWT
            this.debug.log('INFO', 'Calling AgentCore Runtime...');
            const response = await this.callAgentCoreRuntime(message, context);
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Add agent response to chat
            this.addMessage(response.response, 'agent');
            this.debug.log('SUCCESS', 'Agent response received and displayed');
            
            this.updateStatus('online', 'Connected - Ready to Chat');
            
        } catch (error) {
            this.debug.log('ERROR', `Message processing failed: ${error.message}`);
            this.hideTypingIndicator();
            
            // Handle authentication errors
            if (error.message.includes('403') || error.message.includes('401')) {
                this.debug.log('ERROR', 'Authentication error detected');
                this.handleAuthenticationError();
                return;
            }
            
            // Show generic error message
            let errorMessage = 'I apologize, but I\\'m having technical difficulties right now. ';
            errorMessage += 'Please try again in a moment. ';
            errorMessage += 'If you\\'re in crisis, please contact emergency services or a crisis hotline immediately.';
            
            this.addMessage(errorMessage, 'agent');
            this.updateStatus('error', 'Connection Error - Please try again');
            this.debug.log('ERROR', 'Error message displayed to user');
        }
    }
    
    async callAgentCoreRuntime(message, context) {
        if (!this.jwtToken) {
            throw new Error('No JWT token available');
        }
        
        const payload = {
            input: message,
            sessionId: this.sessionId,
            actorId: this.userId,
            context: context
        };
        
        const url = `${this.config.agentCoreEndpoint}/runtimes/${encodeURIComponent(this.config.runtimeArn)}/invocations`;
        
        this.debug.log('INFO', `AgentCore URL: ${url}`);
        this.debug.log('INFO', `Payload size: ${JSON.stringify(payload).length} bytes`);
        this.debug.log('INFO', `JWT token length: ${this.jwtToken.length}`);
        
        const startTime = Date.now();
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.jwtToken}`,
                'Content-Type': 'application/json',
                'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': this.sessionId
            },
            body: JSON.stringify(payload)
        });
        
        const responseTime = Date.now() - startTime;
        this.debug.log('INFO', `AgentCore response time: ${responseTime}ms`);
        this.debug.log('INFO', `Response status: ${response.status}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            this.debug.log('ERROR', `AgentCore error: ${response.status} - ${errorText}`);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const result = await response.json();
        this.debug.log('SUCCESS', `AgentCore response received (${JSON.stringify(result).length} bytes)`);
        
        return result;
    }
    
    getLocalContext() {
        const context = this.messageHistory.slice(-6).map(msg => ({
            role: msg.sender === 'user' ? 'USER' : 'ASSISTANT',
            message: msg.text,
            timestamp: msg.timestamp
        }));
        
        this.debug.log('INFO', `Context generated: ${context.length} messages`);
        return context;
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        bubbleDiv.textContent = text;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.appendChild(bubbleDiv);
        messageDiv.appendChild(timeDiv);
        
        if (this.chatMessages) {
            this.chatMessages.appendChild(messageDiv);
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
        
        // Store in message history
        this.messageHistory.push({
            text: text,
            sender: sender,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 20 messages in memory
        if (this.messageHistory.length > 20) {
            this.messageHistory = this.messageHistory.slice(-20);
            this.debug.log('INFO', 'Message history trimmed to 20 messages');
        }
        
        this.debug.log('INFO', `Message added (${sender}): ${text.length} characters`);
    }
    
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message agent-message typing-message';
        typingDiv.id = 'typingIndicator';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble typing-indicator';
        bubbleDiv.innerHTML = '<span></span><span></span><span></span>';
        
        typingDiv.appendChild(bubbleDiv);
        
        if (this.chatMessages) {
            this.chatMessages.appendChild(typingDiv);
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
        
        this.debug.log('INFO', 'Typing indicator shown');
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
            this.debug.log('INFO', 'Typing indicator removed');
        }
    }
    
    checkForCrisisKeywords(message) {
        const lowerMessage = message.toLowerCase();
        const foundKeywords = this.crisisKeywords.filter(keyword => 
            lowerMessage.includes(keyword.toLowerCase())
        );
        
        this.debug.log('INFO', `Crisis check: ${foundKeywords.length} keywords found`);
        
        if (foundKeywords.length > 0) {
            this.debug.log('WARN', `Crisis keywords detected: ${foundKeywords.join(', ')}`);
            this.showCrisisModal();
        }
    }
    
    showCrisisModal() {
        if (this.crisisModal) {
            this.crisisModal.style.display = 'flex';
            this.debug.log('WARN', 'Crisis modal displayed');
        }
    }
    
    closeCrisisModal() {
        if (this.crisisModal) {
            this.crisisModal.style.display = 'none';
        }
    }
    
    handleAuthenticationError() {
        this.debug.log('ERROR', 'Handling authentication error...');
        this.clearAuthenticationData();
        this.showAuthRequiredModal();
    }
    
    showAuthRequiredModal() {
        if (this.authRequiredModal) {
            this.authRequiredModal.style.display = 'flex';
            this.debug.log('ERROR', 'Authentication required modal displayed');
        }
    }
    
    handleLogout() {
        this.debug.log('INFO', 'Processing logout request...');
        this.clearAuthenticationData();
        this.debug.log('INFO', 'Authentication data cleared');
        this.redirectToLogin();
    }
    
    clearAuthenticationData() {
        localStorage.removeItem('mental_health_jwt_token');
        localStorage.removeItem('mental_health_token_expiry');
        localStorage.removeItem('mental_health_user_email');
        
        this.jwtToken = null;
        this.userEmail = null;
        this.isAuthenticated = false;
        this.isConnected = false;
        
        this.debug.log('INFO', 'All authentication data cleared');
    }
    
    redirectToLogin() {
        this.debug.log('INFO', `Redirecting to login page: ${this.config.loginPageUrl}`);
        window.location.href = this.config.loginPageUrl;
    }
    
    toggleSendButton() {
        const hasText = this.messageInput && this.messageInput.value.trim().length > 0;
        if (this.sendButton) {
            this.sendButton.disabled = !hasText || !this.isConnected || !this.isAuthenticated;
        }
    }
    
    updateStatus(status, text) {
        if (this.statusDot) {
            this.statusDot.className = `status-dot ${status}`;
        }
        if (this.statusText) {
            this.statusText.textContent = text;
        }
        
        if (status === 'online') {
            this.isConnected = true;
        } else if (status === 'error') {
            this.isConnected = false;
        }
        
        this.toggleSendButton();
        this.debug.log('INFO', `Status updated: ${status} - ${text}`);
    }
}

// Initialize the chat portal when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Mental Health Chat Portal with Debug...');
    window.chatPortal = new ChatPortal();
});

// Debug helpers
window.clearSession = function() {
    localStorage.removeItem('mental_health_jwt_token');
    localStorage.removeItem('mental_health_token_expiry');
    localStorage.removeItem('mental_health_user_email');
    console.log('✅ Session cleared');
    if (window.chatPortal && window.chatPortal.debug) {
        window.chatPortal.debug.log('INFO', 'Session manually cleared via debug command');
    }
    location.reload();
};

window.testCrisis = function() {
    if (window.chatPortal) {
        window.chatPortal.debug.log('INFO', 'Testing crisis detection manually');
        window.chatPortal.checkForCrisisKeywords('I want to hurt myself');
    }
};

// Track page events
window.addEventListener('load', () => {
    if (window.chatPortal && window.chatPortal.debug) {
        window.chatPortal.debug.log('INFO', 'Page fully loaded');
    }
});

window.addEventListener('beforeunload', () => {
    if (window.chatPortal && window.chatPortal.debug) {
        window.chatPortal.debug.log('INFO', 'Page unloading');
    }
});

console.log('💬 Chat Portal with Debug Loaded');
console.log('Debug: Use window.clearSession() to clear stored session');
console.log('Debug: Use window.testCrisis() to test crisis detection');
