# Dummy Statement PDF - Actual vs Extracted Comparison

## Actual Transactions from PDF

### Page 1 - Account Transactions by date
| Date | Description | Debit | Credit | Balance |
|------|-------------|-------|--------|---------|
| 10/02 | POS PURCHASE | 4.23 | | 65.73 |
| 10/03 | PREAUTHORIZED CREDIT | | 763.01 | 828.74 |
| 10/04 | POS PURCHASE | 11.68 | | 817.06 |
| 10/05 | CHECK 1234 | 9.98 | | 807.08 |
| 10/05 | POS PURCHASE | 25.50 | | 781.58 |
| 10/08 | POS PURCHASE | 59.08 | | 722.50 |
| 10/12 | CHECK 1236 | 69.00 | | 653.50 |
| 10/14 | CHECK 1237 | 180.63 | | 472.87 |
| 10/14 | POS PURCHASE | 18.96 | | 453.91 |
| 10/16 | PREAUTHORIZED CREDIT | | 763.01 | 1216.92 |
| 10/22 | ATM WITHDRAWAL | 140.00 | | 1076.92 |
| 10/28 | CHECK 1238 | 91.06 | | 985.86 |
| 10/30 | CHECK 1239 | 451.20 | | 534.66 |
| 10/30 | CHECK 1246 | 37.07 | | 497.59 |
| 10/30 | POS PURCHASE | 18.67 | | 478.92 |
| 10/31 | CHECK 1247 | 100.00 | | 378.92 |
| 10/31 | CHECK 1248 | 78.24 | | 300.68 |
| 10/31 | PREAUTHORIZED CREDIT | | 350.00 | 650.68 |
| 11/02 | CHECK 1249 | 52.23 | | 598.45 |
| 11/09 | INTEREST CREDIT | | 0.26 | 598.71 |
| 11/09 | SERVICE CHARGE | 12.00 | | 586.71 |

### Page 2 - Detailed Transactions
**Deposits and Other Credits:**
- 10/03: PREAUTHORIZED CREDIT - PAYROLL 098765 678900 - $763.01
- 10/16: PREAUTHORIZED CREDIT - US TREASURY 310 BOS SEC 020802 5094098S3A SSA - $763.01
- 10/31: PREAUTHORIZED CREDIT - DEPOSIT TERMINAL S097094 09809 5/23 PM 0970837409978X0032 - $350.00
- 11/09: INTEREST CREDIT - $0.26

**Withdrawals and Other Debits:**
- 10/02: POS PURCHASE - Various terminal IDs - $4.23
- 10/04: POS PURCHASE - $11.68
- 10/05: POS PURCHASE - $25.50
- 10/07: POS PURCHASE - $31.57
- 10/14: POS PURCHASE - $18.96
- 10/22: ATM WITHDRAWAL - $140.00
- 10/30: POS PURCHASE - $18.67

**Checks Paid:**
- Check #1234 (10/05): $9.98
- Check #1236 (10/12): $69.00
- Check #1237 (10/14): $180.63
- Check #1238 (10/28): $91.06
- Check #1239 (10/30): $451.20
- Check #1246 (10/30): $37.07
- Check #1247 (10/31): $100.00
- Check #1248 (10/31): $78.24
- Check #1249 (11/02): $52.23

## Our Extraction Results

### Enhanced Parser: 9 transactions
1. 10/05 - CHECK 1234 - $-9.98 ✓
2. 10/12 - CHECK 1236 - $-69.00 ✓
3. 10/14 - CHECK 1237 - $-180.63 ✓
4. 10/16 - PREAUTHORIZED CREDIT - $310.00 ❌ (Should be $763.01)
5. 10/31 - PREAUTHORIZED CREDIT - $9809.00 ❌ (Should be $350.00)
6. 10/04 - POS PURCHASE - $-443565.00 ❌ (Should be $-11.68)
7. 10/07 - POS PURCHASE - $-98765.00 ❌ (Should be $-31.57)
8. 10/14 - POS PURCHASE - $-98765.00 ❌ (Should be $-18.96)
9. 10/30 - POS PURCHASE - $-98765.00 ❌ (Should be $-18.67)

## Analysis

### Major Issues:
1. **Missing Transactions**: Only extracted 9 out of 21 actual transactions
2. **Incorrect Amounts**: 
   - PREAUTHORIZED CREDIT amounts are wrong ($310 instead of $763.01, $9809 instead of $350)
   - POS PURCHASE amounts are completely wrong (hundreds of thousands instead of small amounts)
3. **Missing Transactions Include**:
   - Multiple checks (#1238, #1239, #1246, #1247, #1248, #1249)
   - Several POS purchases
   - ATM withdrawal
   - Interest credit
   - Service charge

### OCR Issues:
The OCR is severely misreading amounts, likely due to:
- Poor image quality
- Misalignment of columns
- Number recognition errors (e.g., reading terminal IDs as amounts)

### Actual Totals:
- **Total Credits**: $763.01 + $763.01 + $350.00 + $0.26 = $1,876.28
- **Total Debits**: $1,289.57
- **Net Change**: $586.71 (matches ending balance)

### Our Extracted Totals:
- **Total Credits**: $10,119.00 (Wildly incorrect)
- **Total Debits**: -$740,119.61 (Wildly incorrect)