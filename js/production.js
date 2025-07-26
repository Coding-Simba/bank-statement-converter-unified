// ===================================
// Production JavaScript - Bank Statement Converter
// Version: 2.0
// ===================================

(function() {
  'use strict';

  // ===================================
  // DOM Elements
  // ===================================
  const elements = {
    menuToggle: null,
    navMenu: null,
    navOverlay: null,
    dropZone: null,
    fileInput: null,
    uploadForm: null,
    convertBtn: null,
    searchInput: null,
    bankCards: null,
    scrollToTop: null
  };

  // ===================================
  // Initialize Application
  // ===================================
  function init() {
    cacheDOMElements();
    setupEventListeners();
    initializeComponents();
    checkAuthStatus();
  }

  // ===================================
  // Cache DOM Elements
  // ===================================
  function cacheDOMElements() {
    elements.menuToggle = document.getElementById('menuToggle');
    elements.navMenu = document.querySelector('.nav-menu');
    elements.navOverlay = document.querySelector('.nav-overlay');
    elements.dropZone = document.getElementById('dropZone');
    elements.fileInput = document.getElementById('fileInput');
    elements.uploadForm = document.getElementById('uploadForm');
    elements.convertBtn = document.getElementById('convertBtn');
    elements.searchInput = document.getElementById('bankSearch');
    elements.bankCards = document.querySelectorAll('.bank-card');
    elements.scrollToTop = document.getElementById('scrollToTop');
  }

  // ===================================
  // Setup Event Listeners
  // ===================================
  function setupEventListeners() {
    // Mobile Navigation
    if (elements.menuToggle) {
      elements.menuToggle.addEventListener('click', toggleMobileMenu);
    }

    if (elements.navOverlay) {
      elements.navOverlay.addEventListener('click', closeMobileMenu);
    }

    // File Upload
    if (elements.dropZone) {
      setupDropZone();
    }

    // Search Functionality
    if (elements.searchInput) {
      elements.searchInput.addEventListener('input', debounce(handleSearch, 300));
    }

    // Scroll Events
    window.addEventListener('scroll', throttle(handleScroll, 100));

    // Smooth Scroll for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', handleSmoothScroll);
    });

    // Form Validation
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', handleFormSubmit);
    });

    // Scroll to Top
    if (elements.scrollToTop) {
      elements.scrollToTop.addEventListener('click', scrollToTop);
    }
  }

  // ===================================
  // Mobile Navigation
  // ===================================
  function toggleMobileMenu() {
    const isActive = elements.navMenu.classList.contains('active');
    
    if (isActive) {
      closeMobileMenu();
    } else {
      openMobileMenu();
    }
  }

  function openMobileMenu() {
    elements.navMenu.classList.add('active');
    elements.navOverlay?.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Animate menu toggle
    const spans = elements.menuToggle.querySelectorAll('span');
    spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
    spans[1].style.opacity = '0';
    spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
  }

  function closeMobileMenu() {
    elements.navMenu.classList.remove('active');
    elements.navOverlay?.classList.remove('active');
    document.body.style.overflow = '';
    
    // Reset menu toggle
    const spans = elements.menuToggle.querySelectorAll('span');
    spans[0].style.transform = '';
    spans[1].style.opacity = '';
    spans[2].style.transform = '';
  }

  // ===================================
  // File Upload Functionality
  // ===================================
  function setupDropZone() {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      elements.dropZone.addEventListener(eventName, preventDefaults, false);
      document.body.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      elements.dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      elements.dropZone.addEventListener(eventName, unhighlight, false);
    });

    elements.dropZone.addEventListener('drop', handleDrop, false);
    elements.dropZone.addEventListener('click', () => elements.fileInput?.click());
    
    if (elements.fileInput) {
      elements.fileInput.addEventListener('change', handleFileSelect);
    }
  }

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function highlight(e) {
    elements.dropZone.classList.add('highlight');
  }

  function unhighlight(e) {
    elements.dropZone.classList.remove('highlight');
  }

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
  }

  function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
  }

  function handleFiles(files) {
    ([...files]).forEach(uploadFile);
  }

  function uploadFile(file) {
    // Validate file type
    const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
      showNotification('Please upload a valid file type (PDF, JPG, PNG, GIF)', 'error');
      return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      showNotification('File size must be less than 10MB', 'error');
      return;
    }

    // Show file preview
    showFilePreview(file);

    // Upload file
    const formData = new FormData();
    formData.append('file', file);

    // Show progress
    showUploadProgress();

    fetch('/api/upload', {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    .then(response => response.json())
    .then(data => {
      hideUploadProgress();
      if (data.success) {
        showNotification('File uploaded successfully!', 'success');
        processConversion(data.fileId);
      } else {
        showNotification(data.message || 'Upload failed', 'error');
      }
    })
    .catch(error => {
      hideUploadProgress();
      showNotification('Upload failed. Please try again.', 'error');
      console.error('Upload error:', error);
    });
  }

  // ===================================
  // Search Functionality
  // ===================================
  function handleSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    
    elements.bankCards.forEach(card => {
      const bankName = card.dataset.bankName?.toLowerCase() || '';
      const bankLocation = card.dataset.location?.toLowerCase() || '';
      const isMatch = bankName.includes(searchTerm) || bankLocation.includes(searchTerm);
      
      card.style.display = isMatch ? '' : 'none';
      
      // Add animation
      if (isMatch) {
        card.classList.add('animate-fadeIn');
      }
    });

    // Show no results message if needed
    const visibleCards = Array.from(elements.bankCards).filter(card => card.style.display !== 'none');
    const noResultsMsg = document.getElementById('noResults');
    
    if (visibleCards.length === 0) {
      if (!noResultsMsg) {
        const msg = document.createElement('div');
        msg.id = 'noResults';
        msg.className = 'no-results';
        msg.textContent = 'No banks found matching your search.';
        elements.searchInput.parentElement.appendChild(msg);
      }
    } else if (noResultsMsg) {
      noResultsMsg.remove();
    }
  }

  // ===================================
  // Scroll Functionality
  // ===================================
  function handleScroll() {
    // Show/hide scroll to top button
    if (elements.scrollToTop) {
      if (window.pageYOffset > 300) {
        elements.scrollToTop.classList.add('visible');
      } else {
        elements.scrollToTop.classList.remove('visible');
      }
    }

    // Add shadow to navigation on scroll
    const nav = document.querySelector('nav');
    if (nav) {
      if (window.pageYOffset > 10) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    }
  }

  function scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }

  function handleSmoothScroll(e) {
    e.preventDefault();
    const targetId = e.currentTarget.getAttribute('href');
    if (targetId === '#') return;
    
    const targetElement = document.querySelector(targetId);
    if (targetElement) {
      const navHeight = document.querySelector('nav')?.offsetHeight || 0;
      const targetPosition = targetElement.offsetTop - navHeight - 20;
      
      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });
    }
  }

  // ===================================
  // Form Handling
  // ===================================
  function handleFormSubmit(e) {
    const form = e.target;
    
    // Skip if form has novalidate attribute
    if (form.hasAttribute('novalidate')) return;
    
    // Validate all required fields
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
      if (!validateField(field)) {
        isValid = false;
        showFieldError(field);
      } else {
        clearFieldError(field);
      }
    });
    
    if (!isValid) {
      e.preventDefault();
      showNotification('Please fill in all required fields correctly.', 'error');
    }
  }

  function validateField(field) {
    const value = field.value.trim();
    
    // Check if empty
    if (!value) return false;
    
    // Email validation
    if (field.type === 'email') {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value);
    }
    
    // Phone validation
    if (field.type === 'tel') {
      const phoneRegex = /^[\d\s\-\+\(\)]+$/;
      return phoneRegex.test(value) && value.replace(/\D/g, '').length >= 10;
    }
    
    // Password validation
    if (field.type === 'password') {
      return value.length >= 8;
    }
    
    return true;
  }

  function showFieldError(field) {
    field.classList.add('error');
    const errorMsg = field.parentElement.querySelector('.error-message');
    if (!errorMsg) {
      const msg = document.createElement('span');
      msg.className = 'error-message';
      msg.textContent = getErrorMessage(field);
      field.parentElement.appendChild(msg);
    }
  }

  function clearFieldError(field) {
    field.classList.remove('error');
    const errorMsg = field.parentElement.querySelector('.error-message');
    if (errorMsg) {
      errorMsg.remove();
    }
  }

  function getErrorMessage(field) {
    if (field.type === 'email') return 'Please enter a valid email address';
    if (field.type === 'tel') return 'Please enter a valid phone number';
    if (field.type === 'password') return 'Password must be at least 8 characters';
    return 'This field is required';
  }

  // ===================================
  // Authentication
  // ===================================
  function checkAuthStatus() {
    const token = getAuthToken();
    const authElements = document.querySelectorAll('[data-auth-required]');
    const userMenus = document.querySelectorAll('.user-menu');
    const loginBtns = document.querySelectorAll('.login-btn');
    
    if (token) {
      // User is logged in
      authElements.forEach(el => el.style.display = '');
      userMenus.forEach(el => el.style.display = '');
      loginBtns.forEach(el => el.style.display = 'none');
      
      // Get user info
      fetchUserInfo();
    } else {
      // User is not logged in
      authElements.forEach(el => el.style.display = 'none');
      userMenus.forEach(el => el.style.display = 'none');
      loginBtns.forEach(el => el.style.display = '');
    }
  }

  function getAuthToken() {
    return localStorage.getItem('authToken');
  }

  function setAuthToken(token) {
    localStorage.setItem('authToken', token);
  }

  function removeAuthToken() {
    localStorage.removeItem('authToken');
  }

  function fetchUserInfo() {
    fetch('/api/user', {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        updateUserInterface(data.user);
      }
    })
    .catch(error => {
      console.error('Failed to fetch user info:', error);
    });
  }

  function updateUserInterface(user) {
    const userNameElements = document.querySelectorAll('.user-name');
    const userEmailElements = document.querySelectorAll('.user-email');
    
    userNameElements.forEach(el => el.textContent = user.name);
    userEmailElements.forEach(el => el.textContent = user.email);
  }

  // ===================================
  // Utility Functions
  // ===================================
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  function throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 3000);
  }

  function showFilePreview(file) {
    const preview = document.getElementById('filePreview');
    if (!preview) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
      preview.innerHTML = `
        <div class="file-preview-item">
          <div class="file-icon">
            <i class="fas fa-file-pdf"></i>
          </div>
          <div class="file-info">
            <p class="file-name">${file.name}</p>
            <p class="file-size">${formatFileSize(file.size)}</p>
          </div>
          <button class="remove-file" onclick="removeFile()">
            <i class="fas fa-times"></i>
          </button>
        </div>
      `;
      preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function showUploadProgress() {
    const progress = document.getElementById('uploadProgress');
    if (progress) {
      progress.style.display = 'block';
      progress.querySelector('.progress-bar').style.width = '0%';
      
      // Simulate progress
      let width = 0;
      const interval = setInterval(() => {
        if (width >= 90) {
          clearInterval(interval);
        } else {
          width += 10;
          progress.querySelector('.progress-bar').style.width = width + '%';
        }
      }, 200);
    }
  }

  function hideUploadProgress() {
    const progress = document.getElementById('uploadProgress');
    if (progress) {
      progress.querySelector('.progress-bar').style.width = '100%';
      setTimeout(() => {
        progress.style.display = 'none';
      }, 500);
    }
  }

  // ===================================
  // Initialize Components
  // ===================================
  function initializeComponents() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize modals
    initModals();
    
    // Initialize tabs
    initTabs();
    
    // Initialize accordions
    initAccordions();
    
    // Lazy load images
    initLazyLoading();
  }

  function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(el => {
      el.addEventListener('mouseenter', showTooltip);
      el.addEventListener('mouseleave', hideTooltip);
    });
  }

  function showTooltip(e) {
    const text = e.target.dataset.tooltip;
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    tooltip.style.left = rect.left + (rect.width - tooltip.offsetWidth) / 2 + 'px';
    
    setTimeout(() => tooltip.classList.add('show'), 10);
  }

  function hideTooltip() {
    const tooltips = document.querySelectorAll('.tooltip');
    tooltips.forEach(tooltip => {
      tooltip.classList.remove('show');
      setTimeout(() => tooltip.remove(), 300);
    });
  }

  function initModals() {
    const modalTriggers = document.querySelectorAll('[data-modal]');
    modalTriggers.forEach(trigger => {
      trigger.addEventListener('click', openModal);
    });
    
    const modalCloses = document.querySelectorAll('.modal-close');
    modalCloses.forEach(close => {
      close.addEventListener('click', closeModal);
    });
    
    window.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal')) {
        closeModal(e);
      }
    });
  }

  function openModal(e) {
    e.preventDefault();
    const modalId = e.currentTarget.dataset.modal;
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModal(e) {
    const modal = e.target.closest('.modal');
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  function initTabs() {
    const tabContainers = document.querySelectorAll('.tabs');
    tabContainers.forEach(container => {
      const tabs = container.querySelectorAll('.tab');
      const panels = container.querySelectorAll('.tab-panel');
      
      tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => {
          tabs.forEach(t => t.classList.remove('active'));
          panels.forEach(p => p.classList.remove('active'));
          
          tab.classList.add('active');
          panels[index].classList.add('active');
        });
      });
    });
  }

  function initAccordions() {
    const accordions = document.querySelectorAll('.accordion-header');
    accordions.forEach(header => {
      header.addEventListener('click', () => {
        const content = header.nextElementSibling;
        const isOpen = header.classList.contains('active');
        
        // Close all accordions in the same group
        const group = header.closest('.accordion-group');
        if (group) {
          group.querySelectorAll('.accordion-header').forEach(h => {
            h.classList.remove('active');
            h.nextElementSibling.style.maxHeight = null;
          });
        }
        
        // Open clicked accordion
        if (!isOpen) {
          header.classList.add('active');
          content.style.maxHeight = content.scrollHeight + 'px';
        }
      });
    });
  }

  function initLazyLoading() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            imageObserver.unobserve(img);
          }
        });
      });
      
      lazyImages.forEach(img => imageObserver.observe(img));
    } else {
      // Fallback for older browsers
      lazyImages.forEach(img => {
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
      });
    }
  }

  // ===================================
  // Initialize on DOM Ready
  // ===================================
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // ===================================
  // Public API
  // ===================================
  window.BankConverter = {
    showNotification,
    getAuthToken,
    setAuthToken,
    removeAuthToken
  };

})();