/**
 * Validation Integration for Bank Statement Converter
 * Adds validation button to conversion results
 */

// Add validation button to conversion results
function addValidationButton(statementId, containerElement) {
    const validationSection = document.createElement('div');
    validationSection.className = 'validation-section';
    validationSection.innerHTML = `
        <div class="validation-prompt">
            <i class="fas fa-exclamation-circle"></i>
            <p>Want to review and edit transactions before downloading?</p>
            <button class="btn btn-primary" onclick="openValidation(${statementId})">
                <i class="fas fa-check-circle"></i> Validate Transactions
            </button>
        </div>
    `;
    
    containerElement.appendChild(validationSection);
}

// Open validation page
function openValidation(statementId) {
    // Save current statement ID
    localStorage.setItem('current_statement_id', statementId);
    
    // Open validation page in new tab or same window
    window.open(`/validation.html?id=${statementId}`, '_blank');
}

// Update the file upload success handler
function enhanceUploadSuccess() {
    // Find the original success handler and wrap it
    const originalHandler = window.handleUploadSuccess;
    
    window.handleUploadSuccess = function(response) {
        // Call original handler if exists
        if (originalHandler) {
            originalHandler(response);
        }
        
        // Add validation option if we have a statement ID
        if (response && response.id) {
            // Wait a bit for DOM to update
            setTimeout(() => {
                const resultContainer = document.querySelector('.conversion-result, .upload-result, #conversionResult');
                if (resultContainer) {
                    addValidationButton(response.id, resultContainer);
                }
            }, 500);
        }
    };
}

// Add styles for validation section
const validationStyles = `
<style>
.validation-section {
    margin-top: 2rem;
    padding: 1.5rem;
    background: #f8f9ff;
    border: 1px solid #e0e7ff;
    border-radius: 8px;
    text-align: center;
}

.validation-prompt {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
}

.validation-prompt i {
    font-size: 2rem;
    color: #667eea;
}

.validation-prompt p {
    margin: 0;
    color: #4a5568;
    font-size: 1rem;
}

.validation-prompt .btn {
    margin-top: 0.5rem;
}

/* Integration with existing result display */
.conversion-result.with-validation {
    padding-bottom: 0;
}

/* History page integration */
.statement-row .actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.statement-row .validate-btn {
    padding: 0.25rem 0.75rem;
    font-size: 0.875rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.statement-row .validate-btn:hover {
    background: #5a67d8;
}

.statement-row .validated-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    background: #c6f6d5;
    color: #276749;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}

.statement-row .validated-badge i {
    font-size: 0.875rem;
}
</style>
`;

// Add validation to statement history
function enhanceStatementHistory() {
    // Check if we're on a page with statement history
    const historyTable = document.querySelector('.statements-table, #statementsTable');
    if (!historyTable) return;
    
    // Add validation column header if not exists
    const headerRow = historyTable.querySelector('thead tr');
    if (headerRow && !headerRow.querySelector('.validation-header')) {
        const validationHeader = document.createElement('th');
        validationHeader.className = 'validation-header';
        validationHeader.textContent = 'Validation';
        headerRow.appendChild(validationHeader);
    }
    
    // Add validation status/button to each row
    const rows = historyTable.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const statementId = row.dataset.statementId;
        if (!statementId) return;
        
        // Check if already has validation cell
        if (row.querySelector('.validation-cell')) return;
        
        const validationCell = document.createElement('td');
        validationCell.className = 'validation-cell';
        
        // Check if statement is validated (would need API call)
        const isValidated = row.dataset.validated === 'true';
        
        if (isValidated) {
            validationCell.innerHTML = `
                <span class="validated-badge">
                    <i class="fas fa-check-circle"></i>
                    Validated
                </span>
            `;
        } else {
            validationCell.innerHTML = `
                <button class="validate-btn" onclick="openValidation(${statementId})">
                    <i class="fas fa-check"></i> Validate
                </button>
            `;
        }
        
        row.appendChild(validationCell);
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add styles
    document.head.insertAdjacentHTML('beforeend', validationStyles);
    
    // Enhance upload success handler
    enhanceUploadSuccess();
    
    // Enhance statement history if present
    enhanceStatementHistory();
    
    // Re-run history enhancement when navigating
    if (window.addEventListener) {
        window.addEventListener('popstate', enhanceStatementHistory);
    }
});

// Export functions for use in other scripts
window.ValidationIntegration = {
    addValidationButton,
    openValidation,
    enhanceStatementHistory
};