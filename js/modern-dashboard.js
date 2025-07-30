// Modern Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html?redirect=dashboard';
        return;
    }

    // Initialize dashboard
    loadUserInfo();
    loadStatistics();
    loadRecentConversions();
    setupEventListeners();
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
            
            // Update user email in navigation
            const userEmailElement = document.getElementById('userEmail');
            if (userEmailElement) {
                userEmailElement.textContent = user.email;
            }
            
            // Store user info
            window.currentUser = user;
        } else if (response.status === 401) {
            // Token expired
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login.html?redirect=dashboard';
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch('/api/user/statistics', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            const stats = await response.json();
            
            // Update statistics
            document.getElementById('todayConversions').textContent = stats.todayConversions || 0;
            document.getElementById('totalConversions').textContent = stats.totalConversions || 0;
            document.getElementById('remainingToday').textContent = stats.remainingToday || 5;
            
            // Update usage progress
            const usagePercentage = ((stats.todayConversions || 0) / 5) * 100;
            document.getElementById('usagePercentage').textContent = `${Math.round(usagePercentage)}%`;
            document.getElementById('usageProgressFill').style.width = `${usagePercentage}%`;
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
        // Set default values
        document.getElementById('todayConversions').textContent = '0';
        document.getElementById('totalConversions').textContent = '0';
        document.getElementById('remainingToday').textContent = '5';
    }
}

// Load recent conversions
async function loadRecentConversions() {
    const container = document.getElementById('conversionsContainer');
    
    try {
        const response = await fetch('/api/statements/recent?limit=10', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            const statements = await response.json();
            
            if (statements.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">
                            <i class="fas fa-file-alt"></i>
                        </div>
                        <h3>No recent conversions</h3>
                        <p>Your converted files will appear here</p>
                        <a href="/" class="btn-primary">
                            <i class="fas fa-file-upload"></i> Convert Your First Statement
                        </a>
                    </div>
                `;
            } else {
                container.innerHTML = statements.map(statement => createConversionItem(statement)).join('');
            }
        } else {
            throw new Error('Failed to load conversions');
        }
    } catch (error) {
        console.error('Error loading conversions:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3>Error loading conversions</h3>
                <p>Please try refreshing the page</p>
                <button onclick="location.reload()" class="btn-primary">
                    <i class="fas fa-sync"></i> Refresh
                </button>
            </div>
        `;
    }
}

// Create conversion item HTML
function createConversionItem(statement) {
    const date = new Date(statement.created_at);
    const timeAgo = getTimeAgo(date);
    const fileSize = formatFileSize(statement.file_size || 0);
    
    return `
        <div class="conversion-item">
            <div class="conversion-info">
                <div class="conversion-icon">
                    <i class="fas fa-file-pdf"></i>
                </div>
                <div class="conversion-details">
                    <h4>${escapeHtml(statement.original_filename || 'Untitled')}</h4>
                    <div class="conversion-meta">
                        <span><i class="fas fa-clock"></i> ${timeAgo}</span>
                        <span><i class="fas fa-building"></i> ${escapeHtml(statement.bank || 'Unknown Bank')}</span>
                        <span><i class="fas fa-file"></i> ${fileSize}</span>
                        ${statement.validated ? '<span class="validated-badge"><i class="fas fa-check-circle"></i> Validated</span>' : ''}
                    </div>
                </div>
            </div>
            <div class="conversion-actions">
                ${!statement.validated ? `
                    <button class="btn-icon" onclick="validateStatement(${statement.id})" title="Validate Transactions">
                        <i class="fas fa-check"></i>
                    </button>
                ` : ''}
                <a href="/api/statement/${statement.id}/download${statement.validated ? '?validated=true' : ''}" 
                   class="btn-icon" title="Download CSV">
                    <i class="fas fa-download"></i>
                </a>
                <button class="btn-icon" onclick="deleteStatement(${statement.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
}

// Validate statement
function validateStatement(statementId) {
    window.open(`/validation.html?id=${statementId}`, '_blank');
}

// Delete statement
async function deleteStatement(statementId) {
    if (!confirm('Are you sure you want to delete this conversion?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/statement/${statementId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            // Reload conversions
            loadRecentConversions();
            loadStatistics();
        } else {
            alert('Failed to delete conversion');
        }
    } catch (error) {
        console.error('Error deleting statement:', error);
        alert('Error deleting conversion');
    }
}

// Setup event listeners
function setupEventListeners() {
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
    
    // Mobile menu toggle
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');
        });
    }
}

// Logout function
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

// Utility functions
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
    
    return date.toLocaleDateString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Auto-refresh conversions every minute
setInterval(function() {
    loadRecentConversions();
    loadStatistics();
}, 60000);