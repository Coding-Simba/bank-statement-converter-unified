// Modern Homepage JavaScript

(function() {
    'use strict';

    // DOM Elements
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const chooseFilesBtn = document.getElementById('chooseFilesBtn');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileMenu = document.getElementById('mobileMenu');

    // Initialize
    function init() {
        setupFileUpload();
        setupMobileMenu();
        setupSmoothScroll();
        setupDropdowns();
    }

    // File Upload Functionality
    function setupFileUpload() {
        if (!uploadBox || !fileInput || !chooseFilesBtn) return;

        // Click to upload
        chooseFilesBtn.addEventListener('click', (e) => {
            e.preventDefault();
            fileInput.click();
        });

        uploadBox.addEventListener('click', (e) => {
            // Don't trigger file input if we're in success state or clicking buttons
            if (e.target === chooseFilesBtn || chooseFilesBtn.contains(e.target)) return;
            if (uploadBox.querySelector('.success-state')) return;
            if (e.target.classList.contains('download-btn') || e.target.closest('.download-btn')) return;
            fileInput.click();
        });

        // File input change
        fileInput.addEventListener('change', handleFileSelect);

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

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        uploadBox.classList.add('dragover');
    }

    function unhighlight(e) {
        uploadBox.classList.remove('dragover');
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
        // Reset processed statements
        window.processedStatements = [];
        
        // Handle multiple files
        const fileArray = [...files];
        if (fileArray.length > 1) {
            // Store pending files
            window.pendingFiles = fileArray.slice(1);
            // Process first file
            processFile(fileArray[0]);
        } else {
            // Single file
            processFile(fileArray[0]);
        }
    }

    async function processFile(file) {
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

        try {
            // Create FormData
            const formData = new FormData();
            formData.append('file', file);

            // Add timeout for long conversions
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

            // Call API to convert
            const response = await fetch(API_CONFIG.getUrl('/api/convert'), {
                method: 'POST',
                body: formData,
                credentials: 'include',
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Conversion failed');
            }

            const result = await response.json();
            
            // Store processed files for multi-file support
            if (!window.processedStatements) {
                window.processedStatements = [];
            }
            window.processedStatements.push(result);

            // If there are more files to process, wait for all
            // Otherwise redirect immediately
            if (window.pendingFiles && window.pendingFiles.length > 0) {
                // Process next file
                const nextFile = window.pendingFiles.shift();
                processFile(nextFile);
            } else {
                // All files processed, redirect to results
                redirectToResults();
            }

        } catch (error) {
            console.error('Conversion error:', error);
            resetUploadBox();
            
            if (error.name === 'AbortError') {
                showNotification('Conversion timed out. Please try with a smaller file.', 'error');
            } else {
                showNotification(error.message || 'Conversion failed. Please try again.', 'error');
            }
        }
    }

    function showProcessingState(file) {
        const uploadContent = uploadBox.innerHTML;
        uploadBox.setAttribute('data-original-content', uploadContent);
        
        uploadBox.innerHTML = `
            <div class="processing-state">
                <div class="spinner"></div>
                <h3>Processing ${file.name}</h3>
                <p>Converting your bank statement...</p>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
        `;

        // Animate progress bar
        const progressFill = uploadBox.querySelector('.progress-fill');
        let progress = 0;
        const progressText = uploadBox.querySelector('p');
        const interval = setInterval(() => {
            progress += 10;
            progressFill.style.width = progress + '%';
            
            // Update status text
            if (progress >= 60 && progress < 90) {
                progressText.textContent = 'Extracting transactions...';
            } else if (progress >= 90) {
                progressText.textContent = 'Finalizing conversion...';
                clearInterval(interval);
            }
        }, 180);
    }

    function showSuccessState(file) {
        uploadBox.innerHTML = `
            <div class="success-state">
                <i class="fas fa-check-circle" style="font-size: 3rem; color: #4ade80; margin-bottom: 1rem;"></i>
                <h3>Conversion Complete!</h3>
                <p>${file.name} has been converted successfully.</p>
                <div class="download-buttons" onclick="event.stopPropagation();">
                    <button class="download-btn csv-btn" data-format="csv" type="button">
                        <i class="fas fa-file-csv"></i> Download CSV
                    </button>
                    <button class="download-btn excel-btn" data-format="excel" type="button">
                        <i class="fas fa-file-excel"></i> Download Excel
                    </button>
                </div>
                <button class="convert-another-btn">Convert Another File</button>
            </div>
        `;

        // Add event listeners
        const convertAnotherBtn = uploadBox.querySelector('.convert-another-btn');
        convertAnotherBtn.addEventListener('click', resetUploadBox);

        // Add download functionality
        const csvBtn = uploadBox.querySelector('.csv-btn');
        const excelBtn = uploadBox.querySelector('.excel-btn');
        
        csvBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            downloadFile(file, 'csv');
        });
        
        excelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            downloadFile(file, 'excel');
        });
    }

    function resetUploadBox() {
        const originalContent = uploadBox.getAttribute('data-original-content');
        uploadBox.innerHTML = originalContent;
        setupFileUpload(); // Re-initialize event listeners
    }

    function redirectToResults() {
        if (!window.processedStatements || window.processedStatements.length === 0) {
            return;
        }

        // Single file - use simple URL
        if (window.processedStatements.length === 1) {
            window.location.href = window.processedStatements[0].results_url;
        } else {
            // Multiple files - use query parameter
            const ids = window.processedStatements.map(s => s.id).join(',');
            window.location.href = `/results?ids=${ids}`;
        }
    }

    // Download functionality
    function downloadFile(originalFile, format) {
        const fileName = originalFile.name.replace(/\.[^/.]+$/, '');
        const convertedFileName = `${fileName}_converted.${format === 'csv' ? 'csv' : 'xlsx'}`;
        
        if (format === 'csv') {
            downloadCSV(convertedFileName);
        } else {
            downloadExcel(convertedFileName);
        }
        
        showNotification(`Downloading ${convertedFileName}`, 'success');
    }

    function downloadCSV(filename) {
        // Sample CSV data - in production this would come from the API
        const csvContent = `Date,Description,Amount,Balance
2024-01-15,Opening Balance,0.00,5000.00
2024-01-16,Grocery Store,-45.32,4954.68
2024-01-17,Salary Deposit,3500.00,8454.68
2024-01-18,Electric Bill,-125.00,8329.68
2024-01-19,Gas Station,-65.45,8264.23
2024-01-20,Restaurant,-82.50,8181.73
2024-01-21,ATM Withdrawal,-200.00,7981.73
2024-01-22,Online Transfer,-500.00,7481.73
2024-01-23,Coffee Shop,-12.75,7468.98
2024-01-24,Pharmacy,-28.90,7440.08`;

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
    }

    function downloadExcel(filename) {
        // For Excel, we'll create a simple HTML table that Excel can read
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
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
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
            }

            .download-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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