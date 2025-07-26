// Conversion Limit Modal Handler
(function() {
  'use strict';

  // Modal HTML template
  const modalHTML = `
    <div id="conversionLimitModal" class="conversion-modal-overlay">
      <div class="conversion-modal">
        <button class="modal-close" aria-label="Close modal">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
        
        <div class="modal-content">
          <div class="modal-icon">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="40" cy="40" r="38" stroke="#FCD34D" stroke-width="4"/>
              <path d="M40 20V45" stroke="#F59E0B" stroke-width="4" stroke-linecap="round"/>
              <circle cx="40" cy="55" r="3" fill="#F59E0B"/>
              <path d="M25 35L40 20L55 35" stroke="#F59E0B" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          
          <h2 class="modal-title">You've Reached Your Daily Limit!</h2>
          
          <div class="limit-info">
            <p class="limit-message" id="limitMessage">
              <!-- Dynamic message will be inserted here -->
            </p>
          </div>
          
          <div class="upgrade-section">
            <h3>Unlock More Conversions with Premium</h3>
            <p class="upgrade-subtitle">Choose a plan that fits your needs</p>
            
            <div class="plan-cards">
              <div class="plan-card">
                <h4>Starter</h4>
                <div class="plan-price">
                  <span class="currency">$</span>
                  <span class="amount">30</span>
                  <span class="period">/month</span>
                </div>
                <p class="plan-feature">400 pages/month</p>
                <a href="/pricing.html#starter" class="plan-cta">Choose Starter</a>
              </div>
              
              <div class="plan-card featured">
                <div class="popular-badge">Most Popular</div>
                <h4>Professional</h4>
                <div class="plan-price">
                  <span class="currency">$</span>
                  <span class="amount">60</span>
                  <span class="period">/month</span>
                </div>
                <p class="plan-feature">1000 pages/month</p>
                <a href="/pricing.html#professional" class="plan-cta primary">Choose Professional</a>
              </div>
              
              <div class="plan-card">
                <h4>Business</h4>
                <div class="plan-price">
                  <span class="currency">$</span>
                  <span class="amount">99</span>
                  <span class="period">/month</span>
                </div>
                <p class="plan-feature">4000 pages/month</p>
                <a href="/pricing.html#business" class="plan-cta">Choose Business</a>
              </div>
            </div>
            
            <div class="modal-footer">
              <p class="or-text">or</p>
              <a href="/signup.html" class="signup-link" id="signupLink">
                Sign up for free to get 5 daily conversions
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Modal CSS
  const modalCSS = `
    <style>
      .conversion-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(4px);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        padding: 2rem;
        animation: fadeIn 0.3s ease-out;
      }
      
      .conversion-modal-overlay.show {
        display: flex;
      }
      
      .conversion-modal {
        background: #ffffff;
        border-radius: 24px;
        max-width: 720px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        position: relative;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        animation: slideUp 0.4s ease-out;
      }
      
      .modal-close {
        position: absolute;
        top: 20px;
        right: 20px;
        background: none;
        border: none;
        cursor: pointer;
        padding: 8px;
        border-radius: 8px;
        transition: all 0.2s;
        color: #6b7280;
      }
      
      .modal-close:hover {
        background: #f3f4f6;
        color: #111827;
      }
      
      .modal-content {
        padding: 3.5rem 2.5rem 2.5rem;
        text-align: center;
      }
      
      .modal-icon {
        margin-bottom: 1.5rem;
        animation: bounce 0.6s ease-out;
        display: inline-block;
      }
      
      .modal-icon svg {
        width: 80px;
        height: 80px;
      }
      
      .modal-title {
        font-size: 2.25rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 1rem;
        line-height: 1.2;
      }
      
      .limit-info {
        background: #fef3c7;
        border: 1px solid #fcd34d;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 2.5rem;
      }
      
      .limit-message {
        font-size: 1.1rem;
        color: #92400e;
        margin: 0;
        font-weight: 500;
      }
      
      .upgrade-section h3 {
        font-size: 1.75rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.5rem;
      }
      
      .upgrade-subtitle {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
      }
      
      .plan-cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1.25rem;
        margin-bottom: 2rem;
      }
      
      .plan-card {
        background: #f9fafb;
        border: 2px solid #e5e7eb;
        border-radius: 16px;
        padding: 1.75rem 1.25rem;
        position: relative;
        transition: all 0.3s;
      }
      
      .plan-card:hover {
        border-color: #0066ff;
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0, 102, 255, 0.1);
      }
      
      .plan-card.featured {
        border-color: #0066ff;
        background: #e6f0ff;
      }
      
      .popular-badge {
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: #00d26a;
        color: white;
        padding: 0.25rem 1rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        white-space: nowrap;
      }
      
      .plan-card h4 {
        font-size: 1.25rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.75rem;
      }
      
      .plan-price {
        display: flex;
        align-items: baseline;
        justify-content: center;
        margin-bottom: 0.5rem;
      }
      
      .plan-price .currency {
        font-size: 1.25rem;
        color: #6b7280;
        margin-right: 0.25rem;
      }
      
      .plan-price .amount {
        font-size: 2.25rem;
        font-weight: 800;
        color: #111827;
      }
      
      .plan-price .period {
        font-size: 1rem;
        color: #6b7280;
        margin-left: 0.25rem;
      }
      
      .plan-feature {
        font-size: 0.95rem;
        color: #6b7280;
        margin-bottom: 1rem;
      }
      
      .plan-cta {
        display: block;
        width: 100%;
        padding: 0.75rem 1.5rem;
        background: #ffffff;
        color: #0066ff;
        border: 2px solid #e5e7eb;
        border-radius: 10px;
        font-weight: 600;
        text-decoration: none;
        transition: all 0.2s;
      }
      
      .plan-cta:hover {
        background: #f3f4f6;
        border-color: #0066ff;
      }
      
      .plan-cta.primary {
        background: #0066ff;
        color: white;
        border-color: #0066ff;
      }
      
      .plan-cta.primary:hover {
        background: #0052cc;
        border-color: #0052cc;
      }
      
      .modal-footer {
        border-top: 1px solid #e5e7eb;
        padding-top: 1.5rem;
        margin-top: 2rem;
      }
      
      .or-text {
        font-size: 0.9rem;
        color: #9ca3af;
        margin-bottom: 0.75rem;
      }
      
      .signup-link {
        color: #0066ff;
        font-weight: 600;
        text-decoration: none;
        font-size: 1.05rem;
        transition: all 0.2s;
      }
      
      .signup-link:hover {
        text-decoration: underline;
      }
      
      @keyframes fadeIn {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }
      
      @keyframes slideUp {
        from {
          transform: translateY(30px);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }
      
      @keyframes bounce {
        0%, 100% {
          transform: translateY(0);
        }
        50% {
          transform: translateY(-10px);
        }
      }
      
      @media (max-width: 640px) {
        .conversion-modal {
          max-width: 100%;
        }
        
        .modal-content {
          padding: 2.5rem 1.5rem 1.5rem;
        }
        
        .modal-title {
          font-size: 1.75rem;
        }
        
        .plan-cards {
          grid-template-columns: 1fr;
          gap: 1rem;
        }
        
        .plan-price .amount {
          font-size: 2rem;
        }
      }
    </style>
  `;

  // Insert CSS and HTML into page
  function initModal() {
    // Add CSS to head
    document.head.insertAdjacentHTML('beforeend', modalCSS);
    
    // Add modal HTML to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Get modal elements
    const modal = document.getElementById('conversionLimitModal');
    const closeBtn = modal.querySelector('.modal-close');
    const signupLink = document.getElementById('signupLink');
    const limitMessage = document.getElementById('limitMessage');
    
    // Close modal function
    function closeModal() {
      modal.classList.remove('show');
    }
    
    // Close on button click
    closeBtn.addEventListener('click', closeModal);
    
    // Close on overlay click
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeModal();
      }
    });
    
    // Close on ESC key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modal.classList.contains('show')) {
        closeModal();
      }
    });
  }
  
  // Show modal function
  window.showConversionLimitModal = function(isLoggedIn = false) {
    const modal = document.getElementById('conversionLimitModal');
    const limitMessage = document.getElementById('limitMessage');
    const signupLink = document.getElementById('signupLink');
    
    if (isLoggedIn) {
      limitMessage.innerHTML = `
        <strong>You've used all 5 free conversions today!</strong><br>
        Upgrade to a premium plan for higher monthly limits and no daily restrictions.
      `;
      signupLink.style.display = 'none';
      modal.querySelector('.or-text').style.display = 'none';
    } else {
      limitMessage.innerHTML = `
        <strong>You've used your 2 free conversions today!</strong><br>
        Sign up for a free account to get 5 daily conversions, or upgrade to premium for more.
      `;
      signupLink.style.display = 'inline-block';
      modal.querySelector('.or-text').style.display = 'block';
    }
    
    modal.classList.add('show');
  };
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initModal);
  } else {
    initModal();
  }
})();