# Failed PDF Management System

This system automatically saves PDFs that fail to parse correctly for future code improvements.

## How It Works

1. **Automatic Detection**: When a PDF is processed, the system checks if parsing was successful
2. **Success Criteria**:
   - At least some transactions were found
   - At least 50% of transactions have valid amounts (non-zero, under $1M)
   - At least 30% of transactions have dates
3. **Automatic Saving**: Failed PDFs are copied to the `failed_pdfs/` directory with metadata

## File Structure

```
failed_pdfs/
├── failed_pdfs_metadata.json    # Metadata about all failed PDFs
├── 20250726_212412_48b7bacd_example.pdf    # Failed PDF files
└── ...
```

## Metadata Tracked

For each failed PDF, we track:
- Original filename
- Timestamp when saved
- Number of transactions found
- Number of valid transactions
- Number of transactions with dates
- Sample of extracted transactions
- File hash (to avoid duplicates)
- Status (pending_review, reviewed, fixed)

## Management Commands

### List Failed PDFs
```bash
python manage_failed_pdfs.py list
python manage_failed_pdfs.py list --status pending_review
```

### Show Statistics
```bash
python manage_failed_pdfs.py stats
```

### Update Status
```bash
python manage_failed_pdfs.py update --hash 48b7bacd --new-status reviewed --notes "Commerce Bank format"
```

## Using Failed PDFs for Improvement

1. Review failed PDFs regularly using the management script
2. Identify common patterns in failures
3. Create specialized parsers for specific formats
4. Test improvements against saved PDFs
5. Mark as "fixed" when parser is updated

## Privacy Considerations

- Failed PDFs contain user financial data
- Store securely and limit access
- Consider anonymization for long-term storage
- Delete after improvements are implemented
- Never share or commit actual PDF files to version control

## Integration

The system is integrated into:
- `backend/universal_parser.py` - Automatically checks and saves failed PDFs
- `backend/api/statements.py` - API endpoints handle failures gracefully
- `backend/failed_pdf_manager.py` - Core management functionality

## Future Improvements

1. **Automatic Pattern Detection**: Analyze failed PDFs to detect common formats
2. **ML Training Data**: Use failed PDFs to train ML models
3. **User Feedback**: Allow users to report parsing issues
4. **Automated Testing**: Test parser improvements against all failed PDFs
5. **Dashboard**: Web interface for reviewing failed PDFs