// Dashboard functionality for Bank Statement Converter

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
        
        // Update account info
        document.getElementById('userEmail').textContent = user.email;
        document.getElementById('accountType').textContent = user.account_type || 'Free';
        
        // Format member since date
        const memberDate = new Date(user.created_at);
        document.getElementById('memberSince').textContent = memberDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        // Update account badge styling
        const accountBadge = document.getElementById('accountType');
        if (user.account_type === 'premium') {
            accountBadge.classList.add('premium');
        }
    } catch (error) {
        console.error('Failed to load user profile:', error);
        UINotification.show('Failed to load user profile', 'error');
    }
}

async function loadUsageStatistics() {
    try {
        const limitData = await window.BankAuth.StatementAPI.checkLimit();
        
        // Update statistics
        document.getElementById('todayConversions').textContent = limitData.conversions_used;
        document.getElementById('remainingConversions').textContent = 
            limitData.daily_limit - limitData.conversions_used;
        document.getElementById('totalConversions').textContent = limitData.total_conversions || 0;
        
        // Update progress bar
        const percentage = (limitData.conversions_used / limitData.daily_limit) * 100;
        document.getElementById('usagePercentage').textContent = `${Math.round(percentage)}%`;
        document.getElementById('usageProgressFill').style.width = `${percentage}%`;
        
        // Color code the progress bar
        const progressFill = document.getElementById('usageProgressFill');
        if (percentage >= 80) {
            progressFill.style.background = 'var(--danger)';
        } else if (percentage >= 60) {
            progressFill.style.background = 'var(--warning)';
        } else {
            progressFill.style.background = 'var(--gradient)';
        }
    } catch (error) {
        console.error('Failed to load usage statistics:', error);
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
    const modal = document.createElement('div');
    modal.className = 'modal upgrade-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
            
            <div class="upgrade-header">
                <i class="fas fa-crown upgrade-icon"></i>
                <h2>Upgrade to Premium</h2>
                <p>Get unlimited conversions and premium features</p>
            </div>
            
            <div class="pricing-comparison">
                <div class="plan-card current">
                    <h3>Free Plan</h3>
                    <div class="price">$0/month</div>
                    <ul class="features">
                        <li><i class="fas fa-check"></i> 5 conversions per day</li>
                        <li><i class="fas fa-check"></i> Files saved for 1 hour</li>
                        <li><i class="fas fa-check"></i> Basic support</li>
                        <li class="disabled"><i class="fas fa-times"></i> Batch processing</li>
                        <li class="disabled"><i class="fas fa-times"></i> API access</li>
                    </ul>
                    <button class="btn btn-outline" disabled>Current Plan</button>
                </div>
                
                <div class="plan-card premium">
                    <div class="badge">COMING SOON</div>
                    <h3>Premium Plan</h3>
                    <div class="price">$9.99/month</div>
                    <ul class="features">
                        <li><i class="fas fa-check"></i> Unlimited conversions</li>
                        <li><i class="fas fa-check"></i> Files saved for 30 days</li>
                        <li><i class="fas fa-check"></i> Priority support</li>
                        <li><i class="fas fa-check"></i> Batch processing</li>
                        <li><i class="fas fa-check"></i> API access</li>
                    </ul>
                    <button class="btn btn-primary" onclick="alert('Premium plan coming soon!')">
                        Coming Soon
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('show'), 10);
}

// Auto-refresh conversions every minute
setInterval(() => {
    loadRecentConversions();
}, 60000);