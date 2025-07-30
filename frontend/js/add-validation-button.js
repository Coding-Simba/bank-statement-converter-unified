/**
 * Simple script to add validation button to conversion results
 * This integrates with the existing upload flow
 */

(function() {
    // Override the showConversionResult function if it exists
    const originalShowResult = window.showConversionResult;
    
    window.showConversionResult = function(data) {
        // Call original if exists
        if (originalShowResult) {
            originalShowResult(data);
        }
        
        // Add validation button after a short delay
        setTimeout(() => {
            addValidationOption(data);
        }, 100);
    };
    
    // Also hook into any AJAX success handlers
    if (window.jQuery || window.$) {
        $(document).ajaxSuccess(function(event, xhr, settings) {
            if (settings.url && settings.url.includes('/api/convert')) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response && response.id) {
                        setTimeout(() => {
                            addValidationOption(response);
                        }, 500);
                    }
                } catch (e) {
                    console.error('Error parsing response:', e);
                }
            }
        });
    }
    
    // Function to add validation button
    function addValidationOption(data) {
        if (!data || !data.id) return;
        
        // Find result container
        const containers = [
            '.conversion-result',
            '.upload-result', 
            '#uploadResult',
            '#conversionResult',
            '.result-container',
            '.file-result'
        ];
        
        let resultContainer = null;
        for (const selector of containers) {
            resultContainer = document.querySelector(selector);
            if (resultContainer) break;
        }
        
        if (!resultContainer) {
            console.log('No result container found');
            return;
        }
        
        // Check if validation button already added
        if (resultContainer.querySelector('.validation-option')) {
            return;
        }
        
        // Create validation section
        const validationDiv = document.createElement('div');
        validationDiv.className = 'validation-option';
        validationDiv.style.cssText = `
            margin-top: 20px;
            padding: 20px;
            background: #f0f4ff;
            border: 1px solid #d0d9ff;
            border-radius: 8px;
            text-align: center;
        `;
        
        validationDiv.innerHTML = `
            <h3 style="margin: 0 0 10px 0; color: #4a5568; font-size: 18px;">
                <i class="fas fa-check-circle" style="color: #667eea;"></i>
                Want to Review Transactions?
            </h3>
            <p style="margin: 0 0 15px 0; color: #718096;">
                Review and edit transaction details before downloading
            </p>
            <button onclick="window.open('/validation.html?id=${data.id}', '_blank')" 
                    style="background: #667eea; color: white; border: none; padding: 10px 20px; 
                           border-radius: 6px; cursor: pointer; font-size: 16px;">
                <i class="fas fa-edit"></i> Validate & Edit Transactions
            </button>
        `;
        
        // Add to result container
        resultContainer.appendChild(validationDiv);
        
        // Also update download button text if exists
        const downloadBtn = resultContainer.querySelector('a[download], .download-btn, button[onclick*="download"]');
        if (downloadBtn && !downloadBtn.textContent.includes('without')) {
            downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download CSV (without validation)';
        }
    }
    
    // Listen for custom events that might indicate conversion complete
    document.addEventListener('conversionComplete', function(e) {
        if (e.detail && e.detail.statementId) {
            addValidationOption({ id: e.detail.statementId });
        }
    });
    
    // Mutation observer to catch dynamically added results
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    // Check if it's a result container
                    if (node.classList && (
                        node.classList.contains('conversion-result') ||
                        node.classList.contains('upload-result') ||
                        node.classList.contains('result-container')
                    )) {
                        // Look for statement ID in the node
                        const downloadLink = node.querySelector('a[href*="/api/statement/"]');
                        if (downloadLink) {
                            const match = downloadLink.href.match(/statement\/(\d+)/);
                            if (match) {
                                addValidationOption({ id: match[1] });
                            }
                        }
                    }
                }
            });
        });
    });
    
    // Start observing when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            observer.observe(document.body, { childList: true, subtree: true });
        });
    } else {
        observer.observe(document.body, { childList: true, subtree: true });
    }
})();