// Modern Dashboard JavaScript - FIXED for cookie-based auth

document.addEventListener('DOMContentLoaded', async function() {
    // Wait for UnifiedAuth to initialize
    if (!window.UnifiedAuth) {
        console.error('UnifiedAuth not loaded!');
        window.location.href = '/login.html?redirect=dashboard-modern.html';
        return;
    }

    // Give auth time to initialize
    setTimeout(async () => {
        // Check authentication using UnifiedAuth
        if (!window.UnifiedAuth.isAuthenticated()) {
            console.log('Not authenticated, redirecting to login...');
            window.location.href = '/login.html?redirect=dashboard-modern.html';
            return;
        }

        // Initialize dashboard
        console.log('User authenticated, loading dashboard...');
        loadUserInfo();
        loadRecentConversions();
        setupEventListeners();
        updateUIForPlan();
    }, 500);
});

// Load user information
async function loadUserInfo() {
    try {
        // Get user from UnifiedAuth
        const user = window.UnifiedAuth.getUser();
        
        if (user) {
            // Update UI with user info
            document.getElementById('userEmail').textContent = user.email || 'Loading...';
            document.getElementById('userName').textContent = user.full_name || user.email;
            document.getElementById('accountType').textContent = user.account_type || 'free';
            document.getElementById('memberSince').textContent = formatDate(user.created_at);
            
            // Update stats
            document.getElementById('dailyConversions').textContent = user.daily_generations || 0;
            document.getElementById('remainingToday').textContent = user.daily_limit - (user.daily_generations || 0);
            document.getElementById('totalConversions').textContent = user.total_conversions || user.daily_generations || 0;
            
            // Store for other functions
            window.currentUser = user;
        } else {
            // Try to get fresh user data
            const response = await window.UnifiedAuth.makeAuthenticatedRequest('/v2/api/auth/check');
            if (response.ok) {
                const data = await response.json();
                if (data.authenticated && data.user) {
                    window.currentUser = data.user;
                    loadUserInfo(); // Recursive call with fresh data
                }
            }
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
        document.getElementById('dailyLimit').textContent = 'Unlimited';
        document.getElementById('remainingToday').textContent = 'Unlimited';
    }
}

// Utility function to format dates
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Handle logout
document.addEventListener('click', (e) => {
    if (e.target.matches('.logout-btn, a[href="/logout"]')) {
        e.preventDefault();
        if (window.UnifiedAuth) {
            window.UnifiedAuth.logout();
        }
    }
});