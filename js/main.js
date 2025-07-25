// Main JavaScript for Bank Statement Converter

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

// Modal Elements
const loginModal = document.getElementById('loginModal');
const registerModal = document.getElementById('registerModal');
const loginBtn = document.getElementById('loginBtn');
const registerBtn = document.getElementById('registerBtn');
const registerPricingBtn = document.getElementById('registerPricingBtn');
const subscribeBtn = document.getElementById('subscribeBtn');
const closeBtns = document.getElementsByClassName('close');

// File handling variables
let selectedFile = null;
let convertedFileUrl = null;

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
    
    // Modal events - only if they exist on the page
    if (loginBtn) loginBtn.addEventListener('click', () => openModal(loginModal));
    if (registerBtn) registerBtn.addEventListener('click', () => openModal(registerModal));
    if (registerPricingBtn) registerPricingBtn.addEventListener('click', () => openModal(registerModal));
    if (subscribeBtn) subscribeBtn.addEventListener('click', () => alert('Subscription feature coming soon!'));
    
    // Close modal events
    if (closeBtns) {
        Array.from(closeBtns).forEach(btn => {
            btn.addEventListener('click', function() {
                this.parentElement.parentElement.style.display = 'none';
            });
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (loginModal && e.target === loginModal) loginModal.style.display = 'none';
        if (registerModal && e.target === registerModal) registerModal.style.display = 'none';
    });
    
    // Form submissions
    if (document.getElementById('loginForm')) document.getElementById('loginForm').addEventListener('submit', handleLogin);
    if (document.getElementById('registerForm')) document.getElementById('registerForm').addEventListener('submit', handleRegister);
}

// File handling functions
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
        selectedFile = file;
        processFile();
    } else {
        alert('Please select a valid PDF file.');
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
    if (files.length > 0) {
        const file = files[0];
        if (file.type === 'application/pdf') {
            selectedFile = file;
            processFile();
        } else {
            alert('Please drop a valid PDF file.');
        }
    }
}

// File processing
async function processFile() {
    if (!selectedFile) return;
    
    // Show progress
    uploadBox.style.display = 'none';
    progressContainer.style.display = 'block';
    
    // For demo purposes, simulate the conversion process
    simulateProgress();
    
    // Simulate conversion completion after 3 seconds
    setTimeout(() => {
        progressContainer.style.display = 'none';
        resultContainer.style.display = 'block';
        
        // Set a flag to use demo CSV
        convertedFileUrl = 'demo';
    }, 3000);
}

// Simulate progress bar
function simulateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress > 90) {
            progress = 100;
            progressFill.style.width = progress + '%';
            progressText.textContent = 'Finalizing conversion...';
            clearInterval(interval);
        } else {
            progressFill.style.width = progress + '%';
            
            if (progress < 30) {
                progressText.textContent = 'Uploading file...';
            } else if (progress < 60) {
                progressText.textContent = 'Analyzing bank statement...';
            } else {
                progressText.textContent = 'Converting to CSV...';
            }
        }
    }, 500);
}

// Download CSV
async function downloadCSV() {
    if (convertedFileUrl) {
        // Download from server - convertedFileUrl already includes /api/
        window.location.href = `http://localhost:5000${convertedFileUrl}`;
    } else {
        // For demo purposes, create a sample CSV
        const sampleCSV = `Date,Description,Money Out,Money In,Balance
2019-02-01,"Balance brought forward",,,40000.00
2019-02-01,"Card payment - High St Petrol Station",24.50,,39975.50
2019-02-01,"Direct debit - Green Mobile Phone Bill",20.00,,39955.50
2019-02-03,"Cash Withdrawal - YourBank, Anytown",30.00,,39925.50
2019-02-04,"YourJob BiWeekly Payment",,2575.00,42500.50
2019-02-11,"Direct Deposit - YourBank, Anytown High Street",,300.00,42800.50
2019-02-16,"Cash Withdrawal - RandomBank, Randomford",50.00,,42750.50
2019-02-17,"Card payment - High St Petrol Station",40.00,,42710.50
2019-02-17,"Direct Debit - Home Insurance",78.34,,42632.16
2019-02-18,"YourJob BiWeekly Payment",,2575.00,45207.16
2019-02-18,"Randomford's Deli",15.00,,45195.16
2019-02-24,"Anytown's Jewelers",150.00,,45042.16
2019-02-24,"Direct Deposit",,25.00,45067.16
2019-02-28,"Monthly Apartment Rent",987.33,,44079.83`;
        
        // Create blob and download
        const blob = new Blob([sampleCSV], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'bank_statement_converted.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    }
}

// Reset upload interface
function resetUpload() {
    selectedFile = null;
    convertedFileUrl = null;
    fileInput.value = '';
    
    uploadBox.style.display = 'block';
    progressContainer.style.display = 'none';
    resultContainer.style.display = 'none';
    progressFill.style.width = '0%';
}

// Modal functions
function openModal(modal) {
    modal.style.display = 'block';
}

// Authentication handlers
async function handleLogin(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: formData.get('email'),
                password: formData.get('password')
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('authToken', data.token);
            loginModal.style.display = 'none';
            alert('Login successful!');
            updateUIForLoggedInUser();
        } else {
            alert('Login failed. Please check your credentials.');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('An error occurred. Please try again.');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    // Validate passwords match
    if (formData.get('password') !== formData.get('confirmPassword')) {
        alert('Passwords do not match!');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: formData.get('name'),
                email: formData.get('email'),
                password: formData.get('password')
            })
        });
        
        if (response.ok) {
            registerModal.style.display = 'none';
            alert('Registration successful! Please login.');
            openModal(loginModal);
        } else {
            const error = await response.json();
            alert(error.message || 'Registration failed. Please try again.');
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('An error occurred. Please try again.');
    }
}

// Update UI for logged-in users
function updateUIForLoggedInUser() {
    loginBtn.style.display = 'none';
    registerBtn.textContent = 'Logout';
    registerBtn.removeEventListener('click', () => openModal(registerModal));
    registerBtn.addEventListener('click', logout);
}

// Logout function
function logout() {
    localStorage.removeItem('authToken');
    location.reload();
}

// Check authentication status on load
function checkAuthStatus() {
    const token = localStorage.getItem('authToken');
    if (token) {
        updateUIForLoggedInUser();
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    checkAuthStatus();
});

// Language selector
const languageSelect = document.getElementById('languageSelect');
if (languageSelect) {
    languageSelect.addEventListener('change', (e) => {
        // In a real app, this would change the UI language
        console.log('Language changed to:', e.target.value);
    });
}