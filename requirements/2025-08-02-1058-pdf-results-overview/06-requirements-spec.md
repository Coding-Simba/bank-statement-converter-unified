# PDF Results Overview - Requirements Specification

## Problem Statement
Users currently receive converted bank statement files without seeing the extracted data first. They cannot verify the extraction quality before downloading, and have no visibility into what was parsed from their PDFs. This creates uncertainty about the conversion accuracy and limits user confidence in the service.

## Solution Overview
Implement a results overview page that displays parsed transaction data in a paginated table format after successful PDF extraction. Users will be automatically redirected to this page after conversion, where they can review all extracted transactions, see extraction statistics, and download the data in CSV or Markdown format.

## Functional Requirements

### 1. Results Display Page
- **Route:** `/results/{statement_id}` - allows direct linking and sharing
- **Access:** Available to both authenticated and anonymous users who converted the file
- **Layout:** Consistent with existing site design using dashboard patterns

### 2. Transaction Table
- **Display:** Paginated table showing all extracted transactions
- **Columns:** Date, Description, Amount, Balance
- **Pagination:** Server-side pagination with 50 transactions per page
- **Styling:** Use existing table patterns from `/css/dashboard.css`

### 3. Extraction Statistics
- **Display:** Statistics cards above the transaction table
- **Information:**
  - Total transactions extracted
  - Date range (earliest to latest transaction)
  - Detected bank name
  - Original filename
- **Layout:** Grid-based stat cards using `.stats-grid` pattern

### 4. Download Options
- **Formats:** CSV and Markdown (.md) only (Excel removed)
- **Buttons:** Prominent download buttons below statistics
- **Markdown Format:** Include statistics header for complete context

### 5. Multiple File Support
- **Behavior:** When multiple PDFs are uploaded, show results for each file
- **Navigation:** Tabs or accordion to switch between different file results
- **State:** Maintain all file results until user navigates away

### 6. Automatic Redirect
- **Trigger:** After successful PDF conversion
- **Timing:** Immediate redirect once processing completes
- **Loading:** Show processing state during conversion

## Technical Requirements

### Backend Modifications

#### 1. Enhanced Convert Endpoint
**File:** `/backend/api/statements.py`
```python
# Modify response to include result page URL
@router.post("/api/convert")
# Return: {...existing, "results_url": f"/results/{statement_id}"}
```

#### 2. New Transactions Endpoint
**File:** `/backend/api/statements.py`
```python
@router.get("/api/statement/{statement_id}/transactions")
async def get_statement_transactions(
    statement_id: int,
    page: int = 1,
    per_page: int = 50
):
    # Re-parse PDF to get transactions
    # Return: {
    #   "transactions": [...],
    #   "total_count": int,
    #   "statistics": {
    #     "bank_name": str,
    #     "date_range": {"start": date, "end": date},
    #     "total_transactions": int
    #   },
    #   "pagination": {
    #     "page": int,
    #     "per_page": int,
    #     "total_pages": int
    #   }
    # }
```

#### 3. Markdown Export Endpoint
**File:** `/backend/api/statements.py`
```python
@router.get("/api/statement/{statement_id}/download/markdown")
# Generate markdown with statistics header
```

### Frontend Implementation

#### 1. New Results Page
**File:** `/results-overview.html`
- Navigation bar (reuse existing)
- Statistics cards section
- Paginated transaction table
- Download buttons (CSV, Markdown)

#### 2. Results JavaScript
**File:** `/js/results-overview.js`
```javascript
// Core functionality:
- fetchTransactions(statementId, page)
- renderStatistics(stats)
- renderTransactionTable(transactions)
- setupPagination(totalPages, currentPage)
- downloadCSV(statementId)
- downloadMarkdown(statementId)
```

#### 3. Modify Upload Flow
**File:** `/js/modern-homepage.js`
```javascript
// In showSuccessState function:
// Instead of showing download buttons, redirect to results
window.location.href = response.results_url;
```

#### 4. Styling
**File:** Extend `/css/dashboard.css` or create `/css/results-overview.css`
- Reuse `.conversions-table` patterns
- Reuse `.stats-grid` and `.stat-card` patterns
- Add pagination styling

## Implementation Patterns

### 1. Table Rendering Pattern (from dashboard.js)
```javascript
const tableHTML = `
    <div class="transactions-table">
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Balance</th>
                </tr>
            </thead>
            <tbody>
                ${transactions.map(createTransactionRow).join('')}
            </tbody>
        </table>
    </div>
`;
```

### 2. Statistics Card Pattern (from modern-dashboard.css)
```html
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-label">Total Transactions</div>
        <div class="stat-value">{count}</div>
    </div>
    <!-- More stat cards -->
</div>
```

### 3. Authentication Check Pattern
```javascript
// For anonymous user access
const user = await window.BankAuth.TokenManager.isAuthenticated();
if (!user) {
    // Check session-based access for anonymous users
}
```

## Acceptance Criteria

1. ✓ Users are automatically redirected to results page after PDF conversion
2. ✓ Results page displays all transactions in a paginated table
3. ✓ Statistics show total transactions, date range, and detected bank
4. ✓ Users can download data as CSV or Markdown
5. ✓ Multiple uploaded PDFs each show their own results
6. ✓ Anonymous users can access results for files they converted
7. ✓ Results page has a shareable URL with statement ID
8. ✓ Page styling matches existing site design
9. ✓ Server-side pagination handles large transaction sets efficiently
10. ✓ Markdown export includes statistics header

## Assumptions

1. PDF files remain available on server for re-parsing when viewing results
2. The 5-minute access window for anonymous users (from statements.py) applies to results viewing
3. Transaction data is not edited on the results page (read-only display)
4. Bank detection logic exists in the universal parser
5. Existing authentication and session management systems will be reused