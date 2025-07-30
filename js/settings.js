// Settings Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html?redirect=settings';
        return;
    }

    // Initialize settings
    loadUserInfo();
    loadSettings();
    setupEventListeners();
    setupNavigationHandlers();
});

// Load user information
async function loadUserInfo() {
    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            const user = await response.json();
            
            // Update navigation
            document.getElementById('userEmail').textContent = user.email;
            
            // Populate profile form
            document.getElementById('fullName').value = user.fullName || '';
            document.getElementById('email').value = user.email || '';
            document.getElementById('company').value = user.company || '';
            document.getElementById('timezone').value = user.timezone || 'UTC';
            
            // Update plan info
            updatePlanInfo(user);
            
            // Store user info
            window.currentUser = user;
        } else if (response.status === 401) {
            // Token expired
            localStorage.removeItem('access_token');
            window.location.href = '/login.html?redirect=settings';
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

// Load user settings
async function loadSettings() {
    try {
        const response = await fetch('/api/user/settings', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            const settings = await response.json();
            
            // Populate notification settings
            document.getElementById('emailConversions').checked = settings.notifications?.emailConversions ?? true;
            document.getElementById('emailSecurity').checked = settings.notifications?.emailSecurity ?? true;
            document.getElementById('emailUpdates').checked = settings.notifications?.emailUpdates ?? false;
            document.getElementById('emailMarketing').checked = settings.notifications?.emailMarketing ?? false;
            
            // Populate preferences
            document.getElementById('defaultFormat').value = settings.preferences?.defaultFormat || 'csv';
            document.getElementById('dateFormat').value = settings.preferences?.dateFormat || 'MM/DD/YYYY';
            document.getElementById('autoDownload').checked = settings.preferences?.autoDownload ?? false;
            document.getElementById('saveHistory').checked = settings.preferences?.saveHistory ?? true;
            document.getElementById('analytics').checked = settings.preferences?.analytics ?? true;
            
            // Load 2FA status
            update2FAStatus(settings.twoFactorEnabled);
            
            // Load login history
            loadLoginHistory();
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Setup navigation handlers
function setupNavigationHandlers() {
    const navItems = document.querySelectorAll('.settings-nav-item');
    const panels = document.querySelectorAll('.settings-panel');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetSection = this.getAttribute('data-section');
            
            // Update active nav item
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            
            // Update active panel
            panels.forEach(panel => panel.classList.remove('active'));
            document.getElementById(`${targetSection}-panel`).classList.add('active');
            
            // Update URL hash
            window.location.hash = targetSection;
        });
    });
    
    // Handle initial hash
    const hash = window.location.hash.slice(1);
    if (hash) {
        const navItem = document.querySelector(`[data-section="${hash}"]`);
        if (navItem) {
            navItem.click();
        }
    }
}

// Setup event listeners
function setupEventListeners() {
    // Profile form
    document.getElementById('profileForm').addEventListener('submit', handleProfileUpdate);
    
    // Password form
    document.getElementById('passwordForm').addEventListener('submit', handlePasswordChange);
    
    // Password strength checker
    document.getElementById('newPassword').addEventListener('input', checkPasswordStrength);
    
    // Notifications form
    document.getElementById('notificationsForm').addEventListener('submit', handleNotificationsUpdate);
    
    // Preferences form
    document.getElementById('preferencesForm').addEventListener('submit', handlePreferencesUpdate);
    
    // 2FA toggle
    document.getElementById('toggle2FA').addEventListener('click', handle2FAToggle);
    
    // Export data
    document.getElementById('exportData').addEventListener('click', handleDataExport);
    
    // Delete account
    document.getElementById('deleteAccount').addEventListener('click', handleDeleteAccount);
    
    // Delete confirmation
    document.getElementById('deleteConfirmation').addEventListener('input', function() {
        const confirmBtn = document.getElementById('confirmDelete');
        confirmBtn.disabled = this.value !== 'DELETE';
    });
    
    document.getElementById('confirmDelete').addEventListener('click', confirmAccountDeletion);
    
    // User menu toggle
    const userMenuToggle = document.getElementById('userMenuToggle');
    const userMenu = document.querySelector('.user-menu');
    
    if (userMenuToggle) {
        userMenuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            userMenu.classList.toggle('active');
        });
    }
    
    // Close user menu on outside click
    document.addEventListener('click', function() {
        userMenu?.classList.remove('active');
    });
    
    // Logout buttons
    document.getElementById('logoutBtn')?.addEventListener('click', logout);
    document.getElementById('logoutBtnMobile')?.addEventListener('click', logout);
    
    // Mobile menu
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');
        });
    }
}

// Handle profile update
async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch('/api/user/profile', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Profile updated successfully', 'success');
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update profile', 'error');
        }
    } catch (error) {
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
        showNotification('Passwords do not match', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/user/change-password', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                currentPassword,
                newPassword
            })
        });
        
        if (response.ok) {
            showNotification('Password changed successfully', 'success');
            e.target.reset();
            document.querySelector('.strength-bar').className = 'strength-bar';
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to change password', 'error');
        }
    } catch (error) {
        showNotification('Error changing password', 'error');
    }
}

// Check password strength
function checkPasswordStrength(e) {
    const password = e.target.value;
    const strengthBar = document.querySelector('.strength-bar');
    
    if (password.length === 0) {
        strengthBar.className = 'strength-bar';
        return;
    }
    
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // Character variety
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    // Update strength indicator
    if (strength <= 2) {
        strengthBar.className = 'strength-bar strength-weak';
    } else if (strength <= 4) {
        strengthBar.className = 'strength-bar strength-medium';
    } else {
        strengthBar.className = 'strength-bar strength-strong';
    }
}

// Handle notifications update
async function handleNotificationsUpdate(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const notifications = {
        emailConversions: formData.get('emailConversions') === 'on',
        emailSecurity: formData.get('emailSecurity') === 'on',
        emailUpdates: formData.get('emailUpdates') === 'on',
        emailMarketing: formData.get('emailMarketing') === 'on'
    };
    
    try {
        const response = await fetch('/api/user/settings/notifications', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(notifications)
        });
        
        if (response.ok) {
            showNotification('Notification preferences updated', 'success');
        } else {
            showNotification('Failed to update notifications', 'error');
        }
    } catch (error) {
        showNotification('Error updating notifications', 'error');
    }
}

// Handle preferences update
async function handlePreferencesUpdate(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const preferences = {
        defaultFormat: formData.get('defaultFormat'),
        dateFormat: formData.get('dateFormat'),
        autoDownload: formData.get('autoDownload') === 'on',
        saveHistory: formData.get('saveHistory') === 'on',
        analytics: formData.get('analytics') === 'on'
    };
    
    try {
        const response = await fetch('/api/user/settings/preferences', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(preferences)
        });
        
        if (response.ok) {
            showNotification('Preferences updated successfully', 'success');
        } else {
            showNotification('Failed to update preferences', 'error');
        }
    } catch (error) {
        showNotification('Error updating preferences', 'error');
    }
}

// Handle 2FA toggle
async function handle2FAToggle() {
    const is2FAEnabled = document.getElementById('2faStatus').textContent === 'Enabled';
    
    if (is2FAEnabled) {
        // Disable 2FA
        if (confirm('Are you sure you want to disable two-factor authentication?')) {
            try {
                const response = await fetch('/api/user/2fa/disable', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                });
                
                if (response.ok) {
                    update2FAStatus(false);
                    showNotification('Two-factor authentication disabled', 'success');
                }
            } catch (error) {
                showNotification('Error disabling 2FA', 'error');
            }
        }
    } else {
        // Enable 2FA - would typically show QR code modal
        showNotification('2FA setup coming soon', 'info');
    }
}

// Update 2FA status display
function update2FAStatus(enabled) {
    const statusElement = document.getElementById('2faStatus');
    const toggleButton = document.getElementById('toggle2FA');
    
    if (enabled) {
        statusElement.textContent = 'Enabled';
        statusElement.className = 'status-value enabled';
        toggleButton.textContent = 'Disable 2FA';
        toggleButton.classList.remove('btn-primary');
        toggleButton.classList.add('btn-secondary');
    } else {
        statusElement.textContent = 'Disabled';
        statusElement.className = 'status-value';
        toggleButton.textContent = 'Enable 2FA';
        toggleButton.classList.remove('btn-secondary');
        toggleButton.classList.add('btn-primary');
    }
}

// Load login history
async function loadLoginHistory() {
    try {
        const response = await fetch('/api/user/login-history', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const history = await response.json();
            const container = document.getElementById('loginHistory');
            
            if (history.length === 0) {
                container.innerHTML = '<p class="empty-message">No login history available</p>';
            } else {
                container.innerHTML = history.slice(0, 5).map(login => `
                    <div class="login-item">
                        <div class="login-info">
                            <div class="login-icon">
                                <i class="fas fa-${getDeviceIcon(login.device)}"></i>
                            </div>
                            <div class="login-details">
                                <h4>${login.browser || 'Unknown Browser'} on ${login.os || 'Unknown OS'}</h4>
                                <p>${login.ip_address || 'Unknown IP'} • ${login.location || 'Unknown Location'}</p>
                            </div>
                        </div>
                        <div class="login-time">
                            ${formatDateTime(login.created_at)}
                        </div>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading login history:', error);
    }
}

// Update plan info
function updatePlanInfo(user) {
    const planName = document.getElementById('currentPlanName');
    const planDetails = document.getElementById('currentPlanDetails');
    const monthlyUsage = document.getElementById('monthlyUsage');
    const usageProgress = document.getElementById('usageProgress');
    
    // Set plan name and details based on user plan
    if (user.plan === 'pro') {
        planName.textContent = 'Professional Plan';
        planDetails.textContent = '100 conversions per month';
        monthlyUsage.textContent = `${user.monthlyUsage || 0} / 100`;
        usageProgress.style.width = `${(user.monthlyUsage || 0) / 100 * 100}%`;
    } else if (user.plan === 'business') {
        planName.textContent = 'Business Plan';
        planDetails.textContent = '500 conversions per month';
        monthlyUsage.textContent = `${user.monthlyUsage || 0} / 500`;
        usageProgress.style.width = `${(user.monthlyUsage || 0) / 500 * 100}%`;
    } else {
        planName.textContent = 'Free Plan';
        planDetails.textContent = '5 conversions per day';
        monthlyUsage.textContent = `${user.monthlyUsage || 0} / 150`;
        usageProgress.style.width = `${(user.monthlyUsage || 0) / 150 * 100}%`;
    }
}

// Handle data export
async function handleDataExport() {
    try {
        const response = await fetch('/api/user/export-data', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bankcsv-data-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showNotification('Data exported successfully', 'success');
        } else {
            showNotification('Failed to export data', 'error');
        }
    } catch (error) {
        showNotification('Error exporting data', 'error');
    }
}

// Handle delete account
function handleDeleteAccount() {
    document.getElementById('deleteAccountModal').classList.add('active');
}

// Confirm account deletion
async function confirmAccountDeletion() {
    try {
        const response = await fetch('/api/user/delete-account', {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            localStorage.clear();
            window.location.href = '/';
        } else {
            showNotification('Failed to delete account', 'error');
        }
    } catch (error) {
        showNotification('Error deleting account', 'error');
    }
}

// Close modal
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    if (modalId === 'deleteAccountModal') {
        document.getElementById('deleteConfirmation').value = '';
        document.getElementById('confirmDelete').disabled = true;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Utility functions
function getDeviceIcon(device) {
    if (!device) return 'desktop';
    if (device.includes('mobile') || device.includes('phone')) return 'mobile-alt';
    if (device.includes('tablet')) return 'tablet-alt';
    return 'desktop';
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)} days ago`;
    
    return date.toLocaleDateString();
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

// Add notification styles if not present
if (!document.querySelector('#notification-styles')) {
    const styles = document.createElement('style');
    styles.id = 'notification-styles';
    styles.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            z-index: 10000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification-success {
            border-left: 4px solid #28a745;
        }
        
        .notification-error {
            border-left: 4px solid #dc3545;
        }
        
        .notification-info {
            border-left: 4px solid #17a2b8;
        }
        
        .notification i {
            font-size: 18px;
        }
        
        .notification-success i {
            color: #28a745;
        }
        
        .notification-error i {
            color: #dc3545;
        }
        
        .notification-info i {
            color: #17a2b8;
        }
    `;
    document.head.appendChild(styles);
}

// Make closeModal function global for onclick handlers
window.closeModal = closeModal;