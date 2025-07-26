/**
 * Upload functionality for bank statement converter
 * Handles file upload, drag & drop, and conversion simulation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const uploadArea = document.getElementById('uploadArea');
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    const progressArea = document.getElementById('progressArea');
    const successArea = document.getElementById('successArea');
    const downloadBtn = document.getElementById('downloadBtn');
    const convertAnother = document.getElementById('convertAnother');
    
    // File upload button click
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function() {
            fileInput.click();
        });
    }
    
    // File input change
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type === 'application/pdf') {
                handleFileUpload(file);
            } else if (file) {
                alert('Please select a valid PDF file');
            }
        });
    }
    
    // Drag and drop functionality
    if (uploadArea) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, function() {
                uploadArea.classList.add('drag-over');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, function() {
                uploadArea.classList.remove('drag-over');
            }, false);
        });
        
        // Handle dropped files
        uploadArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                const file = files[0];
                if (file.type === 'application/pdf') {
                    handleFileUpload(file);
                } else {
                    alert('Please drop a valid PDF file');
                }
            }
        }, false);
    }
    
    // Convert another button
    if (convertAnother) {
        convertAnother.addEventListener('click', function() {
            resetUpload();
        });
    }
    
    // Download button
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            downloadConvertedFile();
        });
    }
    
    // Helper functions
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function handleFileUpload(file) {
        // Show progress area
        uploadArea.classList.add('hidden');
        progressArea.classList.remove('hidden');
        
        // Simulate conversion process
        simulateConversion();
    }
    
    function simulateConversion() {
        const progressFill = document.querySelector('.progress-fill');
        let progress = 0;
        
        const interval = setInterval(function() {
            progress += Math.random() * 30;
            
            if (progress >= 100) {
                progress = 100;
                progressFill.style.width = progress + '%';
                
                setTimeout(function() {
                    progressArea.classList.add('hidden');
                    successArea.classList.remove('hidden');
                }, 500);
                
                clearInterval(interval);
            } else {
                progressFill.style.width = progress + '%';
            }
        }, 300);
    }
    
    function resetUpload() {
        // Reset all states
        uploadArea.classList.remove('hidden');
        progressArea.classList.add('hidden');
        successArea.classList.add('hidden');
        
        // Reset progress bar
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = '0%';
        }
        
        // Clear file input
        fileInput.value = '';
    }
    
    function downloadConvertedFile() {
        // Create sample CSV data
        const bankName = document.querySelector('.bank-hero-title').textContent.split(' ')[0];
        const sampleData = `Date,Description,Amount,Balance
2025-01-15,"Direct Deposit - Salary",2500.00,5432.10
2025-01-14,"Amazon Purchase",-45.99,2932.10
2025-01-13,"Grocery Store",-128.50,2978.09
2025-01-12,"Gas Station",-52.00,3106.59
2025-01-11,"Restaurant",-68.75,3158.59
2025-01-10,"ATM Withdrawal",-200.00,3227.34
2025-01-09,"Online Transfer",500.00,3427.34
2025-01-08,"Utility Bill",-156.25,2927.34
2025-01-07,"Coffee Shop",-4.50,3083.59
2025-01-06,"Subscription Service",-14.99,3088.09`;
        
        // Create blob and trigger download
        const blob = new Blob([sampleData], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${bankName}_statement_converted.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
});