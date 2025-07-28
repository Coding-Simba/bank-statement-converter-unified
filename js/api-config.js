// API Configuration
const API_CONFIG = {
    // Dynamically determine the API URL based on the current environment
    getBaseUrl() {
        // Check if we're on localhost
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return 'http://localhost:5000';
        }
        // In production, use the main domain without port (nginx handles the proxy)
        return `${window.location.protocol}//${window.location.hostname}`;
    },
    
    // API endpoints
    endpoints: {
        convert: '/api/convert',
        splitStatement: '/api/split-statement',
        testExtraction: '/api/test-extraction',
        checkLimit: '/api/check-limit',
        feedback: '/api/feedback',
        auth: {
            login: '/api/auth/login',
            signup: '/api/auth/signup',
            logout: '/api/auth/logout',
            profile: '/api/auth/profile'
        }
    },
    
    // Get full URL for an endpoint
    getUrl(endpoint) {
        return this.getBaseUrl() + endpoint;
    }
};

// Export for use in other scripts
window.API_CONFIG = API_CONFIG;