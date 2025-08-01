// Settings Page JavaScript - Updated for UnifiedAuth

// API base URL
const API_BASE = (() => {
    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
    const base = isLocal ? 'http://localhost:5000' : `${window.location.protocol}//${hostname}`;
    return `${base}/v2/api`;
})();

document.addEventListener('DOMContentLoaded', async function() {
    // Wait for UnifiedAuth to initialize
    if (!window.UnifiedAuth) {
        console.error('UnifiedAuth not loaded');
        window.location.href = '/';
        return;
    }

    // Check authentication
    if (!window.UnifiedAuth.isAuthenticated()) {
        window.location.href = '/login.html?redirect=settings';
        return;
    }

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
            window.location.href = '/login.html?redirect=settings';
            return;
        }
        
        // Update navigation
        document.getElementById('userEmail').textContent = user.email;
        
        // Populate profile form
        document.getElementById('fullName').value = user.full_name || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('company').value = user.company_name || '';
        document.getElementById('timezone').value = user.timezone || 'UTC';
        
        // Update plan info
        updatePlanInfo(user);
        
        // Store user info
        window.currentUser = user;
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

// Load user settings
async function loadSettings() {
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/settings`);

        if (response.ok) {
            const settings = await response.json();
            
            // Email preferences
            if (settings.emailPreferences) {
                document.getElementById('marketingEmails').checked = settings.emailPreferences.marketing || false;
                document.getElementById('productUpdates').checked = settings.emailPreferences.productUpdates || false;
                document.getElementById('usageAlerts').checked = settings.emailPreferences.usageAlerts || true;
            }
            
            // Privacy settings
            if (settings.privacy) {
                document.getElementById('shareUsageData').checked = settings.privacy.shareUsageData || false;
            }
            
            // Export preferences
            if (settings.exportPreferences) {
                document.getElementById('defaultFormat').value = settings.exportPreferences.defaultFormat || 'csv';
                document.getElementById('includeHeaders').checked = settings.exportPreferences.includeHeaders !== false;
                document.getElementById('dateFormat').value = settings.exportPreferences.dateFormat || 'YYYY-MM-DD';
            }
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Save profile information
async function saveProfile(event) {
    event.preventDefault();
    
    const saveButton = event.target.querySelector('button[type="submit"]');
    const originalText = saveButton.textContent;
    saveButton.textContent = 'Saving...';
    saveButton.disabled = true;
    
    try {
        const profileData = {
            fullName: document.getElementById('fullName').value,
            company: document.getElementById('company').value,
            timezone: document.getElementById('timezone').value
        };
        
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });
        
        if (response.ok) {
            showNotification('Profile updated successfully', 'success');
        } else {
            showNotification('Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Error saving profile:', error);
        showNotification('An error occurred while saving', 'error');
    } finally {
        saveButton.textContent = originalText;
        saveButton.disabled = false;
    }
}

// Save notification preferences
async function saveNotifications(event) {
    event.preventDefault();
    
    const saveButton = event.target.querySelector('button[type="submit"]');
    const originalText = saveButton.textContent;
    saveButton.textContent = 'Saving...';
    saveButton.disabled = true;
    
    try {
        const preferences = {
            emailPreferences: {
                marketing: document.getElementById('marketingEmails').checked,
                productUpdates: document.getElementById('productUpdates').checked,
                usageAlerts: document.getElementById('usageAlerts').checked
            }
        };
        
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(preferences)
        });
        
        if (response.ok) {
            showNotification('Notification preferences updated', 'success');
        } else {
            showNotification('Failed to update preferences', 'error');
        }
    } catch (error) {
        console.error('Error saving preferences:', error);
        showNotification('An error occurred while saving', 'error');
    } finally {
        saveButton.textContent = originalText;
        saveButton.disabled = false;
    }
}

// Save privacy settings
async function savePrivacy(event) {
    event.preventDefault();
    
    const saveButton = event.target.querySelector('button[type="submit"]');
    const originalText = saveButton.textContent;
    saveButton.textContent = 'Saving...';
    saveButton.disabled = true;
    
    try {
        const privacy = {
            privacy: {
                shareUsageData: document.getElementById('shareUsageData').checked
            }
        };
        
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(privacy)
        });
        
        if (response.ok) {
            showNotification('Privacy settings updated', 'success');
        } else {
            showNotification('Failed to update privacy settings', 'error');
        }
    } catch (error) {
        console.error('Error saving privacy settings:', error);
        showNotification('An error occurred while saving', 'error');
    } finally {
        saveButton.textContent = originalText;
        saveButton.disabled = false;
    }
}

// Delete account
async function deleteAccount() {
    const confirmDelete = confirm('Are you sure you want to delete your account? This action cannot be undone.');
    
    if (!confirmDelete) {
        return;
    }
    
    const doubleConfirm = prompt('Please type "DELETE" to confirm account deletion:');
    
    if (doubleConfirm !== 'DELETE') {
        return;
    }
    
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/account`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Log out and redirect
            await window.UnifiedAuth.logout();
        } else {
            showNotification('Failed to delete account', 'error');
        }
    } catch (error) {
        console.error('Error deleting account:', error);
        showNotification('An error occurred while deleting account', 'error');
    }
}

// Export user data
async function exportUserData() {
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/user/export`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'user-data-export.json';
            a.click();
            URL.revokeObjectURL(url);
            
            showNotification('Your data has been exported', 'success');
        } else {
            showNotification('Failed to export data', 'error');
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        showNotification('An error occurred while exporting data', 'error');
    }
}

// Manage subscription
function manageSubscription() {
    window.location.href = '/pricing.html';
}

// Update plan info display
function updatePlanInfo(user) {
    const planBadge = document.querySelector('.plan-badge');
    if (planBadge) {
        planBadge.textContent = user.account_type || 'Free';
        planBadge.className = `plan-badge ${(user.account_type || 'free').toLowerCase()}`;
    }
    
    const usageText = document.querySelector('.usage-text');
    if (usageText) {
        usageText.textContent = `${user.daily_generations || 0} / ${user.daily_limit || 5} conversions used today`;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Setup event listeners
function setupEventListeners() {
    // Profile form
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', saveProfile);
    }
    
    // Notification form
    const notificationForm = document.getElementById('notificationForm');
    if (notificationForm) {
        notificationForm.addEventListener('submit', saveNotifications);
    }
    
    // Privacy form
    const privacyForm = document.getElementById('privacyForm');
    if (privacyForm) {
        privacyForm.addEventListener('submit', savePrivacy);
    }
    
    // Delete account button
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', deleteAccount);
    }
    
    // Export data button
    const exportDataBtn = document.getElementById('exportDataBtn');
    if (exportDataBtn) {
        exportDataBtn.addEventListener('click', exportUserData);
    }
    
    // Manage subscription button
    const manageSubBtn = document.getElementById('manageSubscriptionBtn');
    if (manageSubBtn) {
        manageSubBtn.addEventListener('click', manageSubscription);
    }
}

// Setup navigation handlers
function setupNavigationHandlers() {
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Update active states
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            const targetContent = document.getElementById(`${tabName}Tab`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 24px;
    background: #333;
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transform: translateX(400px);
    transition: transform 0.3s ease;
    z-index: 1000;
}

.notification.show {
    transform: translateX(0);
}

.notification.success {
    background: #10B981;
}

.notification.error {
    background: #EF4444;
}

.notification.info {
    background: #3B82F6;
}
`;
document.head.appendChild(style);