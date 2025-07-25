        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing upload functionality');
            
            const uploadArea = document.getElementById('uploadArea');
            const uploadBtn = document.getElementById('uploadBtn');
            const fileInput = document.getElementById('fileInput');
            const initialState = document.getElementById('initialState');
            const processingState = document.getElementById('processingState');
            const successState = document.getElementById('successState');
            const downloadBtn = document.getElementById('downloadBtn');
            const convertAnother = document.getElementById('convertAnother');
            const errorMessage = document.getElementById('errorMessage');
            
            // Check if elements exist
            if (!uploadBtn) {
                console.error('Upload button not found!');
                return;
            }
            if (!fileInput) {
                console.error('File input not found!');
                return;
            }
        
        // Mobile menu toggle
        const menuToggle = document.querySelector('.menu-toggle');
        const navMenu = document.querySelector('.nav-menu');
        
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });
        
        // Close menu when clicking on a link
        document.querySelectorAll('.nav-menu a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
            });
        });
        
        // Upload button click
        uploadBtn.addEventListener('click', () => {
            console.log('Upload button clicked');
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            console.log('File input changed', e.target.files);
            handleFile(e);
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragging');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragging');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragging');
            
            const files = e.dataTransfer.files;
            console.log('Files dropped:', files);
            if (files.length > 0) {
                if (files[0].type === 'application/pdf') {
                    handleFile({ target: { files: files } });
                } else {
                    showError('Please drop a PDF file');
                }
            }
        });
        
        // Convert another button
        convertAnother.addEventListener('click', () => {
            fileInput.value = '';
            showInitialState();
        });
        
        // Handle file upload
        function handleFile(e) {
            console.log('handleFile called', e);
            const file = e.target.files[0];
            console.log('Selected file:', file);
            
            if (!file) {
                showError('No file selected');
                return;
            }
            
            if (file.type !== 'application/pdf') {
                showError('Please select a PDF file. You selected: ' + file.type);
                return;
            }
            
            console.log('Uploading file:', file.name);
            uploadFile(file);
        }
        
        // Upload file to server
        async function uploadFile(file) {
            console.log('uploadFile called with:', file.name);
            showProcessingState();
            
            // Simulate processing delay
            setTimeout(() => {
                console.log('Processing complete');
                // For demo purposes, create a sample CSV download
                const sampleCSV = `Date,Description,Debit,Credit,Balance
2024-01-01,"Beginning Balance",,,5000.00
2024-01-02,"Amazon Purchase",45.99,,4954.01
2024-01-03,"Salary Deposit",,3500.00,8454.01
2024-01-05,"Grocery Store",125.50,,8328.51
2024-01-07,"Utility Bill",89.00,,8239.51
2024-01-10,"ATM Withdrawal",200.00,,8039.51
2024-01-12,"Restaurant",65.00,,7974.51
2024-01-15,"Online Transfer",,500.00,8474.51
2024-01-18,"Gas Station",45.00,,8429.51
2024-01-20,"Subscription Service",12.99,,8416.52`;
                
                const blob = new Blob([sampleCSV], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                showSuccessState(url);
            }, 2000);
            
            // In production, this would connect to a real API:
            /*
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/convert', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) throw new Error('Conversion failed');
                
                const data = await response.json();
                showSuccessState(data.csv_file);
                
            } catch (error) {
                showError('Conversion failed. Please try again.');
                showInitialState();
            }
            */
        }
        
        // State management
        function showInitialState() {
            initialState.style.display = 'block';
            processingState.style.display = 'none';
            successState.style.display = 'none';
            errorMessage.style.display = 'none';
        }
        
        function showProcessingState() {
            initialState.style.display = 'none';
            processingState.style.display = 'block';
            successState.style.display = 'none';
            errorMessage.style.display = 'none';
        }
        
        function showSuccessState(downloadUrl) {
            initialState.style.display = 'none';
            processingState.style.display = 'none';
            successState.style.display = 'block';
            downloadBtn.href = downloadUrl;
            downloadBtn.download = 'bank_statement_converted.csv';
        }
        
        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
        }
        
        // Mobile menu JavaScript
        const menuToggle = document.querySelector('.menu-toggle');
        const navMenu = document.querySelector('.nav-menu');
        
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });
        
        // Close menu when clicking on a link
        document.querySelectorAll('.nav-menu a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
            });
        });
        }); // End of DOMContentLoaded
