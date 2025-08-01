// Modern Dashboard JavaScript - FINAL FIX

// Wait for auth to be ready before doing anything
let authCheckInterval;
let authCheckCount = 0;

function initDashboard() {
    console.log('Initializing dashboard...');
    loadUserInfo();
    loadRecentConversions();
    setupEventListeners();
    updateUIForPlan();
}

// Check auth status
function checkAuthStatus() {
    authCheckCount++;
    
    // Don't check forever
    if (authCheckCount > 50) { // 5 seconds
        clearInterval(authCheckInterval);
        console.error('Auth check timeout');
        window.location.href = '/login.html?redirect=dashboard-modern.html';
        return;
    }
    
    if (!window.UnifiedAuth) {
        console.log('Waiting for UnifiedAuth...');
        return;
    }
    
    if (!window.UnifiedAuth.initialized) {
        console.log('Waiting for UnifiedAuth initialization...');
        return;
    }
    
    // Auth is ready, check if authenticated
    clearInterval(authCheckInterval);
    
    if (window.UnifiedAuth.isAuthenticated()) {
        console.log('User authenticated!');
        initDashboard();
    } else {
        console.log('User not authenticated, redirecting to login...');
        window.location.href = '/login.html?redirect=dashboard-modern.html';
    }
}

// Start checking when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded, checking auth...');
    authCheckInterval = setInterval(checkAuthStatus, 100);
});

// Load user information
async function loadUserInfo() {
    try {
        const user = window.UnifiedAuth.getUser();
        
        if (user) {
            // Update UI with user info
            const emailEl = document.getElementById('userEmail');
            const nameEl = document.getElementById('userName');
            const typeEl = document.getElementById('accountType');
            const sinceEl = document.getElementById('memberSince');
            
            if (emailEl) emailEl.textContent = user.email || 'Loading...';
            if (nameEl) nameEl.textContent = user.full_name || user.email;
            if (typeEl) typeEl.textContent = user.account_type || 'free';
            if (sinceEl) sinceEl.textContent = formatDate(user.created_at);
            
            // Update stats
            const dailyEl = document.getElementById('dailyConversions');
            const remainingEl = document.getElementById('remainingToday');
            const totalEl = document.getElementById('totalConversions');
            
            if (dailyEl) dailyEl.textContent = user.daily_generations || 0;
            if (remainingEl) remainingEl.textContent = (user.daily_limit || 10) - (user.daily_generations || 0);
            if (totalEl) totalEl.textContent = user.total_conversions || user.daily_generations || 0;
            
            window.currentUser = user;
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

// Load recent conversions
async function loadRecentConversions() {
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest('/v2/api/statements/recent');
        
        if (response.ok) {
            const conversions = await response.json();
            displayRecentConversions(conversions);
        }
    } catch (error) {
        console.error('Error loading conversions:', error);
        // Show empty state
        const container = document.getElementById('recentConversions');
        if (container) {
            container.innerHTML = '<p class="no-data">Unable to load conversions</p>';
        }
    }
}

// Display recent conversions
function displayRecentConversions(conversions) {
    const container = document.getElementById('recentConversions');
    if (!container) return;

    if (!conversions || conversions.length === 0) {
        container.innerHTML = '<p class="no-data">No conversions yet</p>';
        return;
    }

    const html = conversions.map(conv => `
        <div class="conversion-item">
            <div class="conversion-info">
                <h4>${conv.original_filename || 'Untitled'}</h4>
                <p>${formatDate(conv.created_at)} • ${conv.bank_name || 'Unknown Bank'}</p>
            </div>
            <div class="conversion-actions">
                <a href="${conv.csv_url}" class="btn-sm" download>
                    <i class="fas fa-download"></i> Download
                </a>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// Setup event listeners
function setupEventListeners() {
    // Convert new statement button
    const convertBtn = document.getElementById('convertNewBtn');
    if (convertBtn) {
        convertBtn.addEventListener('click', () => {
            window.location.href = '/convert-pdf.html';
        });
    }

    // Upgrade button
    const upgradeBtn = document.getElementById('upgradeBtn');
    if (upgradeBtn) {
        upgradeBtn.addEventListener('click', () => {
            window.location.href = '/pricing.html';
        });
    }
    
    // Logout buttons
    document.querySelectorAll('.logout-btn, a[href="/logout"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (window.UnifiedAuth) {
                window.UnifiedAuth.logout();
            }
        });
    });
}

// Update UI based on plan
function updateUIForPlan() {
    const user = window.currentUser;
    if (!user) return;

    const isPro = user.account_type === 'pro' || user.account_type === 'business';
    
    // Show/hide upgrade prompts
    const upgradeElements = document.querySelectorAll('.upgrade-prompt');
    upgradeElements.forEach(el => {
        el.style.display = isPro ? 'none' : 'block';
    });

    // Update limits display
    if (isPro) {
        const limitEl = document.getElementById('dailyLimit');
        const remainingEl = document.getElementById('remainingToday');
        if (limitEl) limitEl.textContent = 'Unlimited';
        if (remainingEl) remainingEl.textContent = 'Unlimited';
    }
}

// Utility function to format dates
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return 'N/A';
    }
}
