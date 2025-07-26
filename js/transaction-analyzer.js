// Transaction Analyzer Backend Functionality
// Analyzes bank statements for insights and reporting

class TransactionAnalyzer {
    constructor() {
        this.transactions = [];
        this.analysisResults = null;
        this.initializeEventListeners();
        this.loadDependencies();
    }

    async loadDependencies() {
        // Load Chart.js for visualizations
        if (!window.Chart) {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
            document.head.appendChild(script);
        }

        // Load Papa Parse for CSV parsing
        if (!window.Papa) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js';
            document.head.appendChild(script);
        }

        // Load jsPDF for PDF report generation
        if (!window.jspdf) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
            document.head.appendChild(script);
        }
    }

    initializeEventListeners() {
        const analyzeArea = document.getElementById('analyzeArea');
        const fileInput = document.getElementById('fileInput');
        const chooseFilesBtn = document.getElementById('chooseFilesBtn');

        if (analyzeArea) {
            // Drag and drop functionality
            analyzeArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                analyzeArea.classList.add('drag-over');
            });

            analyzeArea.addEventListener('dragleave', () => {
                analyzeArea.classList.remove('drag-over');
            });

            analyzeArea.addEventListener('drop', (e) => {
                e.preventDefault();
                analyzeArea.classList.remove('drag-over');
                this.handleFiles(e.dataTransfer.files);
            });

            analyzeArea.addEventListener('click', () => {
                fileInput.click();
            });
        }

        if (chooseFilesBtn) {
            chooseFilesBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
            });
        }
    }

    async handleFiles(files) {
        const file = files[0];
        if (!file) return;

        const validTypes = ['application/pdf', 'text/csv', 'image/jpeg', 'image/png'];
        if (!validTypes.includes(file.type) && !file.name.endsWith('.csv')) {
            this.showMessage('Please upload a PDF, CSV, or image file', 'error');
            return;
        }

        this.showLoadingState();

        try {
            if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
                await this.parseCSV(file);
            } else if (file.type === 'application/pdf') {
                await this.parsePDF(file);
            } else if (file.type.startsWith('image/')) {
                await this.parseImage(file);
            }

            this.analyzeTransactions();
            this.displayResults();
        } catch (error) {
            console.error('Error processing file:', error);
            this.showMessage('Error processing file. Please try again.', 'error');
        }
    }

    async parseCSV(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const csv = e.target.result;
                Papa.parse(csv, {
                    header: true,
                    complete: (results) => {
                        this.transactions = this.normalizeTransactions(results.data);
                        resolve();
                    },
                    error: reject
                });
            };
            reader.readAsText(file);
        });
    }

    async parsePDF(file) {
        // Simulate PDF parsing - in production, use PDF.js or server-side parsing
        this.showMessage('PDF parsing would require server-side processing or PDF.js library', 'info');
        this.transactions = this.generateSampleTransactions();
    }

    async parseImage(file) {
        // Simulate OCR - in production, use Tesseract.js or server-side OCR
        this.showMessage('Image OCR would require server-side processing or Tesseract.js', 'info');
        this.transactions = this.generateSampleTransactions();
    }

    normalizeTransactions(data) {
        // Normalize transaction data to standard format
        return data.map(row => ({
            date: this.parseDate(row.Date || row.date || row.Transaction_Date),
            description: row.Description || row.description || row.Merchant,
            amount: this.parseAmount(row.Amount || row.amount || row.Debit || row.Credit),
            category: this.categorizeTransaction(row.Description || row.description || ''),
            merchant: this.extractMerchant(row.Description || row.description || ''),
            type: this.parseAmount(row.Amount || row.amount || row.Debit || row.Credit) < 0 ? 'debit' : 'credit'
        })).filter(t => t.date && !isNaN(t.amount));
    }

    parseDate(dateStr) {
        if (!dateStr) return null;
        const date = new Date(dateStr);
        return isNaN(date.getTime()) ? null : date;
    }

    parseAmount(amountStr) {
        if (!amountStr) return 0;
        const amount = parseFloat(String(amountStr).replace(/[$,]/g, ''));
        return isNaN(amount) ? 0 : amount;
    }

    categorizeTransaction(description) {
        const desc = description.toLowerCase();
        const categories = {
            'Groceries': ['grocery', 'supermarket', 'whole foods', 'trader joe', 'safeway', 'kroger'],
            'Dining': ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonald', 'subway', 'pizza'],
            'Transportation': ['uber', 'lyft', 'gas', 'shell', 'chevron', 'parking', 'toll'],
            'Entertainment': ['netflix', 'spotify', 'movie', 'theater', 'concert', 'game'],
            'Utilities': ['electric', 'gas', 'water', 'internet', 'phone', 'verizon', 'at&t'],
            'Healthcare': ['pharmacy', 'doctor', 'hospital', 'clinic', 'cvs', 'walgreens'],
            'Shopping': ['amazon', 'walmart', 'target', 'mall', 'store', 'shop'],
            'Subscriptions': ['subscription', 'monthly', 'annual', 'membership']
        };

        for (const [category, keywords] of Object.entries(categories)) {
            if (keywords.some(keyword => desc.includes(keyword))) {
                return category;
            }
        }
        return 'Other';
    }

    extractMerchant(description) {
        // Simple merchant extraction - in production, use more sophisticated NLP
        const cleanDesc = description.replace(/[0-9\*\#]/g, '').trim();
        const words = cleanDesc.split(/\s+/);
        return words.slice(0, 3).join(' ');
    }

    generateSampleTransactions() {
        // Generate sample data for demonstration
        const merchants = [
            { name: 'Whole Foods Market', category: 'Groceries', avgAmount: -85 },
            { name: 'Starbucks Coffee', category: 'Dining', avgAmount: -6 },
            { name: 'Shell Gas Station', category: 'Transportation', avgAmount: -45 },
            { name: 'Netflix Subscription', category: 'Entertainment', avgAmount: -15.99 },
            { name: 'AT&T Wireless', category: 'Utilities', avgAmount: -80 },
            { name: 'Amazon.com', category: 'Shopping', avgAmount: -35 },
            { name: 'Direct Deposit', category: 'Income', avgAmount: 2500 }
        ];

        const transactions = [];
        const today = new Date();

        for (let i = 0; i < 90; i++) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);

            // Add 2-5 transactions per day
            const numTransactions = Math.floor(Math.random() * 4) + 2;
            for (let j = 0; j < numTransactions; j++) {
                const merchant = merchants[Math.floor(Math.random() * merchants.length)];
                const variance = 0.3;
                const amount = merchant.avgAmount * (1 + (Math.random() - 0.5) * variance);

                transactions.push({
                    date: date,
                    description: merchant.name,
                    amount: Math.round(amount * 100) / 100,
                    category: merchant.category,
                    merchant: merchant.name,
                    type: amount < 0 ? 'debit' : 'credit'
                });
            }
        }

        return transactions.sort((a, b) => b.date - a.date);
    }

    analyzeTransactions() {
        this.analysisResults = {
            overview: this.calculateOverview(),
            categoryBreakdown: this.analyzeCategoryBreakdown(),
            merchantAnalysis: this.analyzeMerchants(),
            recurringPayments: this.findRecurringPayments(),
            anomalies: this.detectAnomalies(),
            cashFlow: this.analyzeCashFlow(),
            savingsOpportunities: this.findSavingsOpportunities()
        };
    }

    calculateOverview() {
        const totalSpent = this.transactions
            .filter(t => t.type === 'debit')
            .reduce((sum, t) => sum + Math.abs(t.amount), 0);

        const totalIncome = this.transactions
            .filter(t => t.type === 'credit')
            .reduce((sum, t) => sum + t.amount, 0);

        const monthlyAverage = totalSpent / 3; // Assuming 3 months of data

        const topCategory = Object.entries(this.analyzeCategoryBreakdown())
            .filter(([cat]) => cat !== 'Income')
            .sort((a, b) => b[1].total - a[1].total)[0];

        const lastMonth = new Date();
        lastMonth.setMonth(lastMonth.getMonth() - 1);
        const lastMonthSpent = this.transactions
            .filter(t => t.type === 'debit' && t.date >= lastMonth)
            .reduce((sum, t) => sum + Math.abs(t.amount), 0);

        const previousMonth = new Date();
        previousMonth.setMonth(previousMonth.getMonth() - 2);
        const previousMonthSpent = this.transactions
            .filter(t => t.type === 'debit' && t.date >= previousMonth && t.date < lastMonth)
            .reduce((sum, t) => sum + Math.abs(t.amount), 0);

        const monthOverMonth = previousMonthSpent ? 
            ((lastMonthSpent - previousMonthSpent) / previousMonthSpent * 100).toFixed(1) : 0;

        return {
            totalSpent,
            totalIncome,
            monthlyAverage,
            topCategory: topCategory ? topCategory[0] : 'N/A',
            topCategoryAmount: topCategory ? topCategory[1].total : 0,
            transactionCount: this.transactions.length,
            monthOverMonth
        };
    }

    analyzeCategoryBreakdown() {
        const breakdown = {};
        
        this.transactions.forEach(t => {
            if (!breakdown[t.category]) {
                breakdown[t.category] = { total: 0, count: 0, transactions: [] };
            }
            breakdown[t.category].total += Math.abs(t.amount);
            breakdown[t.category].count++;
            breakdown[t.category].transactions.push(t);
        });

        return breakdown;
    }

    analyzeMerchants() {
        const merchants = {};
        
        this.transactions.forEach(t => {
            if (!merchants[t.merchant]) {
                merchants[t.merchant] = { total: 0, count: 0, transactions: [] };
            }
            merchants[t.merchant].total += Math.abs(t.amount);
            merchants[t.merchant].count++;
            merchants[t.merchant].transactions.push(t);
        });

        return Object.entries(merchants)
            .sort((a, b) => b[1].total - a[1].total)
            .slice(0, 10)
            .map(([name, data]) => ({ name, ...data }));
    }

    findRecurringPayments() {
        const recurring = {};
        
        // Group by merchant and amount
        this.transactions.forEach(t => {
            const key = `${t.merchant}_${Math.abs(t.amount)}`;
            if (!recurring[key]) {
                recurring[key] = [];
            }
            recurring[key].push(t);
        });

        // Find patterns (at least 2 occurrences)
        return Object.entries(recurring)
            .filter(([_, transactions]) => transactions.length >= 2)
            .map(([key, transactions]) => {
                const [merchant] = key.split('_');
                const amount = Math.abs(transactions[0].amount);
                
                // Calculate frequency
                const dates = transactions.map(t => t.date).sort((a, b) => a - b);
                const intervals = [];
                for (let i = 1; i < dates.length; i++) {
                    intervals.push((dates[i] - dates[i-1]) / (1000 * 60 * 60 * 24));
                }
                const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
                
                let frequency = 'Variable';
                if (avgInterval >= 28 && avgInterval <= 32) frequency = 'Monthly';
                else if (avgInterval >= 13 && avgInterval <= 15) frequency = 'Bi-weekly';
                else if (avgInterval >= 6 && avgInterval <= 8) frequency = 'Weekly';
                else if (avgInterval >= 365 - 10 && avgInterval <= 365 + 10) frequency = 'Annual';

                return {
                    merchant,
                    amount,
                    frequency,
                    lastDate: dates[dates.length - 1],
                    occurrences: transactions.length
                };
            })
            .filter(r => r.frequency !== 'Variable');
    }

    detectAnomalies() {
        const anomalies = [];
        
        // Calculate average and standard deviation for each merchant
        const merchantStats = {};
        this.transactions.forEach(t => {
            if (!merchantStats[t.merchant]) {
                merchantStats[t.merchant] = { amounts: [], transactions: [] };
            }
            merchantStats[t.merchant].amounts.push(Math.abs(t.amount));
            merchantStats[t.merchant].transactions.push(t);
        });

        // Find outliers
        Object.entries(merchantStats).forEach(([merchant, data]) => {
            if (data.amounts.length < 3) return;
            
            const avg = data.amounts.reduce((a, b) => a + b, 0) / data.amounts.length;
            const stdDev = Math.sqrt(
                data.amounts.reduce((sum, amount) => sum + Math.pow(amount - avg, 2), 0) / data.amounts.length
            );

            data.transactions.forEach(t => {
                const amount = Math.abs(t.amount);
                if (amount > avg + 2 * stdDev) {
                    anomalies.push({
                        transaction: t,
                        reason: 'Unusually high amount',
                        expected: avg,
                        actual: amount,
                        deviation: ((amount - avg) / avg * 100).toFixed(1) + '%'
                    });
                }
            });
        });

        // Find duplicate charges
        const recentTransactions = this.transactions.slice(0, 30);
        for (let i = 0; i < recentTransactions.length; i++) {
            for (let j = i + 1; j < Math.min(i + 5, recentTransactions.length); j++) {
                if (recentTransactions[i].merchant === recentTransactions[j].merchant &&
                    Math.abs(recentTransactions[i].amount) === Math.abs(recentTransactions[j].amount) &&
                    Math.abs(recentTransactions[i].date - recentTransactions[j].date) < 1000 * 60 * 60 * 24 * 2) {
                    anomalies.push({
                        transaction: recentTransactions[j],
                        reason: 'Possible duplicate charge',
                        relatedTransaction: recentTransactions[i]
                    });
                }
            }
        }

        return anomalies.slice(0, 10);
    }

    analyzeCashFlow() {
        const monthlyFlow = {};
        
        this.transactions.forEach(t => {
            const monthKey = `${t.date.getFullYear()}-${(t.date.getMonth() + 1).toString().padStart(2, '0')}`;
            if (!monthlyFlow[monthKey]) {
                monthlyFlow[monthKey] = { income: 0, expenses: 0, net: 0 };
            }
            
            if (t.type === 'credit') {
                monthlyFlow[monthKey].income += t.amount;
            } else {
                monthlyFlow[monthKey].expenses += Math.abs(t.amount);
            }
        });

        Object.values(monthlyFlow).forEach(month => {
            month.net = month.income - month.expenses;
        });

        return monthlyFlow;
    }

    findSavingsOpportunities() {
        const opportunities = [];
        const categoryBreakdown = this.analyzeCategoryBreakdown();

        // Dining suggestions
        if (categoryBreakdown['Dining'] && categoryBreakdown['Dining'].total > 300) {
            opportunities.push({
                category: 'Dining',
                current: categoryBreakdown['Dining'].total,
                suggestion: 'Consider meal planning to reduce dining out expenses',
                potentialSavings: categoryBreakdown['Dining'].total * 0.3
            });
        }

        // Subscription audit
        const recurring = this.findRecurringPayments();
        const monthlySubscriptions = recurring.filter(r => r.frequency === 'Monthly');
        if (monthlySubscriptions.length > 5) {
            const totalSubscriptions = monthlySubscriptions.reduce((sum, s) => sum + s.amount, 0);
            opportunities.push({
                category: 'Subscriptions',
                current: totalSubscriptions,
                suggestion: 'Review and cancel unused subscriptions',
                potentialSavings: totalSubscriptions * 0.2
            });
        }

        // Transportation
        if (categoryBreakdown['Transportation'] && categoryBreakdown['Transportation'].total > 200) {
            opportunities.push({
                category: 'Transportation',
                current: categoryBreakdown['Transportation'].total,
                suggestion: 'Consider carpooling or public transportation options',
                potentialSavings: categoryBreakdown['Transportation'].total * 0.25
            });
        }

        return opportunities;
    }

    showLoadingState() {
        const container = document.querySelector('.upload-container');
        const existingResults = document.getElementById('analysisResults');
        if (existingResults) {
            existingResults.remove();
        }

        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingState';
        loadingDiv.innerHTML = `
            <div style="text-align: center; padding: 60px;">
                <div class="spinner" style="margin: 0 auto 20px;"></div>
                <h3 style="color: #4facfe;">Analyzing your transactions...</h3>
                <p style="color: #6c757d;">This may take a few moments</p>
            </div>
        `;
        container.appendChild(loadingDiv);
    }

    displayResults() {
        const loadingState = document.getElementById('loadingState');
        if (loadingState) {
            loadingState.remove();
        }

        const container = document.querySelector('.upload-container');
        const resultsDiv = document.createElement('div');
        resultsDiv.id = 'analysisResults';
        resultsDiv.innerHTML = this.generateResultsHTML();
        container.appendChild(resultsDiv);

        // Initialize charts
        this.initializeCharts();

        // Add export functionality
        this.initializeExportButtons();
    }

    generateResultsHTML() {
        const { overview, categoryBreakdown, merchantAnalysis, recurringPayments, anomalies, savingsOpportunities } = this.analysisResults;

        return `
            <div class="analysis-results" style="margin-top: 60px;">
                <!-- Overview Metrics -->
                <div class="metrics-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px;">
                    <div class="metric-card" style="background: #f8f9fa; padding: 25px; border-radius: 12px; text-align: center; border-left: 4px solid #4facfe;">
                        <div class="metric-value" style="font-size: 2rem; font-weight: 700; color: #1a1a1a; margin-bottom: 5px;">
                            $${overview.monthlyAverage.toFixed(0).toLocaleString()}
                        </div>
                        <div class="metric-label" style="color: #6c757d; font-size: 0.875rem; text-transform: uppercase;">Monthly Average</div>
                    </div>
                    <div class="metric-card" style="background: #f8f9fa; padding: 25px; border-radius: 12px; text-align: center; border-left: 4px solid #4facfe;">
                        <div class="metric-value" style="font-size: 2rem; font-weight: 700; color: #1a1a1a; margin-bottom: 5px;">
                            $${overview.topCategoryAmount.toFixed(0).toLocaleString()}
                        </div>
                        <div class="metric-label" style="color: #6c757d; font-size: 0.875rem; text-transform: uppercase;">${overview.topCategory}</div>
                    </div>
                    <div class="metric-card" style="background: #f8f9fa; padding: 25px; border-radius: 12px; text-align: center; border-left: 4px solid #4facfe;">
                        <div class="metric-value" style="font-size: 2rem; font-weight: 700; color: ${overview.monthOverMonth < 0 ? '#00bfa5' : '#ff6b6b'}; margin-bottom: 5px;">
                            ${overview.monthOverMonth > 0 ? '+' : ''}${overview.monthOverMonth}%
                        </div>
                        <div class="metric-label" style="color: #6c757d; font-size: 0.875rem; text-transform: uppercase;">vs Last Month</div>
                    </div>
                    <div class="metric-card" style="background: #f8f9fa; padding: 25px; border-radius: 12px; text-align: center; border-left: 4px solid #4facfe;">
                        <div class="metric-value" style="font-size: 2rem; font-weight: 700; color: #1a1a1a; margin-bottom: 5px;">
                            ${overview.transactionCount}
                        </div>
                        <div class="metric-label" style="color: #6c757d; font-size: 0.875rem; text-transform: uppercase;">Transactions</div>
                    </div>
                </div>

                <!-- Charts Section -->
                <div class="charts-section" style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 40px;">
                    <div class="chart-container" style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                        <h3 style="margin-bottom: 20px;">Spending by Category</h3>
                        <canvas id="categoryChart" width="400" height="300"></canvas>
                    </div>
                    <div class="chart-container" style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                        <h3 style="margin-bottom: 20px;">Spending Trends</h3>
                        <canvas id="trendChart" width="400" height="300"></canvas>
                    </div>
                </div>

                <!-- Top Merchants -->
                <div class="merchants-section" style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 40px;">
                    <h3 style="margin-bottom: 20px;">Top Merchants</h3>
                    <div class="merchants-list">
                        ${merchantAnalysis.slice(0, 5).map(m => `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid #e9ecef;">
                                <div>
                                    <div style="font-weight: 600;">${m.name}</div>
                                    <div style="color: #6c757d; font-size: 0.875rem;">${m.count} transactions</div>
                                </div>
                                <div style="font-weight: 700; color: #1a1a1a;">$${m.total.toFixed(2)}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Recurring Payments -->
                ${recurringPayments.length > 0 ? `
                    <div class="recurring-section" style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 40px;">
                        <h3 style="margin-bottom: 20px;">Recurring Payments Detected</h3>
                        <div class="recurring-list">
                            ${recurringPayments.slice(0, 5).map(r => `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid #e9ecef;">
                                    <div>
                                        <div style="font-weight: 600;">${r.merchant}</div>
                                        <div style="color: #6c757d; font-size: 0.875rem;">${r.frequency} • ${r.occurrences} payments</div>
                                    </div>
                                    <div style="font-weight: 700; color: #1a1a1a;">$${r.amount.toFixed(2)}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Anomalies -->
                ${anomalies.length > 0 ? `
                    <div class="anomalies-section" style="background: #fff5f5; padding: 30px; border-radius: 12px; margin-bottom: 40px;">
                        <h3 style="margin-bottom: 20px; color: #ff6b6b;">
                            <i class="fas fa-exclamation-triangle"></i> Unusual Activity Detected
                        </h3>
                        <div class="anomalies-list">
                            ${anomalies.slice(0, 3).map(a => `
                                <div style="padding: 15px; background: white; border-radius: 8px; margin-bottom: 10px;">
                                    <div style="font-weight: 600;">${a.transaction.merchant}</div>
                                    <div style="color: #6c757d; font-size: 0.875rem;">${a.reason}</div>
                                    <div style="margin-top: 5px;">
                                        Amount: <strong>$${Math.abs(a.transaction.amount).toFixed(2)}</strong>
                                        ${a.expected ? ` (Expected: ~$${a.expected.toFixed(2)})` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Savings Opportunities -->
                ${savingsOpportunities.length > 0 ? `
                    <div class="savings-section" style="background: #e6f9f0; padding: 30px; border-radius: 12px; margin-bottom: 40px;">
                        <h3 style="margin-bottom: 20px; color: #00bfa5;">
                            <i class="fas fa-piggy-bank"></i> Savings Opportunities
                        </h3>
                        <div class="savings-list">
                            ${savingsOpportunities.map(s => `
                                <div style="padding: 15px; background: white; border-radius: 8px; margin-bottom: 10px;">
                                    <div style="font-weight: 600;">${s.category}</div>
                                    <div style="color: #6c757d; margin: 5px 0;">${s.suggestion}</div>
                                    <div>
                                        Potential savings: <strong style="color: #00bfa5;">$${s.potentialSavings.toFixed(0)}/month</strong>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Export Options -->
                <div class="export-section" style="text-align: center; margin-top: 60px;">
                    <h3 style="margin-bottom: 30px;">Export Your Analysis</h3>
                    <div style="display: flex; gap: 20px; justify-content: center;">
                        <button id="exportPDF" class="export-btn" style="background: #4facfe; color: white; border: none; padding: 15px 40px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 10px;">
                            <i class="fas fa-file-pdf"></i> Download PDF Report
                        </button>
                        <button id="exportExcel" class="export-btn" style="background: #00bfa5; color: white; border: none; padding: 15px 40px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 10px;">
                            <i class="fas fa-file-excel"></i> Download Excel Dashboard
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    initializeCharts() {
        // Category Pie Chart
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        const categoryData = Object.entries(this.analysisResults.categoryBreakdown)
            .filter(([cat]) => cat !== 'Income')
            .sort((a, b) => b[1].total - a[1].total)
            .slice(0, 6);

        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: categoryData.map(([cat]) => cat),
                datasets: [{
                    data: categoryData.map(([_, data]) => data.total),
                    backgroundColor: [
                        '#4facfe',
                        '#00f2fe',
                        '#43e97b',
                        '#fa709a',
                        '#fee140',
                        '#30cfd0'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });

        // Trend Line Chart
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        const cashFlow = this.analysisResults.cashFlow;
        const months = Object.keys(cashFlow).sort();

        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: months.map(m => {
                    const [year, month] = m.split('-');
                    return new Date(year, month - 1).toLocaleDateString('en-US', { month: 'short' });
                }),
                datasets: [{
                    label: 'Income',
                    data: months.map(m => cashFlow[m].income),
                    borderColor: '#00bfa5',
                    backgroundColor: 'rgba(0, 191, 165, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Expenses',
                    data: months.map(m => cashFlow[m].expenses),
                    borderColor: '#ff6b6b',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    initializeExportButtons() {
        document.getElementById('exportPDF')?.addEventListener('click', () => {
            this.exportPDFReport();
        });

        document.getElementById('exportExcel')?.addEventListener('click', () => {
            this.exportExcelDashboard();
        });
    }

    exportPDFReport() {
        if (!window.jspdf) {
            this.showMessage('PDF library is still loading. Please try again.', 'info');
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        const { overview, categoryBreakdown, merchantAnalysis } = this.analysisResults;

        // Title
        doc.setFontSize(20);
        doc.text('Financial Analysis Report', 20, 20);

        // Date
        doc.setFontSize(12);
        doc.text(`Generated: ${new Date().toLocaleDateString()}`, 20, 30);

        // Overview Section
        doc.setFontSize(16);
        doc.text('Overview', 20, 45);
        doc.setFontSize(12);
        doc.text(`Monthly Average Spending: $${overview.monthlyAverage.toFixed(2)}`, 20, 55);
        doc.text(`Top Category: ${overview.topCategory} ($${overview.topCategoryAmount.toFixed(2)})`, 20, 65);
        doc.text(`Total Transactions: ${overview.transactionCount}`, 20, 75);
        doc.text(`Month-over-Month Change: ${overview.monthOverMonth}%`, 20, 85);

        // Category Breakdown
        doc.setFontSize(16);
        doc.text('Category Breakdown', 20, 105);
        doc.setFontSize(12);
        let yPos = 115;
        Object.entries(categoryBreakdown)
            .filter(([cat]) => cat !== 'Income')
            .sort((a, b) => b[1].total - a[1].total)
            .slice(0, 5)
            .forEach(([category, data]) => {
                doc.text(`${category}: $${data.total.toFixed(2)} (${data.count} transactions)`, 20, yPos);
                yPos += 10;
            });

        // Top Merchants
        doc.setFontSize(16);
        doc.text('Top Merchants', 20, yPos + 20);
        doc.setFontSize(12);
        yPos += 30;
        merchantAnalysis.slice(0, 5).forEach(merchant => {
            doc.text(`${merchant.name}: $${merchant.total.toFixed(2)} (${merchant.count} transactions)`, 20, yPos);
            yPos += 10;
        });

        // Save PDF
        doc.save(`financial_analysis_${new Date().toISOString().slice(0, 10)}.pdf`);
        this.showMessage('PDF report downloaded successfully!', 'success');
    }

    exportExcelDashboard() {
        // Create CSV data (Excel-compatible)
        const csvData = [];
        
        // Overview sheet data
        csvData.push(['Financial Analysis Dashboard']);
        csvData.push(['Generated:', new Date().toLocaleDateString()]);
        csvData.push([]);
        csvData.push(['Overview']);
        csvData.push(['Metric', 'Value']);
        csvData.push(['Monthly Average', this.analysisResults.overview.monthlyAverage.toFixed(2)]);
        csvData.push(['Top Category', this.analysisResults.overview.topCategory]);
        csvData.push(['Total Transactions', this.analysisResults.overview.transactionCount]);
        csvData.push(['Month-over-Month', this.analysisResults.overview.monthOverMonth + '%']);
        csvData.push([]);

        // Transactions data
        csvData.push(['Transaction Details']);
        csvData.push(['Date', 'Description', 'Category', 'Amount', 'Type']);
        this.transactions.forEach(t => {
            csvData.push([
                t.date.toLocaleDateString(),
                t.description,
                t.category,
                t.amount.toFixed(2),
                t.type
            ]);
        });

        // Convert to CSV string
        const csv = csvData.map(row => row.map(cell => {
            // Escape quotes and wrap in quotes if contains comma
            const str = String(cell);
            return str.includes(',') || str.includes('"') ? 
                `"${str.replace(/"/g, '""')}"` : str;
        }).join(',')).join('\n');

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `financial_dashboard_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showMessage('Excel dashboard downloaded successfully!', 'success');
    }

    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;

        const colors = {
            'success': '#00bfa5',
            'error': '#ff6b6b',
            'info': '#4facfe'
        };

        messageDiv.style.background = colors[type] || colors.info;
        messageDiv.textContent = message;
        document.body.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => messageDiv.remove(), 300);
        }, 3000);
    }
}

// Add styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .analyze-area.drag-over {
        background: linear-gradient(135deg, #5fbdff 0%, #00f8ff 100%) !important;
        transform: scale(1.02);
    }
    
    .export-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }
    
    .spinner {
        width: 50px;
        height: 50px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #4facfe;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @media (max-width: 768px) {
        .charts-section {
            grid-template-columns: 1fr !important;
        }
        
        .metrics-grid {
            grid-template-columns: 1fr 1fr !important;
        }
        
        .export-section > div {
            flex-direction: column !important;
        }
    }
`;
document.head.appendChild(style);

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new TransactionAnalyzer();
    });
} else {
    new TransactionAnalyzer();
}