// Dashboard functionality for Bank Statement Converter

// Get API base URL
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

const API_BASE = getApiBase() + '/api';

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (!window.BankAuth.TokenManager.isAuthenticated()) {
        window.location.href = '/';
        return;
    }

    // Initialize dashboard
    await loadUserProfile();
    await loadUsageStatistics();
    await loadRecentConversions();
    
    // Set up event listeners
    document.getElementById('upgradeButton').addEventListener('click', handleUpgrade);
});

async function loadUserProfile() {
    try {
        const user = await window.BankAuth.AuthAPI.getProfile();
        
        // Update basic info
        document.getElementById('userEmail').textContent = user.email;
        
        // Format member since date
        const memberDate = new Date(user.created_at);
        document.getElementById('memberSince').textContent = memberDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        // Load subscription status
        const subscriptionResponse = await fetch(`${API_BASE}/stripe/subscription-status`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${window.BankAuth.TokenManager.getAccessToken()}`
            }
        });
        
        if (subscriptionResponse.ok) {
            const subscription = await subscriptionResponse.json();
            
            // Update account type display
            const planName = subscription.plan.charAt(0).toUpperCase() + subscription.plan.slice(1);
            document.getElementById('accountType').textContent = planName;
            
            // Update account badge styling
            const accountBadge = document.getElementById('accountType');
            accountBadge.className = 'account-badge ' + subscription.plan;
            
            // Store subscription data for usage stats
            window.userSubscription = subscription;
        }
    } catch (error) {
        console.error('Failed to load user profile:', error);
        if (window.UINotification) {
            window.UINotification.show('Failed to load user profile', 'error');
        }
    }
}

async function loadUsageStatistics() {
    try {
        // If we have subscription data, use it
        if (window.userSubscription) {
            const subscription = window.userSubscription;
            const isMonthly = subscription.pages_limit && subscription.pages_limit > 10;
            
            if (isMonthly) {
                // Monthly plan - show monthly usage
                document.getElementById('todayConversions').textContent = subscription.pages_used;
                document.getElementById('remainingConversions').textContent = 
                    subscription.pages_limit - subscription.pages_used;
                
                // Update labels
                document.querySelector('.stat-item:nth-child(1) .stat-label').textContent = 'Monthly Usage';
                document.querySelector('.stat-item:nth-child(2) .stat-label').textContent = 'Remaining This Month';
                
                // Update progress bar
                const percentage = (subscription.pages_used / subscription.pages_limit) * 100;
                document.getElementById('usagePercentage').textContent = `${Math.round(percentage)}%`;
                document.getElementById('usageProgressFill').style.width = `${percentage}%`;
                
                // Update progress header
                document.querySelector('.progress-header span:first-child').textContent = 'Monthly Usage';
                
                // Show renewal date if available
                if (subscription.renewal_date) {
                    const renewalDate = new Date(subscription.renewal_date).toLocaleDateString();
                    const existingInfo = document.querySelector('.renewal-info');
                    if (!existingInfo) {
                        const progressSection = document.querySelector('.usage-progress');
                        const renewalInfo = document.createElement('div');
                        renewalInfo.className = 'renewal-info';
                        renewalInfo.style.cssText = 'margin-top: 1rem; font-size: 1.4rem; color: #6b7280;';
                        renewalInfo.textContent = `Resets on ${renewalDate}`;
                        progressSection.appendChild(renewalInfo);
                    }
                }
                
                // Color code the progress bar
                const progressFill = document.getElementById('usageProgressFill');
                if (percentage >= 90) {
                    progressFill.style.background = '#ef4444';
                } else if (percentage >= 75) {
                    progressFill.style.background = '#f59e0b';
                } else {
                    progressFill.style.background = '#0066ff';
                }
            } else {
                // Free plan - show daily usage
                await loadDailyUsage();
            }
            
            // Update total conversions
            document.getElementById('totalConversions').textContent = subscription.pages_used || '0';
        } else {
            // Fallback to API call
            await loadDailyUsage();
        }
    } catch (error) {
        console.error('Failed to load usage statistics:', error);
    }
}

async function loadDailyUsage() {
    const limitData = await window.BankAuth.StatementAPI.checkLimit();
    
    // Update statistics
    document.getElementById('todayConversions').textContent = limitData.daily_used;
    document.getElementById('remainingConversions').textContent = 
        limitData.daily_limit - limitData.daily_used;
    document.getElementById('totalConversions').textContent = limitData.monthly_used || limitData.daily_used;
    
    // Update progress bar
    const percentage = (limitData.daily_used / limitData.daily_limit) * 100;
    document.getElementById('usagePercentage').textContent = `${Math.round(percentage)}%`;
    document.getElementById('usageProgressFill').style.width = `${percentage}%`;
    
    // Color code the progress bar
    const progressFill = document.getElementById('usageProgressFill');
    if (percentage >= 80) {
        progressFill.style.background = '#ef4444';
    } else if (percentage >= 60) {
        progressFill.style.background = '#f59e0b';
    } else {
        progressFill.style.background = '#0066ff';
    }
}

async function loadRecentConversions() {
    const container = document.getElementById('conversionsContainer');
    
    try {
        const statements = await window.BankAuth.StatementAPI.getUserStatements();
        
        if (!statements || statements.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox empty-icon"></i>
                    <h3>No recent conversions</h3>
                    <p>Your converted statements will appear here</p>
                    <a href="/" class="btn btn-primary">
                        <i class="fas fa-file-upload"></i>
                        Convert Your First Statement
                    </a>
                </div>
            `;
            return;
        }
        
        // Create table
        const tableHTML = `
            <div class="conversions-table">
                <table>
                    <thead>
                        <tr>
                            <th>File Name</th>
                            <th>Bank</th>
                            <th>Converted</th>
                            <th>Expires</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${statements.map(stmt => createStatementRow(stmt)).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHTML;
        
        // Attach download handlers
        container.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', (e) => handleDownload(e.target.dataset.id));
        });
        
    } catch (error) {
        console.error('Failed to load recent conversions:', error);
        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-circle"></i>
                <p>Failed to load conversions. Please try again.</p>
            </div>
        `;
    }
}

function createStatementRow(statement) {
    const convertedDate = new Date(statement.created_at);
    const expiresDate = new Date(statement.expires_at);
    const now = new Date();
    
    // Calculate time until expiry
    const timeLeft = expiresDate - now;
    const minutesLeft = Math.floor(timeLeft / (1000 * 60));
    
    let expiryText = '';
    let expiryClass = '';
    
    if (minutesLeft <= 0) {
        expiryText = 'Expired';
        expiryClass = 'expired';
    } else if (minutesLeft < 10) {
        expiryText = `${minutesLeft} min`;
        expiryClass = 'expiring-soon';
    } else {
        expiryText = `${minutesLeft} min`;
        expiryClass = 'active';
    }
    
    return `
        <tr>
            <td>
                <div class="file-info">
                    <i class="fas fa-file-pdf file-icon"></i>
                    <span>${statement.original_filename}</span>
                </div>
            </td>
            <td>
                <span class="bank-badge">${statement.bank_name || 'Unknown'}</span>
            </td>
            <td>
                <span class="date-text">${convertedDate.toLocaleString()}</span>
            </td>
            <td>
                <span class="expiry-badge ${expiryClass}">${expiryText}</span>
            </td>
            <td>
                ${minutesLeft > 0 ? `
                    <button class="btn btn-sm btn-primary download-btn" data-id="${statement.id}">
                        <i class="fas fa-download"></i>
                        Download
                    </button>
                ` : `
                    <span class="text-muted">Expired</span>
                `}
            </td>
        </tr>
    `;
}

async function handleDownload(statementId) {
    try {
        await window.BankAuth.StatementAPI.downloadStatement(statementId);
        UINotification.show('Statement downloaded successfully', 'success');
    } catch (error) {
        console.error('Download failed:', error);
        UINotification.show('Failed to download statement', 'error');
    }
}

function handleUpgrade() {
    // Check if user has a subscription
    if (window.userSubscription && window.userSubscription.plan !== 'free') {
        // User has a paid plan - open customer portal
        openCustomerPortal();
    } else {
        // Redirect to pricing page
        window.location.href = '/pricing.html';
    }
}

async function openCustomerPortal() {
    try {
        const response = await fetch(`${API_BASE}/stripe/customer-portal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.BankAuth.TokenManager.getAccessToken()}`
            },
            body: JSON.stringify({
                return_url: '/dashboard.html'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            window.location.href = data.portal_url;
        } else {
            throw new Error('Failed to create portal session');
        }
    } catch (error) {
        console.error('Portal error:', error);
        alert('Failed to open subscription management. Please try again.');
    }
}

// Auto-refresh conversions every minute
setInterval(() => {
    loadRecentConversions();
}, 60000);