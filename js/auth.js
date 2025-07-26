// Authentication module for Bank Statement Converter

const AUTH_API_BASE = 'http://localhost:5000/api/auth';
const API_BASE = 'http://localhost:5000/api';

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
    async register(email, password) {
        try {
            const response = await fetch(`${AUTH_API_BASE}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
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

// Export for use in other modules
window.BankAuth = {
    TokenManager,
    UserManager,
    AuthAPI,
    StatementAPI,
    FeedbackAPI,
};