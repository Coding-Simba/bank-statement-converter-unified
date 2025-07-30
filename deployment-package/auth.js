// Authentication module for Bank Statement Converter

// Use dynamic API configuration
const getApiBase = () => {
    if (window.API_CONFIG) {
        return window.API_CONFIG.getBaseUrl();
    }
    // Fallback to dynamic detection
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5000';
    }
    return `${window.location.protocol}//${window.location.hostname}`;
};

const AUTH_API_BASE = getApiBase() + '/api/auth';
const API_BASE = getApiBase() + '/api';

// Token management
const TokenManager = {
    getAccessToken() {
        return localStorage.getItem('access_token');
    },
    
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },
    
    setTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    },
    
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
    },
    
    isAuthenticated() {
        return !!this.getAccessToken();
    }
};

// User management
const UserManager = {
    setUser(userData) {
        localStorage.setItem('user_data', JSON.stringify(userData));
    },
    
    getUser() {
        const userData = localStorage.getItem('user_data');
        return userData ? JSON.parse(userData) : null;
    },
    
    clearUser() {
        localStorage.removeItem('user_data');
    }
};

// Authentication API calls
const AuthAPI = {
    async register(userData) {
        try {
            console.log('Registering user:', userData);
            console.log('API URL:', `${AUTH_API_BASE}/register`);
            
            const response = await fetch(`${AUTH_API_BASE}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData),
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }
            
            const data = await response.json();
            TokenManager.setTokens(data.access_token, data.refresh_token);
            UserManager.setUser(data.user);
            return data;
        } catch (error) {
            console.error('Registration error:', error);
            if (error.message === 'Failed to fetch') {
                throw new Error('Failed to connect to server. Please ensure the backend is running on port 5000.');
            }
            throw error;
        }
    },
    
    async login(email, password) {
        try {
            const response = await fetch(`${AUTH_API_BASE}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }
            
            const data = await response.json();
            TokenManager.setTokens(data.access_token, data.refresh_token);
            UserManager.setUser(data.user);
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },
    
    async logout() {
        try {
            await fetch(`${AUTH_API_BASE}/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${TokenManager.getAccessToken()}`,
                },
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            TokenManager.clearTokens();
            UserManager.clearUser();
            window.location.href = '/';
        }
    },
    
    async refreshToken() {
        try {
            const refreshToken = TokenManager.getRefreshToken();
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }
            
            const response = await fetch(`${AUTH_API_BASE}/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });
            
            if (!response.ok) {
                throw new Error('Token refresh failed');
            }
            
            const data = await response.json();
            TokenManager.setTokens(data.access_token, TokenManager.getRefreshToken());
            return data.access_token;
        } catch (error) {
            console.error('Token refresh error:', error);
            TokenManager.clearTokens();
            UserManager.clearUser();
            throw error;
        }
    },
    
    async getProfile() {
        try {
            const response = await fetch(`${AUTH_API_BASE}/profile`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${TokenManager.getAccessToken()}`,
                },
            });
            
            if (!response.ok) {
                throw new Error('Failed to get profile');
            }
            
            const data = await response.json();
            UserManager.setUser(data);
            return data;
        } catch (error) {
            console.error('Get profile error:', error);
            throw error;
        }
    }
};

// Statement API calls with authentication
const StatementAPI = {
    async checkLimit() {
        try {
            const headers = {};
            if (TokenManager.isAuthenticated()) {
                headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
            }
            
            const response = await fetch(`${API_BASE}/check-limit`, {
                method: 'GET',
                headers,
                credentials: 'include', // For session cookies
            });
            
            if (!response.ok) {
                throw new Error('Failed to check limit');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Check limit error:', error);
            throw error;
        }
    },
    
    async convertStatement(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const headers = {};
            if (TokenManager.isAuthenticated()) {
                headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
            }
            
            const response = await fetch(`${API_BASE}/convert`, {
                method: 'POST',
                headers,
                body: formData,
                credentials: 'include',
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Conversion failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Convert statement error:', error);
            throw error;
        }
    },
    
    async getUserStatements() {
        try {
            const response = await fetch(`${API_BASE}/user/statements`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${TokenManager.getAccessToken()}`,
                },
            });
            
            if (!response.ok) {
                throw new Error('Failed to get statements');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Get statements error:', error);
            throw error;
        }
    },
    
    async downloadStatement(statementId) {
        try {
            const headers = {};
            if (TokenManager.isAuthenticated()) {
                headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
            }
            
            const response = await fetch(`${API_BASE}/statement/${statementId}/download`, {
                method: 'GET',
                headers,
                credentials: 'include',
            });
            
            if (!response.ok) {
                throw new Error('Failed to download statement');
            }
            
            // Get filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            const filenameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/);
            const filename = filenameMatch ? filenameMatch[1] : 'converted_statement.csv';
            
            // Download file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            return true;
        } catch (error) {
            console.error('Download statement error:', error);
            throw error;
        }
    }
};

// Feedback API
const FeedbackAPI = {
    async submitFeedback(statementId, rating, comment) {
        try {
            const headers = {
                'Content-Type': 'application/json',
            };
            
            if (TokenManager.isAuthenticated()) {
                headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
            }
            
            const response = await fetch(`${API_BASE}/feedback`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    statement_id: statementId,
                    rating,
                    comment,
                }),
                credentials: 'include',
            });
            
            if (!response.ok) {
                throw new Error('Failed to submit feedback');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Submit feedback error:', error);
            throw error;
        }
    }
};

// Axios-like interceptor for automatic token refresh
const setupAuthInterceptor = () => {
    const originalFetch = window.fetch;
    
    window.fetch = async function(...args) {
        let response = await originalFetch(...args);
        
        // If unauthorized and we have a refresh token, try to refresh
        if (response.status === 401 && TokenManager.getRefreshToken()) {
            try {
                await AuthAPI.refreshToken();
                
                // Retry the original request with new token
                if (args[1] && args[1].headers && args[1].headers['Authorization']) {
                    args[1].headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
                }
                
                response = await originalFetch(...args);
            } catch (error) {
                // Refresh failed, redirect to login
                window.location.href = '/login';
            }
        }
        
        return response;
    };
};

// Initialize auth interceptor
setupAuthInterceptor();

// OAuth Authentication
const OAuthAPI = {
    async loginWithGoogle() {
        try {
            // Redirect to Google OAuth endpoint
            window.location.href = `${AUTH_API_BASE}/oauth/google`;
        } catch (error) {
            console.error('Google login error:', error);
            throw error;
        }
    },
    
    async loginWithMicrosoft() {
        try {
            // Redirect to Microsoft OAuth endpoint
            window.location.href = `${AUTH_API_BASE}/oauth/microsoft`;
        } catch (error) {
            console.error('Microsoft login error:', error);
            throw error;
        }
    },
    
    async handleOAuthCallback() {
        // Check if we're on the OAuth callback page
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');
        
        if (error) {
            console.error('OAuth error:', error);
            window.location.href = '/login?error=oauth_failed';
            return;
        }
        
        if (code && state) {
            try {
                // The backend will handle the callback and redirect
                // This is just for client-side error handling
                const provider = window.location.pathname.includes('google') ? 'google' : 'microsoft';
                console.log(`Processing ${provider} OAuth callback...`);
            } catch (error) {
                console.error('OAuth callback error:', error);
                window.location.href = '/login?error=oauth_failed';
            }
        }
    }
};

// Signup/Login Form Handlers
const AuthForms = {
    async handleSignup(formData) {
        try {
            const userData = {
                email: formData.get('email'),
                password: formData.get('password'),
                full_name: formData.get('fullName'),
                company_name: formData.get('company') || '',
                account_type: 'free'
            };
            
            console.log('Form data collected:', userData);
            
            const result = await AuthAPI.register(userData);
            
            // Show success message and redirect
            const submitBtn = document.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.textContent = 'Success! Redirecting...';
            }
            
            // Redirect to dashboard or homepage on success
            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 1000);
            
            return result;
        } catch (error) {
            console.error('Signup error:', error);
            throw error;
        }
    },
    
    async handleLogin(formData) {
        try {
            const email = formData.get('email');
            const password = formData.get('password');
            
            const result = await AuthAPI.login(email, password);
            
            // Redirect to dashboard on success
            const redirect = new URLSearchParams(window.location.search).get('redirect') || '/dashboard.html';
            window.location.href = redirect;
            
            return result;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },
    
    setupSignupForm() {
        const form = document.getElementById('signupForm');
        if (!form) return;
        
        // OAuth buttons
        const googleBtn = form.querySelector('.google-btn, [data-provider="google"]');
        const microsoftBtn = form.querySelector('.microsoft-btn, [data-provider="microsoft"]');
        
        if (googleBtn) {
            googleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                OAuthAPI.loginWithGoogle();
            });
        }
        
        if (microsoftBtn) {
            microsoftBtn.addEventListener('click', (e) => {
                e.preventDefault();
                OAuthAPI.loginWithMicrosoft();
            });
        }
        
        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = form.querySelector('[type="submit"]');
            const originalText = submitBtn.textContent;
            
            try {
                submitBtn.textContent = 'Creating account...';
                submitBtn.disabled = true;
                
                const formData = new FormData(form);
                await AuthForms.handleSignup(formData);
                
            } catch (error) {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                
                // Show error message
                const errorMsg = error.message || 'Signup failed. Please try again.';
                
                // Display error in the error alert
                const errorAlert = document.getElementById('errorAlert');
                const errorMessage = document.getElementById('errorMessage');
                if (errorAlert && errorMessage) {
                    errorMessage.textContent = errorMsg;
                    errorAlert.style.display = 'block';
                } else {
                    alert(errorMsg); // Fallback to alert
                }
            }
        });
    },
    
    setupLoginForm() {
        const form = document.getElementById('loginForm');
        if (!form) return;
        
        // OAuth buttons
        const googleBtn = form.querySelector('.google-btn, [data-provider="google"]');
        const microsoftBtn = form.querySelector('.microsoft-btn, [data-provider="microsoft"]');
        
        if (googleBtn) {
            googleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                OAuthAPI.loginWithGoogle();
            });
        }
        
        if (microsoftBtn) {
            microsoftBtn.addEventListener('click', (e) => {
                e.preventDefault();
                OAuthAPI.loginWithMicrosoft();
            });
        }
        
        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = form.querySelector('[type="submit"]');
            const originalText = submitBtn.textContent;
            
            try {
                submitBtn.textContent = 'Logging in...';
                submitBtn.disabled = true;
                
                const formData = new FormData(form);
                await AuthForms.handleLogin(formData);
                
            } catch (error) {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                
                // Show error message
                const errorMsg = error.message || 'Login failed. Please try again.';
                alert(errorMsg); // In production, use a proper error display
            }
        });
    }
};

// Initialize authentication on page load
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        // Setup forms if on auth pages
        AuthForms.setupSignupForm();
        AuthForms.setupLoginForm();
        
        // Handle OAuth callbacks
        if (window.location.pathname.includes('/oauth/') && window.location.pathname.includes('/callback')) {
            OAuthAPI.handleOAuthCallback();
        }
        
        // Update UI based on auth state
        const updateAuthUI = () => {
            const isAuthenticated = TokenManager.isAuthenticated();
            const user = UserManager.getUser();
            
            // Update navigation
            const loginLink = document.querySelector('a[href="/login"]');
            const signupLink = document.querySelector('a[href="/signup"]');
            const logoutBtn = document.querySelector('.logout-btn');
            const userMenu = document.querySelector('.user-menu');
            
            if (isAuthenticated && user) {
                if (loginLink) loginLink.style.display = 'none';
                if (signupLink) signupLink.style.display = 'none';
                if (logoutBtn) logoutBtn.style.display = 'block';
                if (userMenu) {
                    userMenu.style.display = 'block';
                    const userEmail = userMenu.querySelector('.user-email');
                    if (userEmail) userEmail.textContent = user.email;
                }
            } else {
                if (loginLink) loginLink.style.display = 'block';
                if (signupLink) signupLink.style.display = 'block';
                if (logoutBtn) logoutBtn.style.display = 'none';
                if (userMenu) userMenu.style.display = 'none';
            }
        };
        
        updateAuthUI();
        
        // Logout button handler
        const logoutBtn = document.querySelector('.logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                await AuthAPI.logout();
            });
        }
    });
}

// Export for use in other modules
window.BankAuth = {
    TokenManager,
    UserManager,
    AuthAPI,
    StatementAPI,
    FeedbackAPI,
    OAuthAPI,
    AuthForms
};