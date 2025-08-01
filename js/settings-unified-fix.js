// Settings Page JavaScript - Fixed for UnifiedAuth Race Condition

// API base URL
const API_BASE = (() => {
    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
    const base = isLocal ? 'http://localhost:5000' : `${window.location.protocol}//${hostname}`;
    return `${base}/v2/api`;
})();

document.addEventListener('DOMContentLoaded', async function() {
    console.log('[Settings] Page loading...');
    
    // Wait for UnifiedAuth to initialize (same fix as dashboard)
    const waitForAuth = async () => {
        let attempts = 0;
        while (attempts < 50) { // Wait up to 5 seconds
            if (window.UnifiedAuth && window.UnifiedAuth.initialized) {
                console.log('[Settings] UnifiedAuth initialized');
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        return false;
    };
    
    // Wait for auth to be ready
    const authReady = await waitForAuth();
    if (!authReady) {
        console.error('[Settings] UnifiedAuth not initialized after 5 seconds');
        window.location.href = '/';
        return;
    }
    
    // Now check authentication
    if (!window.UnifiedAuth.isAuthenticated()) {
        console.log('[Settings] User not authenticated, redirecting to login');
        window.location.href = '/login.html?redirect=settings';
        return;
    }
    
    console.log('[Settings] User authenticated, loading settings');
    
    // Initialize settings
    await loadUserInfo();
    await loadSettings();
    setupEventListeners();
    setupNavigationHandlers();
});

// Load user information
async function loadUserInfo() {
    try {
        // Get user from UnifiedAuth
        const user = window.UnifiedAuth.getUser();
        if (!user) {
            console.error('[Settings] No user data found');
            window.location.href = '/login.html?redirect=settings';
            return;
        }
        
        console.log('[Settings] Loading user info:', user.email);
        
        // Update navigation if element exists
        const userEmailElement = document.getElementById('userEmail');
        if (userEmailElement) {
            userEmailElement.textContent = user.email;
        }
        
        // Populate profile form
        const fullNameInput = document.getElementById('fullName');
        const emailInput = document.getElementById('email');
        const companyInput = document.getElementById('company');
        const timezoneInput = document.getElementById('timezone');
        
        if (fullNameInput) fullNameInput.value = user.full_name || '';
        if (emailInput) emailInput.value = user.email || '';
        if (companyInput) companyInput.value = user.company_name || '';
        if (timezoneInput) timezoneInput.value = user.timezone || 'UTC';
        
        // Load user data from backend
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/profile`);
        if (response.ok) {
            const userData = await response.json();
            console.log('[Settings] User data from backend:', userData);
            
            // Update form with backend data
            if (fullNameInput) fullNameInput.value = userData.full_name || '';
            if (companyInput) companyInput.value = userData.company_name || '';
            if (timezoneInput) timezoneInput.value = userData.timezone || 'UTC';
        }
    } catch (error) {
        console.error('[Settings] Error loading user info:', error);
        showNotification('Error loading user information', 'error');
    }
}

// Load settings
async function loadSettings() {
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/settings`);
        if (response.ok) {
            const settings = await response.json();
            console.log('[Settings] Loaded settings:', settings);
            
            // Apply settings to form
            applySettingsToForm(settings);
        }
    } catch (error) {
        console.error('[Settings] Error loading settings:', error);
        // Settings might not exist yet, that's ok
    }
}

// Apply settings to form
function applySettingsToForm(settings) {
    // Email notifications
    const emailNotifications = document.getElementById('emailNotifications');
    if (emailNotifications) {
        emailNotifications.checked = settings.email_notifications !== false;
    }
    
    // Two-factor auth
    const twoFactorAuth = document.getElementById('twoFactorAuth');
    if (twoFactorAuth) {
        twoFactorAuth.checked = settings.two_factor_enabled === true;
    }
    
    // API access
    const apiAccess = document.getElementById('apiAccess');
    if (apiAccess) {
        apiAccess.checked = settings.api_access_enabled === true;
    }
    
    // Data retention
    const dataRetention = document.getElementById('dataRetention');
    if (dataRetention) {
        dataRetention.value = settings.data_retention_days || '30';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Profile form
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }
    
    // Password form
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', handlePasswordChange);
    }
    
    // Settings form
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', handleSettingsUpdate);
    }
    
    // Generate API key button
    const generateApiKeyBtn = document.getElementById('generateApiKey');
    if (generateApiKeyBtn) {
        generateApiKeyBtn.addEventListener('click', handleGenerateApiKey);
    }
    
    // Delete account button
    const deleteAccountBtn = document.getElementById('deleteAccount');
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', handleDeleteAccount);
    }
}

// Handle profile update
async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const formData = {
        full_name: document.getElementById('fullName').value,
        company_name: document.getElementById('company').value,
        timezone: document.getElementById('timezone').value
    };
    
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            showNotification('Profile updated successfully', 'success');
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('[Settings] Profile update error:', error);
        showNotification('Error updating profile', 'error');
    }
}

// Handle password change
async function handlePasswordChange(e) {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (newPassword !== confirmPassword) {
        showNotification('New passwords do not match', 'error');
        return;
    }
    
    if (newPassword.length < 8) {
        showNotification('Password must be at least 8 characters long', 'error');
        return;
    }
    
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/password`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        if (response.ok) {
            showNotification('Password changed successfully', 'success');
            // Clear form
            document.getElementById('passwordForm').reset();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to change password', 'error');
        }
    } catch (error) {
        console.error('[Settings] Password change error:', error);
        showNotification('Error changing password', 'error');
    }
}

// Handle settings update
async function handleSettingsUpdate(e) {
    e.preventDefault();
    
    const settings = {
        email_notifications: document.getElementById('emailNotifications').checked,
        two_factor_enabled: document.getElementById('twoFactorAuth').checked,
        api_access_enabled: document.getElementById('apiAccess').checked,
        data_retention_days: parseInt(document.getElementById('dataRetention').value)
    };
    
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            showNotification('Settings updated successfully', 'success');
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update settings', 'error');
        }
    } catch (error) {
        console.error('[Settings] Settings update error:', error);
        showNotification('Error updating settings', 'error');
    }
}

// Handle generate API key
async function handleGenerateApiKey() {
    if (!confirm('This will invalidate your current API key. Continue?')) {
        return;
    }
    
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/api-key`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('apiKey').value = data.api_key;
            showNotification('New API key generated', 'success');
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to generate API key', 'error');
        }
    } catch (error) {
        console.error('[Settings] API key generation error:', error);
        showNotification('Error generating API key', 'error');
    }
}

// Handle delete account
async function handleDeleteAccount() {
    const confirmText = prompt('To delete your account, type "DELETE" below:');
    if (confirmText !== 'DELETE') {
        return;
    }
    
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/account`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Account deleted successfully', 'success');
            // Logout and redirect
            await window.UnifiedAuth.logout();
            window.location.href = '/';
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to delete account', 'error');
        }
    } catch (error) {
        console.error('[Settings] Account deletion error:', error);
        showNotification('Error deleting account', 'error');
    }
}

// Setup navigation handlers
function setupNavigationHandlers() {
    // Settings navigation
    const settingsLinks = document.querySelectorAll('.settings-nav a');
    const settingsSections = document.querySelectorAll('.settings-section');
    
    settingsLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all
            settingsLinks.forEach(l => l.classList.remove('active'));
            settingsSections.forEach(s => s.classList.remove('active'));
            
            // Add active to clicked
            link.classList.add('active');
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.classList.add('active');
            }
        });
    });
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}-circle"></i>
        <span>${message}</span>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}