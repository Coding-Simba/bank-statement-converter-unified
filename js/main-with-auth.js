// Main JavaScript with Authentication for Bank Statement Converter

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// DOM Elements
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultContainer = document.getElementById('resultContainer');
const downloadBtn = document.getElementById('downloadBtn');
const convertAnotherBtn = document.getElementById('convertAnotherBtn');

// File handling variables
let selectedFile = null;
let convertedFileUrl = null;
let currentStatementId = null;

// Initialize navigation auth UI
async function initializeAuth() {
    const navAuth = document.querySelector('.nav-auth');
    if (!navAuth) return;
    
    const user = await Auth.getCurrentUser();
    
    if (user) {
        navAuth.innerHTML = `
            <div class="user-dropdown">
                <button class="user-menu-btn">
                    <i class="fas fa-user-circle"></i>
                    <span>${user.email}</span>
                    <i class="fas fa-chevron-down"></i>
                </button>
                <div class="dropdown-menu">
                    <a href="/dashboard.html">
                        <i class="fas fa-tachometer-alt"></i>
                        Dashboard
                    </a>
                    <a href="#" onclick="Auth.logout(); window.location.reload();">
                        <i class="fas fa-sign-out-alt"></i>
                        Logout
                    </a>
                </div>
            </div>
        `;
        
        // Toggle dropdown
        const dropdownBtn = navAuth.querySelector('.user-menu-btn');
        dropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownBtn.parentElement.classList.toggle('active');
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
}

// Initialize event listeners
function initializeEventListeners() {
    // File upload events
    if (uploadBtn) uploadBtn.addEventListener('click', () => fileInput.click());
    if (fileInput) fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop events
    if (uploadBox) {
        uploadBox.addEventListener('dragover', handleDragOver);
        uploadBox.addEventListener('dragleave', handleDragLeave);
        uploadBox.addEventListener('drop', handleDrop);
    }
    
    // Button events
    if (downloadBtn) downloadBtn.addEventListener('click', downloadCSV);
    if (convertAnotherBtn) convertAnotherBtn.addEventListener('click', resetUpload);
    
    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            const navMenu = document.querySelector('.nav-menu');
            navMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
}

// File handling functions
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
        selectedFile = file;
        processFile();
    } else {
        showError('Please select a valid PDF file');
    }
}

function handleDragOver(e) {
    e.preventDefault();
    uploadBox.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadBox.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadBox.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        selectedFile = files[0];
        processFile();
    } else {
        showError('Please drop a valid PDF file');
    }
}

// Process file with authentication check
async function processFile() {
    // Check upload limit first
    const canUpload = await UploadLimitUI.checkAndShow();
    if (!canUpload) {
        return;
    }
    
    // Show progress
    uploadBox.style.display = 'none';
    progressContainer.style.display = 'block';
    
    // Create form data
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    // Get session ID if not authenticated
    let headers = {};
    const token = Auth.getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    } else {
        // Get session for anonymous users
        const sessionData = await Auth.api('/auth/session');
        if (sessionData.session_id) {
            headers['X-Session-ID'] = sessionData.session_id;
        }
    }
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                updateProgress(progress);
            }
        }, 200);
        
        // Send file to backend
        const response = await fetch(`${API_BASE_URL}/convert`, {
            method: 'POST',
            headers: headers,
            body: formData
        });
        
        clearInterval(progressInterval);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Conversion failed');
        }
        
        const data = await response.json();
        
        // Update progress to 100%
        updateProgress(100);
        
        // Store the statement ID and file URL
        currentStatementId = data.statement_id;
        convertedFileUrl = data.download_url;
        
        // Show result after a short delay
        setTimeout(() => {
            showResult();
        }, 500);
        
    } catch (error) {
        console.error('Conversion error:', error);
        showError(error.message || 'Failed to convert file. Please try again.');
        resetUpload();
    }
}

function updateProgress(percent) {
    progressFill.style.width = percent + '%';
    
    if (percent < 30) {
        progressText.textContent = 'Uploading your statement...';
    } else if (percent < 60) {
        progressText.textContent = 'Analyzing bank format...';
    } else if (percent < 90) {
        progressText.textContent = 'Extracting transaction data...';
    } else {
        progressText.textContent = 'Finalizing conversion...';
    }
}

function showResult() {
    progressContainer.style.display = 'none';
    resultContainer.style.display = 'block';
    
    // Show feedback prompt after 2 seconds
    setTimeout(() => {
        if (currentStatementId) {
            FeedbackComponent.show(currentStatementId);
        }
    }, 2000);
}

async function downloadCSV() {
    if (convertedFileUrl) {
        // If we have a statement ID, use the API download endpoint
        if (currentStatementId) {
            const token = Auth.getToken();
            const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
            
            try {
                const response = await fetch(`${API_BASE_URL}/statement/${currentStatementId}/download`, {
                    headers: headers
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = selectedFile.name.replace('.pdf', '.csv');
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }
            } catch (error) {
                console.error('Download error:', error);
                // Fallback to direct URL if available
                if (convertedFileUrl) {
                    window.location.href = convertedFileUrl;
                }
            }
        } else if (convertedFileUrl) {
            // Fallback for backwards compatibility
            window.location.href = convertedFileUrl;
        }
    }
}

function resetUpload() {
    uploadBox.style.display = 'block';
    progressContainer.style.display = 'none';
    resultContainer.style.display = 'none';
    fileInput.value = '';
    selectedFile = null;
    convertedFileUrl = null;
    currentStatementId = null;
    progressFill.style.width = '0%';
    
    // Check limits again
    UploadLimitUI.checkAndShow();
}

function showError(message) {
    // You can implement a toast notification here
    alert(message);
}

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    document.querySelectorAll('.user-dropdown.active').forEach(dropdown => {
        dropdown.classList.remove('active');
    });
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeAuth();
    UploadLimitUI.checkAndShow();
});

// Make auth components globally available
window.AuthModal = AuthModal;
window.Auth = Auth;
window.FeedbackComponent = FeedbackComponent;
window.UploadLimitUI = UploadLimitUI;
window.LimitReachedModal = LimitReachedModal;