// Bank Statement Converter - SEO Optimized JavaScript
// Minimal JavaScript for better page speed scores

document.addEventListener('DOMContentLoaded', function() {
    // Core upload functionality
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    
    if (uploadBtn && fileInput) {
        // Click to upload
        uploadBtn.addEventListener('click', () => {
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
    }
    
    // Drag and drop functionality
    if (uploadArea) {
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
            if (files.length > 0 && files[0].type === 'application/pdf') {
                handleFile(files[0]);
            } else if (files.length > 0 && files[0].type !== 'application/pdf') {
                alert('Please upload a PDF file');
            }
        });
    }
    
    // Handle file upload
    async function handleFile(file) {
        // Get UI elements
        const initialState = document.getElementById('initialState');
        const processingState = document.getElementById('processingState');
        const successState = document.getElementById('successState');
        
        // Show processing state
        if (initialState) initialState.style.display = 'none';
        if (processingState) processingState.classList.add('active');
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('http://localhost:5000/api/convert', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Show success state
                if (processingState) processingState.classList.remove('active');
                if (successState) successState.classList.add('active');
                
                // Store the download URL
                window.convertedFileUrl = data.csv_file;
                
                // Setup download button
                const downloadBtn = document.getElementById('downloadBtn');
                if (downloadBtn) {
                    downloadBtn.onclick = () => {
                        if (window.convertedFileUrl) {
                            window.location.href = `http://localhost:5000${window.convertedFileUrl}`;
                        }
                    };
                }
                
                // Track conversion in analytics
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'conversion', {
                        'event_category': 'engagement',
                        'event_label': data.bank_name || 'unknown'
                    });
                }
            } else {
                throw new Error(data.error || 'Conversion failed');
            }
        } catch (error) {
            if (processingState) processingState.classList.remove('active');
            if (initialState) initialState.style.display = 'block';
            alert('Error: ' + error.message);
        }
    }
    
    // Convert another button
    const convertAnotherBtn = document.getElementById('convertAnotherBtn');
    if (convertAnotherBtn) {
        convertAnotherBtn.addEventListener('click', () => {
            const successState = document.getElementById('successState');
            const initialState = document.getElementById('initialState');
            
            if (successState) successState.classList.remove('active');
            if (initialState) initialState.style.display = 'block';
            if (fileInput) fileInput.value = '';
            window.convertedFileUrl = null;
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Lazy load images for better performance
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
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
});

// Google Analytics (add your tracking ID)
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'GA_TRACKING_ID');