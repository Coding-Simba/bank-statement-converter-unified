// Results Overview JavaScript
(function() {
    'use strict';

    // State management
    let currentStatementId = null;
    let currentPage = 1;
    let totalPages = 1;
    let statements = [];
    let activeStatementIndex = 0;

    // Initialize
    document.addEventListener('DOMContentLoaded', () => {
        // Extract statement ID(s) from URL
        const urlParams = new URLSearchParams(window.location.search);
        const pathParts = window.location.pathname.split('/');
        
        if (pathParts[1] === 'results' && pathParts[2]) {
            // Single statement ID from path
            currentStatementId = pathParts[2];
            statements = [{ id: currentStatementId }];
        } else if (urlParams.has('ids')) {
            // Multiple statement IDs from query param
            const ids = urlParams.get('ids').split(',');
            statements = ids.map(id => ({ id }));
            currentStatementId = statements[0].id;
            
            // Show file tabs
            if (statements.length > 1) {
                showFileTabs();
            }
        } else {
            showError('No statement ID provided');
            return;
        }

        // Load first statement
        loadStatementData();

        // Setup event listeners
        setupEventListeners();
    });

    // Setup event listeners
    function setupEventListeners() {
        // Download buttons
        document.getElementById('downloadCSV').addEventListener('click', () => {
            downloadFile('csv');
        });

        document.getElementById('downloadMarkdown').addEventListener('click', () => {
            downloadFile('markdown');
        });
    }

    // Load statement data
    async function loadStatementData() {
        try {
            showLoading();

            const response = await fetch(
                `${API_CONFIG.getUrl('/api/statement/' + currentStatementId + '/transactions')}?page=${currentPage}&per_page=50`,
                {
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to load statement data');
            }

            const data = await response.json();
            
            // Store statement data
            statements[activeStatementIndex] = {
                ...statements[activeStatementIndex],
                data: data,
                currentPage: currentPage
            };

            // Update UI
            displayResults(data);

        } catch (error) {
            console.error('Error loading statement:', error);
            showError(error.message);
        }
    }

    // Display results
    function displayResults(data) {
        // Hide loading, show content
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('resultsContent').style.display = 'block';

        // Update statistics
        updateStatistics(data.statistics);

        // Display transactions
        displayTransactions(data.transactions);

        // Setup pagination
        setupPagination(data.pagination);
    }

    // Update statistics cards
    function updateStatistics(stats) {
        document.getElementById('statBank').textContent = stats.bank_name;
        document.getElementById('statTotal').textContent = stats.total_transactions.toLocaleString();
        
        // Format date range
        if (stats.date_range.start && stats.date_range.end) {
            document.getElementById('statDateRange').textContent = 
                `${formatDate(stats.date_range.start)} - ${formatDate(stats.date_range.end)}`;
        } else {
            document.getElementById('statDateRange').textContent = 'N/A';
        }

        document.getElementById('statFilename').textContent = stats.original_filename;
    }

    // Display transactions in table
    function displayTransactions(transactions) {
        const tbody = document.getElementById('transactionsBody');
        tbody.innerHTML = '';

        if (transactions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="no-data">No transactions found</td>
                </tr>
            `;
            return;
        }

        transactions.forEach(trans => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="date-col">${formatDate(trans.date)}</td>
                <td class="desc-col">${escapeHtml(trans.description)}</td>
                <td class="amount-col ${trans.amount < 0 ? 'negative' : 'positive'}">
                    ${formatCurrency(trans.amount)}
                </td>
                <td class="balance-col">${formatCurrency(trans.balance)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    // Setup pagination controls
    function setupPagination(pagination) {
        totalPages = pagination.total_pages;
        currentPage = pagination.page;

        const paginationDiv = document.getElementById('pagination');
        paginationDiv.innerHTML = '';

        if (totalPages <= 1) return;

        // Previous button
        if (currentPage > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.className = 'pagination-btn';
            prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i> Previous';
            prevBtn.onclick = () => changePage(currentPage - 1);
            paginationDiv.appendChild(prevBtn);
        }

        // Page numbers
        const pageInfo = document.createElement('span');
        pageInfo.className = 'page-info';
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        paginationDiv.appendChild(pageInfo);

        // Next button
        if (currentPage < totalPages) {
            const nextBtn = document.createElement('button');
            nextBtn.className = 'pagination-btn';
            nextBtn.innerHTML = 'Next <i class="fas fa-chevron-right"></i>';
            nextBtn.onclick = () => changePage(currentPage + 1);
            paginationDiv.appendChild(nextBtn);
        }
    }

    // Change page
    function changePage(page) {
        currentPage = page;
        loadStatementData();
    }

    // Show file tabs for multiple files
    function showFileTabs() {
        const tabsDiv = document.getElementById('fileTabs');
        tabsDiv.style.display = 'flex';
        tabsDiv.innerHTML = '';

        statements.forEach((stmt, index) => {
            const tab = document.createElement('button');
            tab.className = `file-tab ${index === activeStatementIndex ? 'active' : ''}`;
            tab.innerHTML = `
                <i class="fas fa-file-pdf"></i>
                <span>File ${index + 1}</span>
            `;
            tab.onclick = () => switchToStatement(index);
            tabsDiv.appendChild(tab);
        });
    }

    // Switch to different statement
    function switchToStatement(index) {
        if (index === activeStatementIndex) return;

        // Update active state
        activeStatementIndex = index;
        currentStatementId = statements[index].id;
        currentPage = statements[index].currentPage || 1;

        // Update tabs UI
        document.querySelectorAll('.file-tab').forEach((tab, i) => {
            tab.classList.toggle('active', i === index);
        });

        // Load data if not cached
        if (statements[index].data) {
            displayResults(statements[index].data);
        } else {
            loadStatementData();
        }
    }

    // Download file
    async function downloadFile(format) {
        try {
            const endpoint = format === 'csv' 
                ? `/api/statement/${currentStatementId}/download`
                : `/api/statement/${currentStatementId}/download/markdown`;

            const response = await fetch(API_CONFIG.getUrl(endpoint), {
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Download failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Get filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `statement.${format === 'csv' ? 'csv' : 'md'}`;
            if (contentDisposition) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
                if (matches && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            // Show success notification
            if (window.UINotification) {
                UINotification.show(`Downloading ${filename}`, 'success');
            }

        } catch (error) {
            console.error('Download error:', error);
            if (window.UINotification) {
                UINotification.show('Download failed', 'error');
            }
        }
    }

    // Utility functions
    function formatDate(dateStr) {
        if (!dateStr || dateStr === 'N/A') return 'N/A';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showLoading() {
        document.getElementById('loadingState').style.display = 'flex';
        document.getElementById('errorState').style.display = 'none';
        document.getElementById('resultsContent').style.display = 'none';
    }

    function showError(message) {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('errorState').style.display = 'flex';
        document.getElementById('resultsContent').style.display = 'none';
        document.getElementById('errorMessage').textContent = message;
    }

})();