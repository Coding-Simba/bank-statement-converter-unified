// Modern Homepage JavaScript - Fixed Download Version

(function() {
    'use strict';

    // DOM Elements
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const chooseFilesBtn = document.getElementById('chooseFilesBtn');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileMenu = document.getElementById('mobileMenu');

    // State tracking
    let isSuccessState = false;

    // Initialize
    function init() {
        setupFileUpload();
        setupMobileMenu();
        setupSmoothScroll();
        setupDropdowns();
    }

    // Store event handlers for cleanup
    let uploadBoxClickHandler = null;
    let chooseFilesBtnClickHandler = null;
    let fileInputChangeHandler = null;

    // File Upload Functionality
    function setupFileUpload() {
        if (!uploadBox || !fileInput || !chooseFilesBtn) return;

        // Remove existing event listeners before adding new ones
        cleanupFileUploadListeners();

        // Create new handlers
        chooseFilesBtnClickHandler = (e) => {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        };

        uploadBoxClickHandler = (e) => {
            // Check if we're clicking on a button or in success state
            if (isSuccessState) {
                e.stopPropagation();
                return;
            }
            
            // Check for specific elements
            if (e.target === chooseFilesBtn || chooseFilesBtn.contains(e.target)) return;
            if (e.target.classList.contains('download-btn')) return;
            if (e.target.closest('.download-btn')) return;
            if (e.target.closest('.download-buttons')) return;
            if (e.target.closest('.success-state')) return;
            
            fileInput.click();
        };

        fileInputChangeHandler = handleFileSelect;

        // Add event listeners
        chooseFilesBtn.addEventListener('click', chooseFilesBtnClickHandler);
        uploadBox.addEventListener('click', uploadBoxClickHandler);
        fileInput.addEventListener('change', fileInputChangeHandler);

        // Drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadBox.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadBox.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadBox.addEventListener(eventName, unhighlight, false);
        });

        uploadBox.addEventListener('drop', handleDrop, false);
    }

    // Cleanup function to remove event listeners
    function cleanupFileUploadListeners() {
        if (uploadBoxClickHandler && uploadBox) {
            uploadBox.removeEventListener('click', uploadBoxClickHandler);
        }
        if (chooseFilesBtnClickHandler && chooseFilesBtn) {
            chooseFilesBtn.removeEventListener('click', chooseFilesBtnClickHandler);
        }
        if (fileInputChangeHandler && fileInput) {
            fileInput.removeEventListener('change', fileInputChangeHandler);
        }
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        if (!isSuccessState) {
            uploadBox.classList.add('dragover');
        }
    }

    function unhighlight(e) {
        uploadBox.classList.remove('dragover');
    }

    function handleDrop(e) {
        if (!isSuccessState) {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        ([...files]).forEach(processFile);
    }

    function processFile(file) {
        // Validate file type
        const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            showNotification('Please upload a PDF or image file (JPG, PNG)', 'error');
            return;
        }

        // Validate file size (50MB limit)
        const maxSize = 50 * 1024 * 1024;
        if (file.size > maxSize) {
            showNotification('File size must be less than 50MB', 'error');
            return;
        }

        // Show processing state
        showProcessingState(file);

        // Upload to backend API
        uploadToBackend(file);
    }

    function showProcessingState(file) {
        isSuccessState = false;
        const uploadContent = uploadBox.innerHTML;
        uploadBox.setAttribute('data-original-content', uploadContent);
        
        uploadBox.innerHTML = `
            <div class="processing-state">
                <div class="spinner"></div>
                <h3>Processing ${file.name}</h3>
                <p class="processing-message">Converting your bank statement...</p>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
        `;

        // Animate progress bar and update message
        const progressFill = uploadBox.querySelector('.progress-fill');
        const processingMessage = uploadBox.querySelector('.processing-message');
        let progress = 0;
        let messageIndex = 0;
        const messages = [
            'Converting your bank statement...',
            'Analyzing document structure...',
            'Extracting transaction data...',
            'Applying OCR for scanned pages...',
            'Finalizing conversion...'
        ];
        
        const interval = setInterval(() => {
            progress += 5;
            progressFill.style.width = progress + '%';
            
            // Update message every 20% progress
            if (progress % 20 === 0 && messageIndex < messages.length - 1) {
                messageIndex++;
                processingMessage.textContent = messages[messageIndex];
            }
            
            if (progress >= 90) {
                processingMessage.textContent = messages[messages.length - 1];
                clearInterval(interval);
            }
        }, 360);
    }

    async function showSuccessState(file) {
        isSuccessState = true;
        
        // Store file reference for download
        uploadBox.setAttribute('data-file-name', file.name);
        
        // Try to fetch the CSV content to show transaction count
        let transactionText = `${file.name} has been converted successfully.`;
        const statementId = uploadBox.getAttribute('data-statement-id');
        
        if (statementId) {
            try {
                const downloadUrl = window.location.hostname === 'localhost' 
                    ? `http://localhost:8000/api/statement/${statementId}/download`
                    : `https://bankcsvconverter.com/api/statement/${statementId}/download`;
                
                const response = await fetch(downloadUrl, {
                    method: 'GET',
                    mode: 'cors'
                });
                
                if (response.ok) {
                    const csvText = await response.text();
                    const lines = csvText.trim().split('\n');
                    // Subtract 1 for header row
                    const transactionCount = lines.length - 1;
                    
                    if (transactionCount > 0) {
                        transactionText = `Found ${transactionCount} transaction${transactionCount !== 1 ? 's' : ''} in ${file.name}`;
                    } else {
                        transactionText = `No transactions found in PDF: ${file.name}`;
                    }
                }
            } catch (error) {
                console.error('Error fetching CSV for preview:', error);
            }
        }
        
        uploadBox.innerHTML = `
            <div class="success-state">
                <i class="fas fa-check-circle" style="font-size: 3rem; color: #4ade80; margin-bottom: 1rem;"></i>
                <h3>Conversion Complete!</h3>
                <p>${transactionText}</p>
                <div class="download-buttons">
                    <button class="download-btn csv-btn" type="button" data-format="csv">
                        <i class="fas fa-file-csv"></i> Download CSV
                    </button>
                    <button class="download-btn excel-btn" type="button" data-format="excel">
                        <i class="fas fa-file-excel"></i> Download Excel
                    </button>
                </div>
                <button class="convert-another-btn" type="button">Convert Another File</button>
            </div>
        `;

        // Wait for DOM update then add event listeners
        setTimeout(() => {
            const convertAnotherBtn = uploadBox.querySelector('.convert-another-btn');
            const csvBtn = uploadBox.querySelector('.csv-btn');
            const excelBtn = uploadBox.querySelector('.excel-btn');

            if (convertAnotherBtn) {
                convertAnotherBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    resetUploadBox();
                });
            }

            if (csvBtn) {
                csvBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    downloadFile(file, 'csv');
                });
            }

            if (excelBtn) {
                excelBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    downloadFile(file, 'excel');
                });
            }
        }, 100);
    }

    function resetUploadBox() {
        isSuccessState = false;
        const originalContent = uploadBox.getAttribute('data-original-content');
        uploadBox.innerHTML = originalContent;
        fileInput.value = ''; // Clear file input
        setupFileUpload(); // Re-initialize event listeners
    }

    // Backend upload functionality
    async function uploadToBackend(file) {
        const formData = new FormData();
        formData.append('file', file);

        console.log('Attempting to upload file:', file.name, 'Size:', file.size);

        try {
            // Try different URL formats to avoid CORS issues
            const apiUrl = window.location.hostname === 'localhost' 
                ? 'http://localhost:8000/api/convert'
                : 'https://bankcsvconverter.com/api/convert';
            
            console.log('Using API URL:', apiUrl);
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData,
                // Remove credentials for now to avoid CORS issues
                // credentials: 'include',
                mode: 'cors'
            });

            console.log('Response received:', response.status, response.statusText);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Conversion failed');
            }

            const result = await response.json();
            console.log('Conversion result:', result);
            
            // Store the statement ID for download
            uploadBox.setAttribute('data-statement-id', result.id);
            
            // Show success state
            await showSuccessState(file);
            
        } catch (error) {
            console.error('Upload error:', error);
            console.error('Error name:', error.name);
            console.error('Error message:', error.message);
            
            // More detailed error logging
            if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
                console.error('Network error - cannot reach backend');
                showNotification('Cannot connect to backend server. Please try again later.', 'error');
                
                // Test connection
                testBackendConnection();
            } else {
                showNotification(error.message || 'Failed to convert file', 'error');
            }
            resetUploadBox();
        }
    }
    
    // Test backend connection
    async function testBackendConnection() {
        console.log('Testing backend connection...');
        const healthUrl = window.location.hostname === 'localhost' 
            ? 'http://localhost:8000/health'
            : 'https://bankcsvconverter.com/health';
            
        try {
            const response = await fetch(healthUrl, {
                method: 'GET',
                mode: 'cors'
            });
            const data = await response.json();
            console.log('Backend health check successful:', data);
        } catch (error) {
            console.error('Backend health check failed:', error);
            console.error('Please ensure the backend is running: python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 5000');
        }
    }

    // Download functionality
    function downloadFile(originalFile, format) {
        console.log('Downloading file:', originalFile.name, 'as', format);
        
        const statementId = uploadBox.getAttribute('data-statement-id');
        
        if (statementId) {
            // Download from backend
            const downloadUrl = window.location.hostname === 'localhost' 
                ? `http://localhost:8000/api/statement/${statementId}/download`
                : `https://bankcsvconverter.com/api/statement/${statementId}/download`;
            
            window.location.href = downloadUrl;
            showNotification(`Downloading converted file`, 'success');
        } else {
            // Fallback to demo data
            const fileName = originalFile.name.replace(/\.[^/.]+$/, '');
            const convertedFileName = `${fileName}_converted.${format === 'csv' ? 'csv' : 'xlsx'}`;
            
            if (format === 'csv') {
                downloadCSV(convertedFileName);
            } else {
                downloadExcel(convertedFileName);
            }
            
            showNotification(`Downloading ${convertedFileName}`, 'success');
        }
    }

    function downloadCSV(filename) {
        console.log('Starting CSV download:', filename);
        
        // Sample CSV data - in production this would come from the API
        const csvData = [
            ['Date', 'Description', 'Amount', 'Balance'],
            ['2024-01-15', 'Opening Balance', '0.00', '5000.00'],
            ['2024-01-16', 'Grocery Store', '-45.32', '4954.68'],
            ['2024-01-17', 'Salary Deposit', '3500.00', '8454.68'],
            ['2024-01-18', 'Electric Bill', '-125.00', '8329.68'],
            ['2024-01-19', 'Gas Station', '-65.45', '8264.23'],
            ['2024-01-20', 'Restaurant', '-82.50', '8181.73'],
            ['2024-01-21', 'ATM Withdrawal', '-200.00', '7981.73'],
            ['2024-01-22', 'Online Transfer', '-500.00', '7481.73'],
            ['2024-01-23', 'Coffee Shop', '-12.75', '7468.98'],
            ['2024-01-24', 'Pharmacy', '-28.90', '7440.08']
        ];
        
        const csvContent = csvData.map(row => row.join(',')).join('\n');
        
        // Try multiple methods to ensure download works
        try {
            // Method 1: Standard blob download
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = window.URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.style.display = 'none';
            
            // Force the download by temporarily adding to DOM
            document.body.appendChild(link);
            
            // Use setTimeout to ensure the element is in the DOM
            setTimeout(() => {
                link.click();
                
                // Cleanup
                setTimeout(() => {
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(url);
                }, 100);
            }, 0);
            
        } catch (error) {
            console.error('Primary download method failed:', error);
            
            // Fallback: Use data URI
            try {
                const dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);
                const link = document.createElement('a');
                link.href = dataUri;
                link.download = filename;
                link.style.display = 'none';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } catch (fallbackError) {
                console.error('Fallback download method failed:', fallbackError);
                showNotification('Download failed. Please check your browser settings.', 'error');
            }
        }
    }

    function downloadExcel(filename) {
        console.log('Starting Excel download:', filename);
        
        // Create Excel-compatible XML format
        const excelContent = `
            <html xmlns:x="urn:schemas-microsoft-com:office:excel">
            <head>
                <meta charset="UTF-8">
                <style>
                    table { border-collapse: collapse; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #4CAF50; color: white; font-weight: bold; }
                </style>
            </head>
            <body>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Amount</th>
                        <th>Balance</th>
                    </tr>
                    <tr><td>2024-01-15</td><td>Opening Balance</td><td>0.00</td><td>5000.00</td></tr>
                    <tr><td>2024-01-16</td><td>Grocery Store</td><td>-45.32</td><td>4954.68</td></tr>
                    <tr><td>2024-01-17</td><td>Salary Deposit</td><td>3500.00</td><td>8454.68</td></tr>
                    <tr><td>2024-01-18</td><td>Electric Bill</td><td>-125.00</td><td>8329.68</td></tr>
                    <tr><td>2024-01-19</td><td>Gas Station</td><td>-65.45</td><td>8264.23</td></tr>
                    <tr><td>2024-01-20</td><td>Restaurant</td><td>-82.50</td><td>8181.73</td></tr>
                    <tr><td>2024-01-21</td><td>ATM Withdrawal</td><td>-200.00</td><td>7981.73</td></tr>
                    <tr><td>2024-01-22</td><td>Online Transfer</td><td>-500.00</td><td>7481.73</td></tr>
                    <tr><td>2024-01-23</td><td>Coffee Shop</td><td>-12.75</td><td>7468.98</td></tr>
                    <tr><td>2024-01-24</td><td>Pharmacy</td><td>-28.90</td><td>7440.08</td></tr>
                </table>
            </body>
            </html>
        `;

        const blob = new Blob([excelContent], { 
            type: 'application/vnd.ms-excel;charset=utf-8;' 
        });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        link.style.position = 'absolute';
        link.style.top = '-1000px';
        
        document.body.appendChild(link);
        link.click();
        
        setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }, 100);
    }

    // Mobile Menu
    function setupMobileMenu() {
        if (!mobileMenuToggle || !mobileMenu) return;

        mobileMenuToggle.addEventListener('click', toggleMobileMenu);

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenu.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                mobileMenu.classList.remove('active');
            }
        });

        // Close menu when clicking on a link
        const mobileLinks = mobileMenu.querySelectorAll('a');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.remove('active');
            });
        });
    }

    function toggleMobileMenu() {
        mobileMenu.classList.toggle('active');
    }

    // Smooth Scroll
    function setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href === '#') return;

                const target = document.querySelector(href);
                if (!target) return;

                e.preventDefault();
                const offset = 80; // Account for fixed header
                const targetPosition = target.offsetTop - offset;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            });
        });
    }

    // Dropdowns
    function setupDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown');
        
        dropdowns.forEach(dropdown => {
            const toggle = dropdown.querySelector('.dropdown-toggle');
            const menu = dropdown.querySelector('.dropdown-menu');
            
            if (!toggle || !menu) return;

            // Click to toggle on mobile
            toggle.addEventListener('click', (e) => {
                if (window.innerWidth <= 768) {
                    e.preventDefault();
                    menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
                }
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.dropdown')) {
                document.querySelectorAll('.dropdown-menu').forEach(menu => {
                    if (window.innerWidth <= 768) {
                        menu.style.display = 'none';
                    }
                });
            }
        });
    }

    // Notifications
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        // Add styles
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '16px 24px',
            borderRadius: '8px',
            background: type === 'success' ? '#4ade80' : type === 'error' ? '#f87171' : '#60a5fa',
            color: 'white',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
            zIndex: '9999',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontSize: '16px',
            fontWeight: '500',
            transform: 'translateX(400px)',
            transition: 'transform 0.3s ease'
        });

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // Add CSS for spinner and other dynamic elements
    function addDynamicStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .processing-state,
            .success-state {
                text-align: center;
                color: white;
            }

            .spinner {
                width: 60px;
                height: 60px;
                margin: 0 auto 20px;
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-top-color: white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            .progress-bar {
                width: 100%;
                height: 6px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                margin-top: 20px;
                overflow: hidden;
            }

            .progress-fill {
                height: 100%;
                background: white;
                border-radius: 3px;
                width: 0%;
                transition: width 0.3s ease;
            }

            .download-buttons {
                display: flex;
                gap: 16px;
                justify-content: center;
                margin: 24px 0;
            }

            .download-btn {
                background: white;
                color: #00bfa5;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                border: none;
                outline: none;
            }

            .download-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }

            .download-btn:active {
                transform: translateY(0);
            }

            .convert-another-btn {
                background: transparent;
                color: white;
                border: 2px solid white;
                padding: 10px 24px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                outline: none;
            }

            .convert-another-btn:hover {
                background: white;
                color: #00bfa5;
            }

            .notification-content {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            /* Prevent parent click handlers in success state */
            .success-state {
                pointer-events: all;
            }
            
            .success-state * {
                pointer-events: all;
            }
        `;
        document.head.appendChild(style);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            init();
            addDynamicStyles();
        });
    } else {
        init();
        addDynamicStyles();
    }

})();