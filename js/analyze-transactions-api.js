// Analyze Transactions API Integration
// Uses the unified backend for transaction analysis

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const analyzeArea = document.getElementById('analyzeArea');
    const fileInput = document.getElementById('fileInput');
    const chooseFilesBtn = document.getElementById('chooseFilesBtn');
    const analyzeButton = document.getElementById('analyzeButton');
    const processingMessage = document.getElementById('processingMessage');
    const errorMessage = document.getElementById('errorMessage');
    const resultsSection = document.getElementById('resultsSection');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    const downloadExcelBtn = document.getElementById('downloadExcelBtn');
    
    let selectedFile = null;
    let currentTransactions = [];
    
    // File selection
    chooseFilesBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        fileInput.click();
    });
    
    analyzeArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            const fileName = selectedFile.name;
            chooseFilesBtn.innerHTML = `<i class="fas fa-check"></i> ${fileName}`;
            analyzeArea.style.borderColor = 'rgba(255, 255, 255, 0.8)';
            analyzeButton.classList.add('enabled');
        }
    });
    
    // Drag and drop
    analyzeArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.transform = 'scale(1.05)';
        this.style.borderColor = 'white';
    });
    
    analyzeArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.style.transform = 'scale(1.02)';
        this.style.borderColor = 'rgba(255, 255, 255, 0.5)';
    });
    
    analyzeArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.transform = 'scale(1.02)';
        this.style.borderColor = 'rgba(255, 255, 255, 0.8)';
        
        if (e.dataTransfer.files.length > 0) {
            selectedFile = e.dataTransfer.files[0];
            fileInput.files = e.dataTransfer.files;
            const fileName = selectedFile.name;
            chooseFilesBtn.innerHTML = `<i class="fas fa-check"></i> ${fileName}`;
            analyzeButton.classList.add('enabled');
        }
    });
    
    // Analyze button click
    analyzeButton.addEventListener('click', async function() {
        if (!selectedFile) return;
        
        // Hide error and results
        errorMessage.style.display = 'none';
        resultsSection.style.display = 'none';
        
        // Show processing
        processingMessage.style.display = 'block';
        analyzeButton.style.display = 'none';
        
        try {
            // Create form data
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            // Send to backend
            const response = await fetch(API_CONFIG.getUrl('/api/analyze-transactions'), {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Store transactions for export
                currentTransactions = data.transactions || [];
                displayResults(data.analysis);
                resultsSection.style.display = 'block';
            } else {
                throw new Error(data.detail || 'Failed to analyze transactions');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            
            // Check if it's a connection error
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage.innerHTML = `
                    <strong>Backend API Connection Error</strong><br>
                    The analysis backend is currently unavailable. This could mean:<br>
                    • The backend service is not running<br>
                    • Nginx is not configured to proxy /api requests<br>
                    • The backend is deployed but not accessible<br><br>
                    Please contact support or try again later.
                `;
            } else {
                errorMessage.textContent = 'Error: ' + error.message;
            }
            errorMessage.style.display = 'block';
        } finally {
            processingMessage.style.display = 'none';
            analyzeButton.style.display = 'inline-flex';
        }
    });
    
    function displayResults(analysis) {
        // Store analysis data globally for downloads
        window.currentAnalysis = analysis;
        
        // Summary cards
        document.getElementById('totalTransactions').textContent = analysis.summary.total_transactions.toLocaleString();
        document.getElementById('totalDeposits').textContent = '$' + analysis.summary.total_deposits.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById('totalWithdrawals').textContent = '$' + analysis.summary.total_withdrawals.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById('netChange').textContent = (analysis.summary.net_change >= 0 ? '+' : '') + '$' + analysis.summary.net_change.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        // Update net change color
        const netChangeElement = document.getElementById('netChange').parentElement.parentElement;
        if (analysis.summary.net_change >= 0) {
            netChangeElement.style.background = 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)';
        } else {
            netChangeElement.style.background = 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)';
        }
        
        // Categories chart
        displayCategoriesChart(analysis.categories);
        
        // Monthly breakdown
        displayMonthlyBreakdown(analysis.monthly_breakdown);
        
        // Top merchants
        displayTopMerchants(analysis.top_merchants);
        
        // Alerts
        displayAlerts(analysis.alerts);
        
        // Spending patterns
        displaySpendingPatterns(analysis.spending_patterns);
        
        // Show download buttons
        document.getElementById('downloadPdfBtn').style.display = 'inline-flex';
        document.getElementById('downloadExcelBtn').style.display = 'inline-flex';
    }
    
    function displayCategoriesChart(categories) {
        const chartContainer = document.getElementById('categoriesChart');
        chartContainer.innerHTML = '';
        
        // Sort categories by total
        const sortedCategories = Object.entries(categories)
            .filter(([_, data]) => data.total > 0)
            .sort((a, b) => b[1].total - a[1].total);
        
        if (sortedCategories.length === 0) {
            chartContainer.innerHTML = '<p style="text-align: center; color: #999;">No categorized transactions found</p>';
            return;
        }
        
        // Create simple bar chart
        const maxValue = Math.max(...sortedCategories.map(([_, data]) => data.total));
        
        sortedCategories.forEach(([category, data]) => {
            const percentage = (data.total / maxValue) * 100;
            
            const bar = document.createElement('div');
            bar.className = 'category-bar';
            bar.innerHTML = `
                <div class="category-label">${category}</div>
                <div class="category-progress">
                    <div class="category-fill" style="width: ${percentage}%"></div>
                </div>
                <div class="category-amount">$${data.total.toFixed(2)} (${data.count})</div>
            `;
            chartContainer.appendChild(bar);
        });
    }
    
    function displayMonthlyBreakdown(monthlyData) {
        const container = document.getElementById('monthlyBreakdown');
        container.innerHTML = '';
        
        if (Object.keys(monthlyData).length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #999;">No monthly data available</p>';
            return;
        }
        
        Object.entries(monthlyData).forEach(([month, data]) => {
            const monthCard = document.createElement('div');
            monthCard.className = 'month-card';
            monthCard.innerHTML = `
                <h4>${month}</h4>
                <div class="month-stats">
                    <div><strong>Total:</strong> $${data.total.toFixed(2)}</div>
                    <div><strong>Count:</strong> ${data.count}</div>
                    <div><strong>Average:</strong> $${data.average.toFixed(2)}</div>
                </div>
            `;
            container.appendChild(monthCard);
        });
    }
    
    function displayTopMerchants(merchants) {
        const container = document.getElementById('topMerchants');
        container.innerHTML = '';
        
        if (merchants.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #999;">No merchant data available</p>';
            return;
        }
        
        merchants.slice(0, 5).forEach((merchant, index) => {
            const merchantItem = document.createElement('div');
            merchantItem.className = 'merchant-item';
            merchantItem.innerHTML = `
                <span class="merchant-rank">${index + 1}</span>
                <div class="merchant-info">
                    <div class="merchant-name">${merchant.merchant}</div>
                    <div class="merchant-stats">$${merchant.total_spent.toFixed(2)} • ${merchant.transaction_count} transactions</div>
                </div>
            `;
            container.appendChild(merchantItem);
        });
    }
    
    function displayAlerts(alerts) {
        const container = document.getElementById('alerts');
        container.innerHTML = '';
        
        if (alerts.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #999;">No alerts at this time</p>';
            return;
        }
        
        alerts.forEach(alert => {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${alert.type}`;
            alertDiv.innerHTML = `
                <i class="fas fa-${getAlertIcon(alert.type)}"></i>
                <div>
                    <strong>${alert.title}</strong>
                    <p>${alert.message}</p>
                </div>
            `;
            container.appendChild(alertDiv);
        });
    }
    
    function displaySpendingPatterns(patterns) {
        const container = document.getElementById('spendingPatterns');
        container.innerHTML = `
            <div class="pattern-grid">
                <div class="pattern-card">
                    <i class="fas fa-calendar-day"></i>
                    <h4>Daily Average</h4>
                    <p class="pattern-value">$${patterns.daily_average.toFixed(2)}</p>
                </div>
                <div class="pattern-card">
                    <i class="fas fa-chart-bar"></i>
                    <h4>Weekend vs Weekday</h4>
                    <p class="pattern-value">
                        Weekend: $${patterns.weekend_vs_weekday.weekend.toFixed(2)}<br>
                        Weekday: $${patterns.weekend_vs_weekday.weekday.toFixed(2)}
                    </p>
                </div>
                ${patterns.largest_expense ? `
                <div class="pattern-card">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h4>Largest Expense</h4>
                    <p class="pattern-value">$${patterns.largest_expense.amount.toFixed(2)}</p>
                    <p class="pattern-desc">${patterns.largest_expense.description}</p>
                </div>
                ` : ''}
                ${patterns.most_frequent_amount ? `
                <div class="pattern-card">
                    <i class="fas fa-redo"></i>
                    <h4>Most Frequent Amount</h4>
                    <p class="pattern-value">$${patterns.most_frequent_amount.amount.toFixed(2)}</p>
                    <p class="pattern-desc">${patterns.most_frequent_amount.count} times</p>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    function getAlertIcon(type) {
        switch(type) {
            case 'success': return 'check-circle';
            case 'warning': return 'exclamation-triangle';
            case 'danger': return 'times-circle';
            case 'info': return 'info-circle';
            default: return 'info-circle';
        }
    }
    
    // Download PDF button
    downloadPdfBtn.addEventListener('click', async function() {
        if (!window.currentAnalysis) return;
        
        try {
            downloadPdfBtn.disabled = true;
            downloadPdfBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';
            
            const response = await fetch(API_CONFIG.getUrl('/api/generate-pdf-report'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(window.currentAnalysis)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `financial_analysis_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                throw new Error('Failed to generate PDF');
            }
        } catch (error) {
            console.error('PDF download error:', error);
            alert('Error generating PDF report: ' + error.message);
        } finally {
            downloadPdfBtn.disabled = false;
            downloadPdfBtn.innerHTML = '<i class="fas fa-download"></i> Download PDF';
        }
    });
    
    // Download Excel button
    downloadExcelBtn.addEventListener('click', async function() {
        if (!window.currentAnalysis) return;
        
        try {
            downloadExcelBtn.disabled = true;
            downloadExcelBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Excel...';
            
            const response = await fetch(API_CONFIG.getUrl('/api/generate-excel-report'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    analysis: window.currentAnalysis,
                    transactions: currentTransactions
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `financial_analysis_${new Date().toISOString().split('T')[0]}.xlsx`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                throw new Error('Failed to generate Excel');
            }
        } catch (error) {
            console.error('Excel download error:', error);
            alert('Error generating Excel report: ' + error.message);
        } finally {
            downloadExcelBtn.disabled = false;
            downloadExcelBtn.innerHTML = '<i class="fas fa-download"></i> Download Excel';
        }
    });
});

// Add required styles
const style = document.createElement('style');
style.textContent = `
.category-bar {
    margin-bottom: 15px;
}

.category-label {
    font-weight: 600;
    margin-bottom: 5px;
}

.category-progress {
    background: #e9ecef;
    height: 25px;
    border-radius: 4px;
    overflow: hidden;
}

.category-fill {
    background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
    height: 100%;
    transition: width 0.5s ease;
}

.category-amount {
    text-align: right;
    font-size: 0.875rem;
    color: #6c757d;
    margin-top: 5px;
}

.month-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 15px;
}

.month-card h4 {
    margin: 0 0 10px 0;
    color: #1a1a1a;
}

.month-stats {
    display: grid;
    gap: 5px;
    font-size: 0.875rem;
}

.merchant-item {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
    margin-bottom: 10px;
}

.merchant-rank {
    font-size: 1.5rem;
    font-weight: 700;
    color: #4facfe;
    min-width: 30px;
}

.merchant-info {
    flex: 1;
}

.merchant-name {
    font-weight: 600;
    margin-bottom: 5px;
}

.merchant-stats {
    font-size: 0.875rem;
    color: #6c757d;
}

.alert {
    display: flex;
    align-items: start;
    gap: 15px;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
}

.alert i {
    font-size: 1.25rem;
    margin-top: 2px;
}

.alert-success {
    background: #d4edda;
    color: #155724;
}

.alert-warning {
    background: #fff3cd;
    color: #856404;
}

.alert-danger {
    background: #f8d7da;
    color: #721c24;
}

.alert-info {
    background: #d1ecf1;
    color: #0c5460;
}

.pattern-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
}

.pattern-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}

.pattern-card i {
    font-size: 2rem;
    color: #4facfe;
    margin-bottom: 10px;
}

.pattern-card h4 {
    margin: 10px 0;
    font-size: 1rem;
}

.pattern-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1a1a1a;
    margin: 5px 0;
}

.pattern-desc {
    font-size: 0.875rem;
    color: #6c757d;
    margin-top: 5px;
}

.analyzeButton.enabled {
    opacity: 1 !important;
    pointer-events: auto !important;
}
`;
document.head.appendChild(style);