// Settings Page - Fully Integrated with Backend
// This replaces settings-unified.js with proper backend integration

document.addEventListener('DOMContentLoaded', async function() {
    // Initialize settings system
    await initializeSettings();
});

// Global state
let currentUser = null;
let csrfToken = null;

// Initialize settings
async function initializeSettings() {
    try {
        // Get CSRF token first
        await getCsrfToken();
        
        // Check authentication using cookie auth
        const authCheck = await checkAuthentication();
        if (!authCheck) {
            window.location.href = '/login.html?redirect=' + encodeURIComponent(window.location.pathname);
            return;
        }
        
        // Load user data
        await loadUserProfile();
        
        // Setup all components
        setupPanelNavigation();
        setupFormHandlers();
        setupModalHandlers();
        setupPreferencesAutoSave();
        
        // Load initial data
        await loadAllSettings();
        
    } catch (error) {
        console.error('Settings initialization error:', error);
        showNotification('Failed to initialize settings', 'error');
    }
}

// Get CSRF token
async function getCsrfToken() {
    try {
        const response = await fetch('/v2/api/auth/csrf', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            csrfToken = data.csrf_token;
        }
    } catch (error) {
        console.error('Failed to get CSRF token:', error);
    }
}

// Check authentication
async function checkAuthentication() {
    try {
        const response = await fetch('/v2/api/auth/me', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'X-CSRF-Token': csrfToken || ''
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            updateUserDisplay();
            return true;
        }
        
        // Try legacy JWT auth
        const token = localStorage.getItem('access_token');
        if (token) {
            const jwtResponse = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (jwtResponse.ok) {
                currentUser = await jwtResponse.json();
                updateUserDisplay();
                return true;
            }
        }
        
        return false;
    } catch (error) {
        console.error('Auth check failed:', error);
        return false;
    }
}

// Update user display
function updateUserDisplay() {
    if (currentUser) {
        const userEmailEl = document.getElementById('userEmail');
        if (userEmailEl) {
            userEmailEl.textContent = currentUser.email || 'User';
        }
    }
}

// Load user profile
async function loadUserProfile() {
    try {
        const response = await makeAuthRequest('/api/user/profile');
        if (response.ok) {
            const profile = await response.json();
            
            // Update profile form
            setValue('fullName', profile.full_name);
            setValue('email', profile.email);
            setValue('company', profile.company_name);
            setValue('timezone', profile.timezone || 'UTC');
            
            // Update plan info
            updatePlanDisplay(profile);
            
            // Update 2FA status
            if (profile.two_factor_enabled) {
                document.getElementById('2faStatus').textContent = 'Enabled';
                document.getElementById('2faStatus').classList.add('enabled');
                document.getElementById('toggle2FA').textContent = 'Disable 2FA';
            }
        }
    } catch (error) {
        console.error('Failed to load profile:', error);
    }
}

// Load all settings
async function loadAllSettings() {
    try {
        // Load settings summary
        const response = await makeAuthRequest('/api/user/settings');
        if (response.ok) {
            const settings = await response.json();
            
            // Update notifications
            if (settings.notifications) {
                setValue('emailConversions', true); // Default
                setValue('emailSecurity', settings.notifications.security_alerts);
                setValue('emailUpdates', settings.notifications.product_updates);
                setValue('emailMarketing', settings.notifications.marketing_emails);
            }
            
            // Update usage stats
            if (settings.account) {
                updateUsageDisplay(settings.account);
            }
            
            // Update subscription info
            if (settings.subscription) {
                updateSubscriptionDisplay(settings.subscription);
            }
        }
        
        // Load preferences (if endpoint exists)
        await loadPreferences();
        
        // Load login history
        await loadLoginHistory();
        
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

// Setup panel navigation
function setupPanelNavigation() {
    const navItems = document.querySelectorAll('.settings-nav-item');
    const panels = document.querySelectorAll('.settings-panel');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            
            // Update active states
            navItems.forEach(nav => nav.classList.remove('active'));
            panels.forEach(panel => panel.classList.remove('active'));
            
            item.classList.add('active');
            const targetPanel = document.getElementById(`${section}-panel`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
            
            // Update URL hash
            window.location.hash = section;
        });
    });
    
    // Handle initial hash
    if (window.location.hash) {
        const target = document.querySelector(`[data-section="${window.location.hash.slice(1)}"]`);
        if (target) {
            target.click();
        }
    }
}

// Setup form handlers
function setupFormHandlers() {
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
    
    // Notifications form
    const notificationsForm = document.getElementById('notificationsForm');
    if (notificationsForm) {
        notificationsForm.addEventListener('submit', handleNotificationUpdate);
    }
    
    // Preferences form
    const preferencesForm = document.getElementById('preferencesForm');
    if (preferencesForm) {
        preferencesForm.addEventListener('submit', handlePreferencesUpdate);
    }
    
    // 2FA toggle
    const toggle2FA = document.getElementById('toggle2FA');
    if (toggle2FA) {
        toggle2FA.addEventListener('click', handle2FAToggle);
    }
    
    // Export data
    const exportBtn = document.getElementById('exportData');
    if (exportBtn) {
        exportBtn.addEventListener('click', handleDataExport);
    }
    
    // Delete account
    const deleteBtn = document.getElementById('deleteAccount');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', handleAccountDelete);
    }
    
    // Add payment method
    const addPaymentBtn = document.getElementById('addPaymentMethod');
    if (addPaymentBtn) {
        addPaymentBtn.addEventListener('click', handleAddPaymentMethod);
    }
    
    // Password strength indicator
    const newPasswordInput = document.getElementById('newPassword');
    if (newPasswordInput) {
        newPasswordInput.addEventListener('input', updatePasswordStrength);
    }
}

// Handle profile update
async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    submitBtn.disabled = true;
    
    try {
        const formData = {
            full_name: getValue('fullName'),
            company_name: getValue('company'),
            timezone: getValue('timezone')
        };
        
        // Check if email changed
        const newEmail = getValue('email');
        if (newEmail !== currentUser.email) {
            formData.email = newEmail;
        }
        
        const response = await makeAuthRequest('/api/user/profile', {
            method: 'PUT',
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('Profile updated successfully', 'success');
            
            if (result.email_verification_sent) {
                showNotification('Please check your email to verify the new address', 'info');
            }
            
            // Reload profile
            await loadUserProfile();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showNotification('An error occurred while updating profile', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Handle password change
async function handlePasswordChange(e) {
    e.preventDefault();
    
    const currentPassword = getValue('currentPassword');
    const newPassword = getValue('newPassword');
    const confirmPassword = getValue('confirmPassword');
    
    // Validate passwords match
    if (newPassword !== confirmPassword) {
        showNotification('New passwords do not match', 'error');
        return;
    }
    
    // Validate password strength
    if (newPassword.length < 8) {
        showNotification('Password must be at least 8 characters long', 'error');
        return;
    }
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
    submitBtn.disabled = true;
    
    try {
        const response = await makeAuthRequest('/api/user/password', {
            method: 'PUT',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        if (response.ok) {
            showNotification('Password changed successfully', 'success');
            e.target.reset();
            
            // Clear password strength indicator
            const strengthBar = document.querySelector('.strength-bar');
            if (strengthBar) {
                strengthBar.style.width = '0%';
                strengthBar.className = 'strength-bar';
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to change password', 'error');
        }
    } catch (error) {
        console.error('Password change error:', error);
        showNotification('An error occurred while changing password', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Handle notification preferences update
async function handleNotificationUpdate(e) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    submitBtn.disabled = true;
    
    try {
        const preferences = {
            security_alerts: getValue('emailSecurity', true),
            product_updates: getValue('emailUpdates', true),
            usage_reports: getValue('emailConversions', true),
            marketing_emails: getValue('emailMarketing', true)
        };
        
        const response = await makeAuthRequest('/api/user/notifications', {
            method: 'PUT',
            body: JSON.stringify(preferences)
        });
        
        if (response.ok) {
            showNotification('Notification preferences updated', 'success');
        } else {
            showNotification('Failed to update preferences', 'error');
        }
    } catch (error) {
        console.error('Notification update error:', error);
        showNotification('An error occurred while updating preferences', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Handle preferences update
async function handlePreferencesUpdate(e) {
    e.preventDefault();
    await savePreferences();
}

// Save preferences (used by auto-save and manual save)
async function savePreferences(showMessage = true) {
    const submitBtn = document.querySelector('#preferencesForm button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : '';
    
    if (submitBtn && showMessage) {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        submitBtn.disabled = true;
    }
    
    try {
        const preferences = {
            default_format: getValue('defaultFormat'),
            date_format: getValue('dateFormat'),
            auto_download: getValue('autoDownload', true),
            save_history: getValue('saveHistory', true),
            analytics: getValue('analytics', true)
        };
        
        // Store locally immediately
        localStorage.setItem('conversion_preferences', JSON.stringify(preferences));
        
        // Try to save to backend
        try {
            const response = await makeAuthRequest('/api/user/preferences', {
                method: 'PUT',
                body: JSON.stringify(preferences)
            });
            
            if (response.ok && showMessage) {
                showNotification('Preferences saved', 'success');
            }
        } catch (error) {
            // Silently fail for auto-save
            if (showMessage) {
                console.error('Failed to save to backend:', error);
            }
        }
        
    } catch (error) {
        console.error('Preferences save error:', error);
        if (showMessage) {
            showNotification('An error occurred while saving preferences', 'error');
        }
    } finally {
        if (submitBtn) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
}

// Setup auto-save for preferences
function setupPreferencesAutoSave() {
    // Debounce function to avoid too many saves
    let saveTimeout;
    const autoSave = () => {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            savePreferences(false); // Don't show notification for auto-save
        }, 1000); // Save 1 second after user stops changing
    };
    
    // Watch for changes in preferences form
    const preferencesForm = document.getElementById('preferencesForm');
    if (preferencesForm) {
        // Select dropdowns
        preferencesForm.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', autoSave);
        });
        
        // Checkboxes
        preferencesForm.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', autoSave);
        });
    }
}

// Handle 2FA toggle
async function handle2FAToggle() {
    const is2FAEnabled = document.getElementById('2faStatus').textContent === 'Enabled';
    
    if (is2FAEnabled) {
        // Show disable 2FA modal
        show2FADisableModal();
    } else {
        // Show enable 2FA modal
        show2FAEnableModal();
    }
}

// Show 2FA enable modal
async function show2FAEnableModal() {
    const password = prompt('Please enter your password to enable 2FA:');
    if (!password) return;
    
    try {
        const response = await makeAuthRequest('/api/user/2fa/enable', {
            method: 'POST',
            body: JSON.stringify({ password })
        });
        
        if (response.ok) {
            const data = await response.json();
            // Show QR code and backup codes
            show2FASetupModal(data);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to enable 2FA', 'error');
        }
    } catch (error) {
        console.error('2FA enable error:', error);
        showNotification('An error occurred while enabling 2FA', 'error');
    }
}

// Show 2FA setup modal
function show2FASetupModal(data) {
    // Create modal HTML
    const modalHtml = `
        <div class="modal" id="2faSetupModal" style="display: flex;">
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h3>Setup Two-Factor Authentication</h3>
                    <button class="modal-close" onclick="closeModal('2faSetupModal')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="twofa-setup-steps">
                        <div class="setup-step">
                            <div class="step-number">1</div>
                            <div class="step-content">
                                <h4>Install an Authenticator App</h4>
                                <p>If you don't have one, download:</p>
                                <ul>
                                    <li>Google Authenticator</li>
                                    <li>Microsoft Authenticator</li>
                                    <li>Authy</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="setup-step">
                            <div class="step-number">2</div>
                            <div class="step-content">
                                <h4>Add Account to Your App</h4>
                                <div class="setup-options">
                                    <div class="option-qr">
                                        <p>Scan this QR code:</p>
                                        <div class="qr-container">
                                            <img src="${data.qr_code}" alt="2FA QR Code">
                                        </div>
                                    </div>
                                    <div class="option-manual">
                                        <p>Or enter manually:</p>
                                        <div class="manual-entry">
                                            <label>Account:</label>
                                            <code>BankCSV</code>
                                            <label>Key:</label>
                                            <code class="secret-key">${data.secret}</code>
                                            <button class="btn-copy" onclick="copyToClipboard('${data.secret.replace(/ /g, '')}')">
                                                <i class="fas fa-copy"></i> Copy
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="setup-step">
                            <div class="step-number">3</div>
                            <div class="step-content">
                                <h4>Save Backup Codes</h4>
                                <p>Store these codes safely. You can use them if you lose access to your authenticator app:</p>
                                <div class="backup-codes">
                                    ${data.backup_codes.map(code => `<code>${code}</code>`).join('')}
                                </div>
                                <button class="btn btn-secondary btn-sm" onclick="downloadBackupCodes(${JSON.stringify(data.backup_codes)})">
                                    <i class="fas fa-download"></i> Download Codes
                                </button>
                            </div>
                        </div>
                        
                        <div class="setup-step">
                            <div class="step-number">4</div>
                            <div class="step-content">
                                <h4>Verify Setup</h4>
                                <p>Enter the 6-digit code from your authenticator app:</p>
                                <div class="verify-input">
                                    <input type="text" id="2faVerifyCode" class="form-control code-input" 
                                           placeholder="000000" maxlength="6" autocomplete="off">
                                    <div class="code-timer" id="codeTimer"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('2faSetupModal')">Cancel</button>
                    <button class="btn btn-primary" onclick="verify2FASetup()" id="verify2FABtn">
                        <i class="fas fa-shield-alt"></i> Verify & Enable 2FA
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Focus on input
    setTimeout(() => {
        document.getElementById('2faVerifyCode').focus();
    }, 100);
    
    // Start timer
    update2FATimer();
}

// Update 2FA timer
function update2FATimer() {
    const timerEl = document.getElementById('codeTimer');
    if (!timerEl) return;
    
    const updateTimer = () => {
        const seconds = 30 - (Math.floor(Date.now() / 1000) % 30);
        timerEl.textContent = `Code refreshes in ${seconds}s`;
        
        if (seconds <= 5) {
            timerEl.style.color = '#ef4444';
        } else {
            timerEl.style.color = '#6b7280';
        }
    };
    
    updateTimer();
    const interval = setInterval(() => {
        if (!document.getElementById('codeTimer')) {
            clearInterval(interval);
            return;
        }
        updateTimer();
    }, 1000);
}

// Copy to clipboard
window.copyToClipboard = function(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard', 'success');
    }).catch(() => {
        showNotification('Failed to copy', 'error');
    });
}

// Download backup codes
window.downloadBackupCodes = function(codes) {
    const content = `BankCSV Two-Factor Authentication Backup Codes
Generated: ${new Date().toISOString()}

IMPORTANT: Store these codes in a safe place.
Each code can only be used once.

${codes.join('\n')}

If you lose access to your authenticator app, you can use one of these codes to sign in.`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bankcsv-2fa-backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Backup codes downloaded', 'success');
}

// Verify 2FA setup
async function verify2FASetup() {
    const token = document.getElementById('2faVerifyCode').value;
    if (!token) {
        showNotification('Please enter verification code', 'error');
        return;
    }
    
    try {
        const response = await makeAuthRequest('/api/user/2fa/verify', {
            method: 'POST',
            body: JSON.stringify({ token })
        });
        
        if (response.ok) {
            showNotification('Two-factor authentication enabled successfully', 'success');
            closeModal('2faSetupModal');
            await loadUserProfile();
        } else {
            showNotification('Invalid verification code', 'error');
        }
    } catch (error) {
        console.error('2FA verify error:', error);
        showNotification('An error occurred while verifying 2FA', 'error');
    }
}

// Show 2FA disable modal
async function show2FADisableModal() {
    const password = prompt('Enter your password:');
    if (!password) return;
    
    const token = prompt('Enter your 2FA code or backup code:');
    if (!token) return;
    
    try {
        const response = await makeAuthRequest('/api/user/2fa/disable', {
            method: 'POST',
            body: JSON.stringify({ password, token })
        });
        
        if (response.ok) {
            showNotification('Two-factor authentication disabled', 'success');
            await loadUserProfile();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to disable 2FA', 'error');
        }
    } catch (error) {
        console.error('2FA disable error:', error);
        showNotification('An error occurred while disabling 2FA', 'error');
    }
}

// Handle data export
async function handleDataExport() {
    const btn = document.getElementById('exportData');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
    btn.disabled = true;
    
    try {
        const response = await makeAuthRequest('/api/user/export-data', {
            method: 'POST'
        });
        
        if (response.ok) {
            // Download the file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bankcsv_export_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showNotification('Data exported successfully', 'success');
        } else {
            showNotification('Failed to export data', 'error');
        }
    } catch (error) {
        console.error('Export error:', error);
        showNotification('An error occurred while exporting data', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Handle account deletion
async function handleAccountDelete() {
    // Update the delete confirmation modal
    const modal = document.getElementById('deleteAccountModal');
    if (modal) {
        modal.style.display = 'block';
        
        // Setup confirmation input
        const confirmInput = document.getElementById('deleteConfirmation');
        const confirmBtn = document.getElementById('confirmDelete');
        
        confirmInput.addEventListener('input', (e) => {
            confirmBtn.disabled = e.target.value !== 'DELETE';
        });
        
        confirmBtn.addEventListener('click', async () => {
            const password = prompt('Enter your password to confirm account deletion:');
            if (!password) return;
            
            try {
                const response = await makeAuthRequest('/api/user/account', {
                    method: 'DELETE',
                    body: JSON.stringify({ password })
                });
                
                if (response.ok) {
                    showNotification('Account deletion confirmation sent to your email', 'info');
                    closeModal('deleteAccountModal');
                } else {
                    const error = await response.json();
                    showNotification(error.detail || 'Failed to delete account', 'error');
                }
            } catch (error) {
                console.error('Account deletion error:', error);
                showNotification('An error occurred while deleting account', 'error');
            }
        });
    }
}

// Handle add payment method
async function handleAddPaymentMethod() {
    try {
        const response = await makeAuthRequest('/api/stripe/customer-portal', {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            window.location.href = data.url;
        } else {
            showNotification('Failed to open payment portal', 'error');
        }
    } catch (error) {
        console.error('Payment portal error:', error);
        showNotification('An error occurred while opening payment portal', 'error');
    }
}

// Load preferences
async function loadPreferences() {
    // Load from localStorage for now
    const saved = localStorage.getItem('conversion_preferences');
    if (saved) {
        try {
            const prefs = JSON.parse(saved);
            setValue('defaultFormat', prefs.default_format || 'csv');
            setValue('dateFormat', prefs.date_format || 'MM/DD/YYYY');
            setValue('autoDownload', prefs.auto_download);
            setValue('saveHistory', prefs.save_history);
            setValue('analytics', prefs.analytics);
        } catch (error) {
            console.error('Failed to load preferences:', error);
        }
    }
}

// Load login history
async function loadLoginHistory() {
    const historyContainer = document.getElementById('loginHistory');
    if (!historyContainer) return;
    
    try {
        const response = await makeAuthRequest('/api/user/sessions?limit=5');
        if (response.ok) {
            const data = await response.json();
            
            if (data.sessions && data.sessions.length > 0) {
                historyContainer.innerHTML = data.sessions.map(session => {
                    const deviceIcon = session.device_type === 'mobile' ? 'fa-mobile-alt' : 
                                     session.device_type === 'tablet' ? 'fa-tablet-alt' : 'fa-desktop';
                    
                    const loginTime = new Date(session.created_at);
                    const timeAgo = getTimeAgo(loginTime);
                    
                    return `
                        <div class="login-item ${session.is_current ? 'current-session' : ''}">
                            <div class="login-info">
                                <div class="login-location">
                                    <i class="fas fa-map-marker-alt"></i>
                                    <span>${session.location || session.ip_address}</span>
                                </div>
                                <div class="login-details">
                                    <span class="login-browser">${session.browser} on ${session.os}</span>
                                    <span class="login-time">
                                        <i class="fas fa-clock"></i>
                                        ${session.is_active ? (session.is_current ? 'Active now' : 'Active ' + timeAgo) : 'Logged out ' + timeAgo}
                                    </span>
                                </div>
                            </div>
                            <div class="login-device">
                                <i class="fas ${deviceIcon}"></i>
                                ${session.is_current ? '<span class="current-badge">Current</span>' : ''}
                                ${session.is_active && !session.is_current ? 
                                    `<button class="btn-terminate" onclick="terminateSession('${session.session_id}')">
                                        <i class="fas fa-times"></i>
                                    </button>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
                
                // Add terminate all button if multiple active sessions
                if (data.active_sessions > 1) {
                    historyContainer.innerHTML += `
                        <div class="login-actions">
                            <button class="btn btn-secondary btn-sm" onclick="terminateAllSessions()">
                                <i class="fas fa-sign-out-alt"></i> Sign out all other sessions
                            </button>
                        </div>
                    `;
                }
            } else {
                historyContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-history"></i>
                        <p>No login history available</p>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Failed to load login history:', error);
        // Show fallback
        historyContainer.innerHTML = `
            <div class="login-item">
                <div class="login-info">
                    <div class="login-location">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>Current Session</span>
                    </div>
                    <div class="login-time">
                        <i class="fas fa-clock"></i>
                        <span>Active now</span>
                    </div>
                </div>
                <div class="login-device">
                    <i class="fas fa-desktop"></i>
                    <span>${navigator.userAgent.includes('Mobile') ? 'Mobile' : 'Desktop'}</span>
                </div>
            </div>
        `;
    }
}

// Get time ago string
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' minutes ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + ' days ago';
    
    return date.toLocaleDateString();
}

// Terminate a session
window.terminateSession = async function(sessionId) {
    if (!confirm('Are you sure you want to end this session?')) return;
    
    try {
        const response = await makeAuthRequest(`/api/user/sessions/${sessionId}/terminate`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('Session terminated', 'success');
            await loadLoginHistory();
        } else {
            showNotification('Failed to terminate session', 'error');
        }
    } catch (error) {
        console.error('Terminate session error:', error);
        showNotification('An error occurred', 'error');
    }
}

// Terminate all other sessions
window.terminateAllSessions = async function() {
    if (!confirm('Are you sure you want to sign out all other sessions?')) return;
    
    try {
        const response = await makeAuthRequest('/api/user/sessions/terminate-all', {
            method: 'POST',
            body: JSON.stringify({ except_current: true })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(result.message, 'success');
            await loadLoginHistory();
        } else {
            showNotification('Failed to terminate sessions', 'error');
        }
    } catch (error) {
        console.error('Terminate all sessions error:', error);
        showNotification('An error occurred', 'error');
    }
}

// Update plan display
function updatePlanDisplay(profile) {
    const planName = document.getElementById('currentPlanName');
    const planDetails = document.getElementById('currentPlanDetails');
    
    if (planName) {
        const plans = {
            'free': 'Free Plan',
            'starter': 'Starter Plan',
            'professional': 'Professional Plan',
            'business': 'Business Plan'
        };
        planName.textContent = plans[profile.account_type] || 'Free Plan';
    }
    
    if (planDetails) {
        const limits = {
            'free': '5 conversions per day',
            'starter': '50 conversions per day',
            'professional': '500 conversions per day',
            'business': 'Unlimited conversions'
        };
        planDetails.textContent = limits[profile.account_type] || '5 conversions per day';
    }
}

// Update usage display
function updateUsageDisplay(account) {
    const usageEl = document.getElementById('monthlyUsage');
    const progressEl = document.getElementById('usageProgress');
    
    if (usageEl) {
        const used = account.daily_generations || 0;
        const limit = account.daily_limit || 5;
        usageEl.textContent = `${used} / ${limit}`;
        
        if (progressEl) {
            const percentage = Math.min(100, (used / limit) * 100);
            progressEl.style.width = `${percentage}%`;
            
            // Add color based on usage
            if (percentage >= 90) {
                progressEl.classList.add('danger');
            } else if (percentage >= 70) {
                progressEl.classList.add('warning');
            }
        }
    }
}

// Update subscription display
function updateSubscriptionDisplay(subscription) {
    // Update billing history section if subscription exists
    const billingHistory = document.getElementById('billingHistory');
    if (billingHistory && subscription) {
        billingHistory.innerHTML = `
            <div class="billing-item">
                <div class="billing-info">
                    <span class="billing-plan">${subscription.plan}</span>
                    <span class="billing-status ${subscription.status}">${subscription.status}</span>
                </div>
                <div class="billing-date">
                    Expires: ${new Date(subscription.expires_at).toLocaleDateString()}
                </div>
            </div>
        `;
    }
}

// Update password strength indicator
function updatePasswordStrength(e) {
    const password = e.target.value;
    const strengthBar = document.querySelector('.strength-bar');
    if (!strengthBar) return;
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    const percentage = (strength / 5) * 100;
    strengthBar.style.width = `${percentage}%`;
    
    // Update color
    strengthBar.className = 'strength-bar';
    if (strength >= 4) {
        strengthBar.classList.add('strong');
    } else if (strength >= 2) {
        strengthBar.classList.add('medium');
    } else {
        strengthBar.classList.add('weak');
    }
}

// Modal handlers
function setupModalHandlers() {
    // Close modal on background click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
}

// Close modal
window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Make authenticated request
async function makeAuthRequest(url, options = {}) {
    // Try cookie auth first
    const cookieOptions = {
        ...options,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken || '',
            ...(options.headers || {})
        }
    };
    
    try {
        const response = await fetch(url, cookieOptions);
        if (response.ok || response.status !== 401) {
            return response;
        }
    } catch (error) {
        console.error('Cookie auth request failed:', error);
    }
    
    // Fallback to JWT auth
    const token = localStorage.getItem('access_token');
    if (token) {
        const jwtOptions = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                ...(options.headers || {})
            }
        };
        
        return fetch(url, jwtOptions);
    }
    
    // Return failed response
    return new Response(null, { status: 401 });
}

// Helper functions
function getValue(id, isCheckbox = false) {
    const element = document.getElementById(id);
    if (!element) return isCheckbox ? false : '';
    return isCheckbox ? element.checked : element.value;
}

function setValue(id, value, isCheckbox = false) {
    const element = document.getElementById(id);
    if (!element) return;
    if (isCheckbox) {
        element.checked = value;
    } else {
        element.value = value || '';
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Add CSS for notifications and modals
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
    z-index: 10000;
    display: flex;
    align-items: center;
    gap: 12px;
    max-width: 400px;
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

.notification i {
    font-size: 20px;
}

/* Modal styles */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-content {
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    max-width: 90%;
    max-height: 90vh;
    overflow: auto;
    animation: modalSlideIn 0.3s ease;
}

@keyframes modalSlideIn {
    from {
        transform: translateY(-50px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

.modal-header {
    padding: 20px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-body {
    padding: 20px;
}

.modal-footer {
    padding: 20px;
    border-top: 1px solid #e5e7eb;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
}

.modal-close {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #6b7280;
}

.modal-close:hover {
    color: #374151;
}

/* Password strength */
.password-strength {
    margin-top: 8px;
    height: 4px;
    background: #e5e7eb;
    border-radius: 2px;
    overflow: hidden;
}

.strength-bar {
    height: 100%;
    width: 0;
    transition: width 0.3s ease;
    background: #ef4444;
}

.strength-bar.weak {
    background: #ef4444;
}

.strength-bar.medium {
    background: #f59e0b;
}

.strength-bar.strong {
    background: #10b981;
}

/* 2FA styles */
.twofa-setup-steps {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.setup-step {
    display: flex;
    gap: 16px;
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
}

.step-number {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    background: #3b82f6;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

.step-content {
    flex: 1;
}

.step-content h4 {
    margin: 0 0 8px 0;
    color: #111827;
}

.setup-options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-top: 16px;
}

.option-qr,
.option-manual {
    padding: 16px;
    background: white;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
}

.qr-container {
    text-align: center;
    margin-top: 12px;
}

.qr-container img {
    max-width: 180px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}

.manual-entry {
    margin-top: 12px;
}

.manual-entry label {
    display: block;
    font-size: 12px;
    color: #6b7280;
    margin-top: 8px;
}

.manual-entry code {
    display: block;
    padding: 8px;
    background: #f3f4f6;
    border-radius: 4px;
    font-family: monospace;
    margin-bottom: 8px;
}

.secret-key {
    font-size: 16px;
    letter-spacing: 2px;
}

.btn-copy {
    background: none;
    border: 1px solid #d1d5db;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-copy:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
}

.backup-codes {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin: 16px 0;
    padding: 16px;
    background: white;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
}

.backup-codes code {
    padding: 8px 12px;
    background: #f3f4f6;
    border-radius: 4px;
    font-family: monospace;
    font-size: 14px;
    text-align: center;
}

.verify-input {
    margin-top: 12px;
}

.code-input {
    font-size: 24px;
    letter-spacing: 8px;
    text-align: center;
    font-family: monospace;
    padding: 12px;
}

.code-timer {
    margin-top: 8px;
    text-align: center;
    font-size: 14px;
    color: #6b7280;
}

/* Login history */
.login-item {
    padding: 16px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    transition: all 0.2s ease;
}

.login-item:hover {
    border-color: #d1d5db;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.login-item.current-session {
    border-color: #3b82f6;
    background: #eff6ff;
}

.login-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.login-location {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
    color: #111827;
}

.login-details {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.login-browser {
    font-size: 14px;
    color: #6b7280;
}

.login-time {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #9ca3af;
}

.login-device {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #374151;
}

.current-badge {
    padding: 2px 8px;
    background: #3b82f6;
    color: white;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
}

.btn-terminate {
    background: none;
    border: none;
    color: #ef4444;
    cursor: pointer;
    padding: 6px;
    border-radius: 4px;
    transition: all 0.2s ease;
}

.btn-terminate:hover {
    background: #fee2e2;
}

.login-actions {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #e5e7eb;
    text-align: center;
}

.empty-state {
    text-align: center;
    padding: 32px;
    color: #6b7280;
}

.empty-state i {
    font-size: 48px;
    color: #d1d5db;
    margin-bottom: 12px;
}

/* Usage progress */
.usage-progress {
    margin-top: 8px;
}

.progress-bar {
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: #3b82f6;
    transition: width 0.3s ease;
}

.progress-fill.warning {
    background: #f59e0b;
}

.progress-fill.danger {
    background: #ef4444;
}

/* Billing history */
.billing-item {
    padding: 16px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 12px;
}

.billing-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.billing-status {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}

.billing-status.active {
    background: #d1fae5;
    color: #065f46;
}

.billing-status.canceled {
    background: #fee2e2;
    color: #991b1b;
}

.billing-date {
    font-size: 14px;
    color: #6b7280;
}

/* 2FA status */
#2faStatus.enabled {
    color: #10b981;
    font-weight: 600;
}
`;
document.head.appendChild(style);