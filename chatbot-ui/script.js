// Mental Health Chatbot JavaScript
class MentalHealthChatbot {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.isConnected = false;
        this.messageHistory = [];
        this.apiEndpoint = 'https://49rwj9ccpd.execute-api.us-east-1.amazonaws.com/prod/chat';
        
        // DOM elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.crisisModal = document.getElementById('crisisModal');
        this.closeModal = document.getElementById('closeModal');
        
        this.initializeEventListeners();
        this.checkConnection();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
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
    
    async checkConnection() {
        try {
            // Test connection to API Gateway
            const response = await fetch(this.apiEndpoint, {
                method: 'OPTIONS',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                this.updateStatus('online', 'Connected');
            } else {
                this.updateStatus('error', 'Connection Error');
            }
        } catch (error) {
            this.updateStatus('error', 'Connection Error');
            console.error('Connection check failed:', error);
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
            // Send to API Gateway -> Lambda -> AgentCore
            const response = await this.callAgentCore(message);
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
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
    
    async callAgentCore(message) {
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    input: message,
                    sessionId: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Check if there's an error in the response
            if (data.error) {
                throw new Error(data.message || data.error);
            }
            
            return data;
            
        } catch (error) {
            console.error('API call failed:', error);
            
            // Return fallback response
            return {
                response: "I'm here to listen and support you. While I'm having technical difficulties right now, please know that your feelings are valid and help is available. If you're in crisis, please contact a mental health professional or crisis hotline immediately.",
                sessionId: this.sessionId,
                status: 'error'
            };
        }
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
        
        // Store in history
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

// Initialize chatbot when page loads
document.addEventListener('DOMContentLoaded', () => {
    new MentalHealthChatbot();
});

// Service Worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
