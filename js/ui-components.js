// UI Components for Bank Statement Converter
// Handles all authentication and user interface components

// Authentication Modal Component
const AuthModal = {
    init() {
        this.createModalHTML();
        this.attachEventListeners();
        this.updateNavigationUI();
    },

    createModalHTML() {
        // Create modal container
        const modalHTML = `
            <div id="authModal" class="modal auth-modal">
                <div class="modal-content">
                    <span class="close-modal">&times;</span>
                    
                    <div class="auth-container">
                        <!-- Login Form -->
                        <div id="loginFormContainer" class="auth-form-container active">
                            <h2 class="auth-title">Welcome Back</h2>
                            <p class="auth-subtitle">Sign in to access your saved statements</p>
                            
                            <form id="loginForm" class="auth-form">
                                <div class="form-group">
                                    <label for="loginEmail">Email</label>
                                    <input type="email" id="loginEmail" name="email" required 
                                           placeholder="Enter your email" class="form-input">
                                </div>
                                
                                <div class="form-group">
                                    <label for="loginPassword">Password</label>
                                    <input type="password" id="loginPassword" name="password" required 
                                           placeholder="Enter your password" class="form-input">
                                </div>
                                
                                <button type="submit" class="btn btn-primary btn-block">
                                    <span class="btn-text">Sign In</span>
                                    <span class="btn-loader" style="display: none;">
                                        <i class="fas fa-spinner fa-spin"></i>
                                    </span>
                                </button>
                                
                                <div class="auth-switch">
                                    <p>Don't have an account? 
                                        <a href="#" id="switchToRegister">Sign up</a>
                                    </p>
                                </div>
                            </form>
                        </div>
                        
                        <!-- Register Form -->
                        <div id="registerFormContainer" class="auth-form-container">
                            <h2 class="auth-title">Create Account</h2>
                            <p class="auth-subtitle">Get 5 free conversions every day</p>
                            
                            <form id="registerForm" class="auth-form">
                                <div class="form-group">
                                    <label for="registerEmail">Email</label>
                                    <input type="email" id="registerEmail" name="email" required 
                                           placeholder="Enter your email" class="form-input">
                                </div>
                                
                                <div class="form-group">
                                    <label for="registerPassword">Password</label>
                                    <input type="password" id="registerPassword" name="password" required 
                                           placeholder="Create a password" class="form-input">
                                    <small class="form-hint">At least 8 characters</small>
                                </div>
                                
                                <div class="form-group">
                                    <label for="confirmPassword">Confirm Password</label>
                                    <input type="password" id="confirmPassword" name="confirmPassword" required 
                                           placeholder="Confirm your password" class="form-input">
                                </div>
                                
                                <button type="submit" class="btn btn-primary btn-block">
                                    <span class="btn-text">Create Account</span>
                                    <span class="btn-loader" style="display: none;">
                                        <i class="fas fa-spinner fa-spin"></i>
                                    </span>
                                </button>
                                
                                <div class="auth-benefits">
                                    <div class="benefit-item">
                                        <i class="fas fa-check-circle"></i>
                                        <span>5 free conversions daily</span>
                                    </div>
                                    <div class="benefit-item">
                                        <i class="fas fa-check-circle"></i>
                                        <span>Save statements for 1 hour</span>
                                    </div>
                                    <div class="benefit-item">
                                        <i class="fas fa-check-circle"></i>
                                        <span>Priority support</span>
                                    </div>
                                </div>
                                
                                <div class="auth-switch">
                                    <p>Already have an account? 
                                        <a href="#" id="switchToLogin">Sign in</a>
                                    </p>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    },

    attachEventListeners() {
        // Modal close button
        const closeBtn = document.querySelector('#authModal .close-modal');
        closeBtn.addEventListener('click', () => this.closeModal());

        // Click outside modal to close
        const modal = document.getElementById('authModal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeModal();
        });

        // Switch between login and register
        document.getElementById('switchToRegister').addEventListener('click', (e) => {
            e.preventDefault();
            this.showRegisterForm();
        });

        document.getElementById('switchToLogin').addEventListener('click', (e) => {
            e.preventDefault();
            this.showLoginForm();
        });

        // Form submissions
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin(e);
        });

        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister(e);
        });
    },

    showModal(formType = 'login') {
        const modal = document.getElementById('authModal');
        modal.style.display = 'flex';
        
        if (formType === 'register') {
            this.showRegisterForm();
        } else {
            this.showLoginForm();
        }
    },

    closeModal() {
        const modal = document.getElementById('authModal');
        modal.style.display = 'none';
        this.clearErrors();
    },

    showLoginForm() {
        document.getElementById('loginFormContainer').classList.add('active');
        document.getElementById('registerFormContainer').classList.remove('active');
    },

    showRegisterForm() {
        document.getElementById('registerFormContainer').classList.add('active');
        document.getElementById('loginFormContainer').classList.remove('active');
    },

    async handleLogin(e) {
        const form = e.target;
        const email = form.email.value;
        const password = form.password.value;
        
        this.setLoading(form, true);
        this.clearErrors();

        try {
            await window.BankAuth.AuthAPI.login(email, password);
            this.closeModal();
            this.updateNavigationUI();
            UINotification.show('Successfully logged in!', 'success');
            
            // Refresh page if on dashboard
            if (window.location.pathname === '/dashboard') {
                window.location.reload();
            }
        } catch (error) {
            this.showError(form, error.message);
        } finally {
            this.setLoading(form, false);
        }
    },

    async handleRegister(e) {
        const form = e.target;
        const email = form.email.value;
        const password = form.password.value;
        const confirmPassword = form.confirmPassword.value;
        
        if (password !== confirmPassword) {
            this.showError(form, 'Passwords do not match');
            return;
        }

        if (password.length < 8) {
            this.showError(form, 'Password must be at least 8 characters');
            return;
        }
        
        this.setLoading(form, true);
        this.clearErrors();

        try {
            await window.BankAuth.AuthAPI.register(email, password);
            this.closeModal();
            this.updateNavigationUI();
            UINotification.show('Account created successfully! You have 5 free conversions.', 'success');
        } catch (error) {
            this.showError(form, error.message);
        } finally {
            this.setLoading(form, false);
        }
    },

    setLoading(form, isLoading) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        
        if (isLoading) {
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
        } else {
            submitBtn.disabled = false;
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
        }
    },

    showError(form, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.textContent = message;
        
        const existingError = form.querySelector('.form-error');
        if (existingError) {
            existingError.remove();
        }
        
        form.insertBefore(errorDiv, form.firstChild);
    },

    clearErrors() {
        const errors = document.querySelectorAll('.form-error');
        errors.forEach(error => error.remove());
    },

    updateNavigationUI() {
        const navAuth = document.querySelector('.nav-auth');
        if (!navAuth) return;

        if (window.BankAuth.TokenManager.isAuthenticated()) {
            const user = window.BankAuth.UserManager.getUser();
            navAuth.innerHTML = `
                <div class="nav-user-menu">
                    <button class="nav-user-toggle">
                        <i class="fas fa-user-circle"></i>
                        <span>${user?.email || 'Account'}</span>
                        <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="nav-user-dropdown">
                        <a href="/dashboard" class="dropdown-item">
                            <i class="fas fa-tachometer-alt"></i>
                            My Dashboard
                        </a>
                        <div class="dropdown-divider"></div>
                        <button class="dropdown-item" onclick="AuthModal.handleLogout()">
                            <i class="fas fa-sign-out-alt"></i>
                            Logout
                        </button>
                    </div>
                </div>
            `;
            
            // Add dropdown toggle
            const toggle = navAuth.querySelector('.nav-user-toggle');
            const dropdown = navAuth.querySelector('.nav-user-dropdown');
            toggle.addEventListener('click', () => {
                dropdown.classList.toggle('show');
            });
            
            // Close dropdown on outside click
            document.addEventListener('click', (e) => {
                if (!navAuth.contains(e.target)) {
                    dropdown.classList.remove('show');
                }
            });
        } else {
            navAuth.innerHTML = `
                <button class="btn btn-outline" onclick="AuthModal.showModal('login')">
                    <i class="fas fa-sign-in-alt"></i>
                    Login
                </button>
                <button class="btn btn-primary" onclick="AuthModal.showModal('register')">
                    <i class="fas fa-user-plus"></i>
                    Sign Up
                </button>
            `;
        }
    },

    async handleLogout() {
        try {
            await window.BankAuth.AuthAPI.logout();
            UINotification.show('Successfully logged out', 'success');
        } catch (error) {
            console.error('Logout error:', error);
        }
    }
};

// Feedback Component
const FeedbackComponent = {
    show(statementId) {
        const feedbackHTML = `
            <div id="feedbackPrompt" class="feedback-prompt">
                <div class="feedback-content">
                    <button class="feedback-close">&times;</button>
                    
                    <div class="feedback-header">
                        <i class="fas fa-star feedback-icon"></i>
                        <h3>How was your experience?</h3>
                        <p class="feedback-incentive">
                            ${!window.BankAuth.TokenManager.isAuthenticated() ? 
                                'Rate your experience and get <strong>2 extra conversions</strong> today!' : 
                                'Help us improve by rating your experience'}
                        </p>
                    </div>
                    
                    <div class="feedback-stars" id="feedbackStars">
                        <button class="star" data-rating="1"><i class="fas fa-star"></i></button>
                        <button class="star" data-rating="2"><i class="fas fa-star"></i></button>
                        <button class="star" data-rating="3"><i class="fas fa-star"></i></button>
                        <button class="star" data-rating="4"><i class="fas fa-star"></i></button>
                        <button class="star" data-rating="5"><i class="fas fa-star"></i></button>
                    </div>
                    
                    <div class="feedback-comment" style="display: none;">
                        <textarea id="feedbackComment" placeholder="Tell us more (optional)" 
                                  class="form-textarea"></textarea>
                    </div>
                    
                    <button id="submitFeedback" class="btn btn-primary btn-block" style="display: none;">
                        Submit Feedback
                    </button>
                </div>
            </div>
        `;

        // Add to page
        document.body.insertAdjacentHTML('beforeend', feedbackHTML);
        
        // Attach events
        this.attachEvents(statementId);
        
        // Show with animation
        setTimeout(() => {
            document.getElementById('feedbackPrompt').classList.add('show');
        }, 100);
    },

    attachEvents(statementId) {
        const prompt = document.getElementById('feedbackPrompt');
        const stars = prompt.querySelectorAll('.star');
        const submitBtn = document.getElementById('submitFeedback');
        const closeBtn = prompt.querySelector('.feedback-close');
        const commentArea = prompt.querySelector('.feedback-comment');
        
        let selectedRating = 0;

        // Star selection
        stars.forEach(star => {
            star.addEventListener('click', () => {
                selectedRating = parseInt(star.dataset.rating);
                this.updateStars(selectedRating);
                commentArea.style.display = 'block';
                submitBtn.style.display = 'block';
            });
            
            star.addEventListener('mouseenter', () => {
                this.updateStars(parseInt(star.dataset.rating), true);
            });
        });

        prompt.querySelector('.feedback-stars').addEventListener('mouseleave', () => {
            this.updateStars(selectedRating);
        });

        // Submit feedback
        submitBtn.addEventListener('click', async () => {
            const comment = document.getElementById('feedbackComment').value;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

            try {
                const result = await window.BankAuth.FeedbackAPI.submitFeedback(
                    statementId, 
                    selectedRating, 
                    comment
                );
                
                this.close();
                
                if (result.bonus_conversions) {
                    UINotification.show(
                        `Thank you! You've earned ${result.bonus_conversions} extra conversions today!`, 
                        'success'
                    );
                } else {
                    UINotification.show('Thank you for your feedback!', 'success');
                }
            } catch (error) {
                UINotification.show('Failed to submit feedback. Please try again.', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Submit Feedback';
            }
        });

        // Close button
        closeBtn.addEventListener('click', () => this.close());
    },

    updateStars(rating, hover = false) {
        const stars = document.querySelectorAll('.star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add(hover ? 'hover' : 'selected');
            } else {
                star.classList.remove('selected', 'hover');
            }
        });
    },

    close() {
        const prompt = document.getElementById('feedbackPrompt');
        if (prompt) {
            prompt.classList.remove('show');
            setTimeout(() => prompt.remove(), 300);
        }
    }
};

// Notification Component
const UINotification = {
    show(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `ui-notification ${type}`;
        
        const icon = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        }[type];
        
        notification.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.classList.add('show'), 10);
        
        // Auto remove
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
};

// Upload Limit Component
const UploadLimitUI = {
    async checkAndShow() {
        try {
            const limitData = await window.BankAuth.StatementAPI.checkLimit();
            
            if (!window.BankAuth.TokenManager.isAuthenticated() && limitData.conversions_used >= limitData.daily_limit) {
                this.showLimitReached();
                return false;
            }
            
            this.updateLimitDisplay(limitData);
            return true;
        } catch (error) {
            console.error('Failed to check limit:', error);
            return true; // Allow upload on error
        }
    },

    updateLimitDisplay(limitData) {
        const limitDisplay = document.getElementById('conversionLimit');
        if (!limitDisplay) return;

        const remaining = limitData.daily_limit - limitData.conversions_used;
        const isAuthenticated = window.BankAuth.TokenManager.isAuthenticated();

        limitDisplay.innerHTML = `
            <div class="limit-info">
                <i class="fas fa-info-circle"></i>
                <span>${remaining} conversion${remaining !== 1 ? 's' : ''} remaining today</span>
                ${!isAuthenticated ? `
                    <a href="#" onclick="AuthModal.showModal('register'); return false;">
                        Sign up for more
                    </a>
                ` : ''}
            </div>
        `;
    },

    showLimitReached() {
        const modal = document.createElement('div');
        modal.className = 'modal limit-modal';
        modal.innerHTML = `
            <div class="modal-content limit-content">
                <div class="limit-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h2>Daily Limit Reached</h2>
                <p>You've used all your free conversions for today.</p>
                
                <div class="limit-options">
                    <div class="option-card">
                        <h3>Free Account</h3>
                        <p>Get 5 conversions daily</p>
                        <button class="btn btn-primary" onclick="AuthModal.showModal('register'); this.closest('.modal').remove();">
                            Sign Up Free
                        </button>
                    </div>
                    
                    <div class="option-card premium">
                        <div class="premium-badge">Premium</div>
                        <h3>Unlimited Conversions</h3>
                        <p>Convert unlimited statements</p>
                        <button class="btn btn-secondary" onclick="alert('Premium coming soon!'); this.closest('.modal').remove();">
                            Coming Soon
                        </button>
                    </div>
                </div>
                
                <button class="modal-close" onclick="this.closest('.modal').remove();">
                    &times;
                </button>
            </div>
        `;
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('show'), 10);
    }
};

// Initialize UI components when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    AuthModal.init();
    
    // Make components globally accessible
    window.AuthModal = AuthModal;
    window.FeedbackComponent = FeedbackComponent;
    window.UINotification = UINotification;
    window.UploadLimitUI = UploadLimitUI;
});