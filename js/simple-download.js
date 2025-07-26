// Simple, direct download implementation

function simpleDownloadCSV() {
    // Create CSV content
    const csvContent = 'Date,Description,Amount,Balance\n' +
        '2024-01-15,Opening Balance,0.00,5000.00\n' +
        '2024-01-16,Grocery Store,-45.32,4954.68\n' +
        '2024-01-17,Salary Deposit,3500.00,8454.68\n' +
        '2024-01-18,Electric Bill,-125.00,8329.68\n' +
        '2024-01-19,Gas Station,-65.45,8264.23';
    
    // Create a Blob
    const blob = new Blob([csvContent], { type: 'text/csv' });
    
    // Create a temporary URL for the blob
    const url = window.URL.createObjectURL(blob);
    
    // Create a temporary anchor element
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bank_statement.csv';
    
    // Trigger the download
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    // Clean up the URL
    window.URL.revokeObjectURL(url);
    
    console.log('CSV download triggered');
}

function simpleDownloadExcel() {
    // Create simple HTML table that Excel can read
    const htmlContent = '<html><head><meta charset="utf-8"></head><body>' +
        '<table border="1">' +
        '<tr><th>Date</th><th>Description</th><th>Amount</th><th>Balance</th></tr>' +
        '<tr><td>2024-01-15</td><td>Opening Balance</td><td>0.00</td><td>5000.00</td></tr>' +
        '<tr><td>2024-01-16</td><td>Grocery Store</td><td>-45.32</td><td>4954.68</td></tr>' +
        '<tr><td>2024-01-17</td><td>Salary Deposit</td><td>3500.00</td><td>8454.68</td></tr>' +
        '<tr><td>2024-01-18</td><td>Electric Bill</td><td>-125.00</td><td>8329.68</td></tr>' +
        '<tr><td>2024-01-19</td><td>Gas Station</td><td>-65.45</td><td>8264.23</td></tr>' +
        '</table></body></html>';
    
    // Create a Blob with Excel MIME type
    const blob = new Blob([htmlContent], { type: 'application/vnd.ms-excel' });
    
    // Create a temporary URL
    const url = window.URL.createObjectURL(blob);
    
    // Create temporary anchor
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bank_statement.xls';
    
    // Trigger download
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    // Clean up
    window.URL.revokeObjectURL(url);
    
    console.log('Excel download triggered');
}