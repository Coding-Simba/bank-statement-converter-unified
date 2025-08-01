// Dashboard functionality for Bank Statement Converter

// Use v2 API endpoints to match UnifiedAuth
const API_BASE = (() => {
    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
    const base = isLocal ? 'http://localhost:5000' : `${window.location.protocol}//${hostname}`;
    return `${base}/v2/api`;
})();

document.addEventListener('DOMContentLoaded', async () => {
    // FIX: Wait for UnifiedAuth to initialize before checking authentication
    const waitForAuth = async () => {
        let attempts = 0;
        while (attempts < 50) { // Wait up to 5 seconds
            if (window.UnifiedAuth && window.UnifiedAuth.initialized) {
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
    };
    
    await waitForAuth();
    
    // Check authentication
    if (!window.UnifiedAuth || !window.UnifiedAuth.isAuthenticated()) {
        console.log('[Dashboard] Not authenticated, redirecting to login...');
        // Preserve the intended destination
        window.location.href = '/login.html?redirect=dashboard';
        return;
    }
    
    console.log('[Dashboard] User authenticated, loading dashboard...');
    
    // Initialize dashboard
    await loadUserProfile();
    await loadUsageStatistics();
    await loadRecentConversions();
    
    // Set up event listeners
    const upgradeBtn = document.getElementById('upgradeButton');
    if (upgradeBtn) {
        upgradeBtn.addEventListener('click', handleUpgrade);
    }
});

async function loadUserProfile() {
    try {
        const user = window.UnifiedAuth.getUser();
        
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
        const subscriptionResponse = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE}/stripe/subscription-status`, {
            method: 'GET'
        });
        
        if (subscriptionResponse.ok) {
            const subscription = await subscriptionResponse.json();
            
            // Update account type display
            const planName = subscription.plan.charAt(0).toUpperCase() + subscription.plan.slice(1);
            document.getElementById('accountType').textContent = planName;
            
            // Update account badge styling
            const accountBadge = document.getElementById('accountType');
            accountBadge.className = 'account-badge ' + subscription.plan;
            
            // Store subscription for other functions
            window.userSubscription = subscription;
        } else {
            // Default to free plan
            document.getElementById('accountType').textContent = 'Free';
            window.userSubscription = { plan: 'free' };
        }
        
    } catch (error) {
        console.error('Error loading user profile:', error);
    }
}

async function loadUsageStatistics() {
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE.replace('/v2/api', '/api')}/check-limit`);
        const limitData = await response.json();
        
        // Update conversion stats
        const usedToday = limitData.conversions_today || 0;
        const dailyLimit = limitData.daily_limit || 5;
        const monthlyUsed = limitData.monthly_conversions || 0;
        const monthlyLimit = limitData.monthly_limit || 'Unlimited';
        
        // Update daily stats
        document.getElementById('dailyUsed').textContent = usedToday;
        document.getElementById('dailyLimit').textContent = dailyLimit;
        document.getElementById('dailyPercentage').textContent = 
            Math.round((usedToday / dailyLimit) * 100) + '%';
        
        // Update daily progress bar
        const dailyProgress = document.getElementById('dailyProgress');
        const dailyPercentage = (usedToday / dailyLimit) * 100;
        dailyProgress.style.width = Math.min(dailyPercentage, 100) + '%';
        
        // Set progress bar color based on usage
        if (dailyPercentage >= 90) {
            dailyProgress.className = 'progress-fill danger';
        } else if (dailyPercentage >= 70) {
            dailyProgress.className = 'progress-fill warning';
        } else {
            dailyProgress.className = 'progress-fill';
        }
        
        // Update monthly stats (for paid plans)
        if (window.userSubscription && window.userSubscription.plan !== 'free') {
            document.getElementById('monthlyStats').style.display = 'block';
            document.getElementById('monthlyUsed').textContent = monthlyUsed;
            document.getElementById('monthlyLimit').textContent = monthlyLimit;
            
            if (monthlyLimit !== 'Unlimited') {
                const monthlyPercentage = (monthlyUsed / parseInt(monthlyLimit)) * 100;
                document.getElementById('monthlyPercentage').textContent = 
                    Math.round(monthlyPercentage) + '%';
                
                const monthlyProgress = document.getElementById('monthlyProgress');
                monthlyProgress.style.width = Math.min(monthlyPercentage, 100) + '%';
            }
        } else {
            document.getElementById('monthlyStats').style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error loading usage statistics:', error);
    }
}

async function loadRecentConversions() {
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE.replace('/v2/api', '/api')}/user/statements`);
        const statements = await response.json();
        
        const conversionsList = document.getElementById('conversionsList');
        conversionsList.innerHTML = '';
        
        if (!statements || statements.length === 0) {
            conversionsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <p>No recent conversions</p>
                    <p class="text-muted">Your converted files will appear here</p>
                </div>
            `;
            return;
        }
        
        // Display recent conversions
        statements.slice(0, 5).forEach(statement => {
            const item = document.createElement('div');
            item.className = 'conversion-item';
            
            const uploadDate = new Date(statement.created_at);
            const expiresAt = new Date(statement.expires_at);
            const now = new Date();
            const expired = expiresAt < now;
            
            item.innerHTML = `
                <div class="conversion-info">
                    <div class="conversion-name">
                        <i class="fas fa-file-csv"></i>
                        ${statement.original_filename || 'Converted File'}
                    </div>
                    <div class="conversion-date">
                        ${uploadDate.toLocaleDateString()} at ${uploadDate.toLocaleTimeString()}
                    </div>
                    ${expired ? 
                        '<div class="conversion-status expired">Expired</div>' : 
                        `<div class="conversion-status">Expires in ${getTimeRemaining(expiresAt)}</div>`
                    }
                </div>
                <div class="conversion-actions">
                    ${!expired ? 
                        `<button class="btn btn-sm btn-primary" onclick="downloadStatement('${statement.id}', '${statement.output_filename}')">
                            <i class="fas fa-download"></i> Download
                        </button>` : 
                        '<button class="btn btn-sm btn-secondary" disabled>Expired</button>'
                    }
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteStatement('${statement.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            conversionsList.appendChild(item);
        });
        
        // Add view all link if more than 5
        if (statements.length > 5) {
            const viewAllLink = document.createElement('div');
            viewAllLink.className = 'view-all-link';
            viewAllLink.innerHTML = '<a href="/conversions.html">View all conversions →</a>';
            conversionsList.appendChild(viewAllLink);
        }
        
    } catch (error) {
        console.error('Error loading recent conversions:', error);
        document.getElementById('conversionsList').innerHTML = `
            <div class="error-state">
                <p>Error loading conversions</p>
            </div>
        `;
    }
}

function getTimeRemaining(expiresAt) {
    const now = new Date();
    const diff = expiresAt - now;
    
    if (diff < 0) return 'Expired';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

async function downloadStatement(statementId, filename) {
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE.replace('/v2/api', '/api')}/statement/${statementId}/download`);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || 'statement.csv';
        a.click();
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error downloading statement:', error);
        alert('Error downloading file. Please try again.');
    }
}

async function deleteStatement(statementId) {
    if (!confirm('Are you sure you want to delete this conversion?')) {
        return;
    }
    
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE.replace('/v2/api', '/api')}/statements/${statementId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Reload the conversions list
            await loadRecentConversions();
        } else {
            alert('Error deleting conversion. Please try again.');
        }
    } catch (error) {
        console.error('Error deleting statement:', error);
        alert('Error deleting conversion. Please try again.');
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
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${API_BASE.replace('/v2/api', '/api')}/stripe/customer-portal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                return_url: '/dashboard.html'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            window.location.href = data.portal_url;
        } else {
            alert('Unable to open customer portal. Please try again.');
        }
    } catch (error) {
        console.error('Portal error:', error);
        alert('Unable to open customer portal. Please try again.');
    }
}

// Auto-refresh conversions every minute
setInterval(() => {
    if (document.visibilityState === 'visible') {
        loadRecentConversions();
    }
}, 60000);