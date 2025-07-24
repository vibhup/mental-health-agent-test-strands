// Login Page Authentication Handler with Debug Logging
class DebugLogger {
    constructor(pageType) {
        this.logContainer = document.getElementById('debugLog');
        this.isMinimized = false;
        this.logCount = 0;
        this.startTime = Date.now();
        this.pageType = pageType;
        
        this.log('INFO', `Debug system initialized for ${pageType}`);
        this.log('INFO', `Page: ${pageType}`);
        this.log('INFO', 'Flow Step: 2 - Authentication Page');
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
        if (this.logCount > 50) {
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

// Login Authentication with Debug Logging
class LoginAuth {
    constructor() {
        this.debug = new DebugLogger('Login Page');
        
        this.config = {
            region: 'us-east-1',
            userPoolId: 'us-east-1_IqzrBzc0g',
            clientId: '1l0v1imj8h6pg0i7villspuqr8',
            chatPortalUrl: 'chat.html'
        };
        
        this.userPool = null;
        this.isAuthenticating = false;
        
        this.debug.log('INFO', 'LoginAuth class initialized');
        this.debug.log('INFO', `User Pool ID: ${this.config.userPoolId}`);
        this.debug.log('INFO', `Client ID: ${this.config.clientId}`);
        
        this.initializeAuth();
    }
    
    async initializeAuth() {
        this.debug.log('INFO', 'Starting authentication initialization...');
        
        // Get DOM elements
        this.loginForm = document.getElementById('loginForm');
        this.loginButton = document.getElementById('loginButton');
        this.loginError = document.getElementById('loginError');
        this.loginStatus = document.getElementById('loginStatus');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        
        this.debug.log('INFO', 'DOM elements retrieved');
        
        // Set up event listeners
        this.setupEventListeners();
        this.debug.log('INFO', 'Event listeners registered');
        
        // Check if user is already authenticated
        this.debug.log('INFO', 'Checking for existing session...');
        await this.checkExistingSession();
        
        // Initialize Cognito
        this.debug.log('INFO', 'Initializing Cognito User Pool...');
        this.initializeCognito();
    }
    
    setupEventListeners() {
        if (this.loginForm) {
            this.loginForm.addEventListener('submit', (e) => {
                this.debug.log('INFO', 'Login form submitted');
                this.handleLogin(e);
            });
        }
        
        // Enter key handling
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isAuthenticating) {
                this.debug.log('INFO', 'Enter key pressed - triggering login');
                e.preventDefault();
                this.handleLogin(e);
            }
        });
        
        // Track input changes
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        
        if (usernameInput) {
            usernameInput.addEventListener('input', () => {
                this.debug.log('INFO', `Username field updated: ${usernameInput.value}`);
            });
        }
        
        if (passwordInput) {
            passwordInput.addEventListener('input', () => {
                this.debug.log('INFO', 'Password field updated (length: ' + passwordInput.value.length + ')');
            });
        }
    }
    
    async checkExistingSession() {
        try {
            // Check if there's a valid session in localStorage
            const existingToken = localStorage.getItem('mental_health_jwt_token');
            const tokenExpiry = localStorage.getItem('mental_health_token_expiry');
            const userEmail = localStorage.getItem('mental_health_user_email');
            
            this.debug.log('INFO', `Existing token found: ${!!existingToken}`);
            this.debug.log('INFO', `Token expiry found: ${!!tokenExpiry}`);
            this.debug.log('INFO', `User email found: ${!!userEmail}`);
            
            if (existingToken && tokenExpiry) {
                const expiryTime = new Date(tokenExpiry);
                const now = new Date();
                
                this.debug.log('INFO', `Token expires: ${expiryTime.toLocaleString()}`);
                this.debug.log('INFO', `Current time: ${now.toLocaleString()}`);
                
                if (expiryTime > now) {
                    this.debug.log('SUCCESS', 'Valid session found! Redirecting to chat portal...');
                    this.showStatus('Valid session found, redirecting to chat...', 'success');
                    
                    setTimeout(() => {
                        this.debug.log('INFO', 'Executing redirect to chat portal');
                        this.redirectToChatPortal();
                    }, 1500);
                    return;
                } else {
                    this.debug.log('WARN', 'Token expired, clearing session');
                    localStorage.removeItem('mental_health_jwt_token');
                    localStorage.removeItem('mental_health_token_expiry');
                    localStorage.removeItem('mental_health_user_email');
                }
            }
            
            this.debug.log('INFO', 'No valid existing session - user needs to login');
        } catch (error) {
            this.debug.log('ERROR', `Error checking existing session: ${error.message}`);
        }
    }
    
    initializeCognito() {
        try {
            // Check if AWS SDK is loaded
            if (typeof AWS === 'undefined') {
                throw new Error('AWS SDK not loaded');
            }
            this.debug.log('SUCCESS', 'AWS SDK loaded successfully');
            
            // Check if Cognito Identity SDK is loaded
            if (typeof AmazonCognitoIdentity === 'undefined') {
                throw new Error('Cognito Identity SDK not loaded');
            }
            this.debug.log('SUCCESS', 'Cognito Identity SDK loaded successfully');
            
            // Configure AWS region
            AWS.config.region = this.config.region;
            this.debug.log('INFO', `AWS region configured: ${this.config.region}`);
            
            // Initialize Cognito User Pool
            const poolData = {
                UserPoolId: this.config.userPoolId,
                ClientId: this.config.clientId
            };
            
            this.userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
            this.debug.log('SUCCESS', 'Cognito User Pool initialized successfully');
            this.debug.log('INFO', 'Login page ready for authentication');
            
        } catch (error) {
            this.debug.log('ERROR', `Cognito initialization failed: ${error.message}`);
            this.showError('Authentication system initialization failed. Please refresh the page.');
        }
    }
    
    async handleLogin(event) {
        event.preventDefault();
        
        if (this.isAuthenticating) {
            this.debug.log('WARN', 'Authentication already in progress, ignoring request');
            return;
        }
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        this.debug.log('INFO', `Login attempt for user: ${username}`);
        this.debug.log('INFO', `Password length: ${password.length}`);
        
        if (!username || !password) {
            this.debug.log('ERROR', 'Missing username or password');
            this.showError('Please enter both email and password');
            return;
        }
        
        if (!this.userPool) {
            this.debug.log('ERROR', 'Cognito User Pool not initialized');
            this.showError('Authentication system not ready. Please refresh the page.');
            return;
        }
        
        try {
            this.startAuthentication();
            this.debug.log('INFO', 'Starting Cognito authentication process...');
            
            const result = await this.authenticateUser(username, password);
            this.debug.log('SUCCESS', 'Cognito authentication successful!');
            
            // Store authentication data
            const jwtToken = result.getAccessToken().getJwtToken();
            const expiresIn = result.getAccessToken().getExpiration();
            
            this.debug.log('INFO', `JWT token received (length: ${jwtToken.length})`);
            this.debug.log('INFO', `Token expires at: ${new Date(expiresIn * 1000).toLocaleString()}`);
            
            // Store in localStorage for session persistence
            localStorage.setItem('mental_health_jwt_token', jwtToken);
            localStorage.setItem('mental_health_token_expiry', new Date(expiresIn * 1000).toISOString());
            localStorage.setItem('mental_health_user_email', username);
            
            this.debug.log('SUCCESS', 'Authentication data stored in localStorage');
            this.debug.log('INFO', 'Preparing redirect to chat portal...');
            
            this.showStatus('Authentication successful! Redirecting to chat portal...', 'success');
            
            // Redirect to chat portal after short delay
            setTimeout(() => {
                this.debug.log('INFO', 'Executing redirect to chat portal');
                this.redirectToChatPortal();
            }, 1500);
            
        } catch (error) {
            this.debug.log('ERROR', `Authentication failed: ${error.message}`);
            this.debug.log('ERROR', `Error code: ${error.code || 'Unknown'}`);
            this.handleAuthenticationError(error);
        } finally {
            this.stopAuthentication();
        }
    }
    
    async authenticateUser(username, password) {
        this.debug.log('INFO', 'Creating Cognito authentication request...');
        
        return new Promise((resolve, reject) => {
            const authenticationData = {
                Username: username,
                Password: password,
            };
            
            const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);
            this.debug.log('INFO', 'Authentication details created');
            
            const userData = {
                Username: username,
                Pool: this.userPool,
            };
            
            const cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
            this.debug.log('INFO', 'Cognito user object created');
            
            this.debug.log('INFO', 'Sending authentication request to Cognito...');
            
            cognitoUser.authenticateUser(authenticationDetails, {
                onSuccess: (result) => {
                    this.debug.log('SUCCESS', 'Cognito authentication callback: SUCCESS');
                    resolve(result);
                },
                onFailure: (err) => {
                    this.debug.log('ERROR', `Cognito authentication callback: FAILURE - ${err.message}`);
                    reject(err);
                },
                newPasswordRequired: (userAttributes, requiredAttributes) => {
                    this.debug.log('WARN', 'Cognito authentication callback: NEW PASSWORD REQUIRED');
                    reject(new Error('New password required. Please contact administrator.'));
                }
            });
        });
    }
    
    redirectToChatPortal() {
        this.debug.log('INFO', `Redirecting to: ${this.config.chatPortalUrl}`);
        window.location.href = this.config.chatPortalUrl;
    }
    
    startAuthentication() {
        this.debug.log('INFO', 'Starting authentication UI state...');
        this.isAuthenticating = true;
        
        if (this.loginButton) {
            this.loginButton.disabled = true;
            this.loginButton.innerHTML = '<span class="button-icon">⏳</span>Authenticating...';
        }
        
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'flex';
        }
        
        this.clearMessages();
        this.debug.log('INFO', 'Authentication UI state updated');
    }
    
    stopAuthentication() {
        this.debug.log('INFO', 'Stopping authentication UI state...');
        this.isAuthenticating = false;
        
        if (this.loginButton) {
            this.loginButton.disabled = false;
            this.loginButton.innerHTML = '<span class="button-icon">🔐</span>Login Securely';
        }
        
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
        
        this.debug.log('INFO', 'Authentication UI state reset');
    }
    
    handleAuthenticationError(error) {
        let errorMessage = 'Authentication failed. ';
        
        this.debug.log('INFO', 'Processing authentication error...');
        
        if (error.code === 'NotAuthorizedException') {
            errorMessage += 'Invalid email or password. Please check your credentials and try again.';
            this.debug.log('ERROR', 'Error type: Invalid credentials');
        } else if (error.code === 'UserNotFoundException') {
            errorMessage += 'User not found. Please check your email address.';
            this.debug.log('ERROR', 'Error type: User not found');
        } else if (error.code === 'UserNotConfirmedException') {
            errorMessage += 'User account not confirmed. Please contact administrator.';
            this.debug.log('ERROR', 'Error type: User not confirmed');
        } else if (error.code === 'TooManyRequestsException') {
            errorMessage += 'Too many login attempts. Please wait a moment and try again.';
            this.debug.log('ERROR', 'Error type: Rate limited');
        } else if (error.code === 'NetworkError') {
            errorMessage += 'Network error. Please check your internet connection.';
            this.debug.log('ERROR', 'Error type: Network error');
        } else {
            errorMessage += error.message || 'Please try again or contact support.';
            this.debug.log('ERROR', 'Error type: Unknown');
        }
        
        this.showError(errorMessage);
    }
    
    showError(message) {
        this.debug.log('INFO', `Showing error message: ${message}`);
        
        if (this.loginError) {
            this.loginError.textContent = message;
            this.loginError.style.display = 'block';
        }
        
        if (this.loginStatus) {
            this.loginStatus.style.display = 'none';
        }
    }
    
    showStatus(message, type = 'info') {
        this.debug.log('INFO', `Showing status message (${type}): ${message}`);
        
        if (this.loginStatus) {
            this.loginStatus.textContent = message;
            this.loginStatus.style.display = 'block';
            
            // Update styling based on type
            if (type === 'success') {
                this.loginStatus.style.background = '#f0fdf4';
                this.loginStatus.style.color = '#166534';
                this.loginStatus.style.borderLeftColor = '#22c55e';
            } else {
                this.loginStatus.style.background = '#f0f9ff';
                this.loginStatus.style.color = '#0369a1';
                this.loginStatus.style.borderLeftColor = '#0ea5e9';
            }
        }
        
        if (this.loginError) {
            this.loginError.style.display = 'none';
        }
    }
    
    clearMessages() {
        this.debug.log('INFO', 'Clearing all messages');
        
        if (this.loginError) {
            this.loginError.style.display = 'none';
        }
        
        if (this.loginStatus) {
            this.loginStatus.style.display = 'none';
        }
    }
}

// Initialize login authentication when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Mental Health Login Page with Debug...');
    window.loginAuth = new LoginAuth();
});

// Debug helpers
window.clearSession = function() {
    localStorage.removeItem('mental_health_jwt_token');
    localStorage.removeItem('mental_health_token_expiry');
    localStorage.removeItem('mental_health_user_email');
    console.log('✅ Session cleared');
    if (window.loginAuth && window.loginAuth.debug) {
        window.loginAuth.debug.log('INFO', 'Session manually cleared via debug command');
    }
    location.reload();
};

// Track page events
window.addEventListener('load', () => {
    if (window.loginAuth && window.loginAuth.debug) {
        window.loginAuth.debug.log('INFO', 'Page fully loaded');
    }
});

window.addEventListener('beforeunload', () => {
    if (window.loginAuth && window.loginAuth.debug) {
        window.loginAuth.debug.log('INFO', 'Page unloading');
    }
});

console.log('🔐 Login Page with Debug Loaded');
console.log('Demo Credentials: testuser@example.com / MentalHealth123!');
console.log('Debug: Use window.clearSession() to clear stored session');
