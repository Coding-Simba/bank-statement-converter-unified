// Fixed download functionality that works across all browsers

function forceDownloadCSV(filename) {
    console.log('Starting CSV download for:', filename);
    
    // Sample CSV data
    const csvContent = [
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
    ].map(row => row.join(',')).join('\n');

    // Method 1: Try using download attribute
    try {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || 'bank_statement.csv';
        link.style.display = 'none';
        
        // Append to body, click, and remove
        document.body.appendChild(link);
        link.click();
        
        // Cleanup
        setTimeout(() => {
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        }, 100);
        
        return true;
    } catch (e) {
        console.error('Download method 1 failed:', e);
    }
    
    // Method 2: Try using window.open
    try {
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
        }, 100);
        
        return true;
    } catch (e) {
        console.error('Download method 2 failed:', e);
    }
    
    // Method 3: Use data URI as fallback
    try {
        const dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);
        const link = document.createElement('a');
        link.href = dataUri;
        link.download = filename || 'bank_statement.csv';
        link.click();
        return true;
    } catch (e) {
        console.error('Download method 3 failed:', e);
    }
    
    return false;
}

function forceDownloadExcel(filename) {
    console.log('Starting Excel download for:', filename);
    
    // Excel XML format that opens correctly in Excel
    const excelContent = `<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
 <DocumentProperties xmlns="urn:schemas-microsoft-com:office:office">
  <Created>2024-01-01T00:00:00Z</Created>
  <Version>16.00</Version>
 </DocumentProperties>
 <Styles>
  <Style ss:ID="Default" ss:Name="Normal">
   <Alignment ss:Vertical="Bottom"/>
   <Borders/>
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>
   <Interior/>
   <NumberFormat/>
   <Protection/>
  </Style>
  <Style ss:ID="s62">
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"
    ss:Bold="1"/>
  </Style>
 </Styles>
 <Worksheet ss:Name="Statement">
  <Table>
   <Row ss:StyleID="s62">
    <Cell><Data ss:Type="String">Date</Data></Cell>
    <Cell><Data ss:Type="String">Description</Data></Cell>
    <Cell><Data ss:Type="String">Amount</Data></Cell>
    <Cell><Data ss:Type="String">Balance</Data></Cell>
   </Row>
   <Row>
    <Cell><Data ss:Type="String">2024-01-15</Data></Cell>
    <Cell><Data ss:Type="String">Opening Balance</Data></Cell>
    <Cell><Data ss:Type="Number">0.00</Data></Cell>
    <Cell><Data ss:Type="Number">5000.00</Data></Cell>
   </Row>
   <Row>
    <Cell><Data ss:Type="String">2024-01-16</Data></Cell>
    <Cell><Data ss:Type="String">Grocery Store</Data></Cell>
    <Cell><Data ss:Type="Number">-45.32</Data></Cell>
    <Cell><Data ss:Type="Number">4954.68</Data></Cell>
   </Row>
   <Row>
    <Cell><Data ss:Type="String">2024-01-17</Data></Cell>
    <Cell><Data ss:Type="String">Salary Deposit</Data></Cell>
    <Cell><Data ss:Type="Number">3500.00</Data></Cell>
    <Cell><Data ss:Type="Number">8454.68</Data></Cell>
   </Row>
   <Row>
    <Cell><Data ss:Type="String">2024-01-18</Data></Cell>
    <Cell><Data ss:Type="String">Electric Bill</Data></Cell>
    <Cell><Data ss:Type="Number">-125.00</Data></Cell>
    <Cell><Data ss:Type="Number">8329.68</Data></Cell>
   </Row>
   <Row>
    <Cell><Data ss:Type="String">2024-01-19</Data></Cell>
    <Cell><Data ss:Type="String">Gas Station</Data></Cell>
    <Cell><Data ss:Type="Number">-65.45</Data></Cell>
    <Cell><Data ss:Type="Number">8264.23</Data></Cell>
   </Row>
   <Row>
    <Cell><Data ss:Type="String">2024-01-20</Data></Cell>
    <Cell><Data ss:Type="String">Restaurant</Data></Cell>
    <Cell><Data ss:Type="Number">-82.50</Data></Cell>
    <Cell><Data ss:Type="Number">8181.73</Data></Cell>
   </Row>
  </Table>
 </Worksheet>
</Workbook>`;

    // Try multiple download methods
    try {
        const blob = new Blob([excelContent], { 
            type: 'application/vnd.ms-excel;charset=utf-8;' 
        });
        const url = window.URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || 'bank_statement.xls';
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        
        setTimeout(() => {
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        }, 100);
        
        return true;
    } catch (e) {
        console.error('Excel download failed:', e);
        
        // Fallback to CSV if Excel fails
        return forceDownloadCSV(filename.replace('.xls', '.csv'));
    }
}

// Global functions for testing
window.testDirectDownloadCSV = function() {
    const success = forceDownloadCSV('test_statement.csv');
    console.log('CSV download result:', success);
};

window.testDirectDownloadExcel = function() {
    const success = forceDownloadExcel('test_statement.xls');
    console.log('Excel download result:', success);
};