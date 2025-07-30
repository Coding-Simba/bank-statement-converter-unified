"""Standalone becu parser"""
import re
from datetime import datetime
import pandas as pd
import pdfplumber
import logging

logger = logging.getLogger(__name__)

def parse_becu(pdf_path: str) -> pd.DataFrame:
    """Parse becu PDF"""
    logger.info(f"Parsing becu PDF: {pdf_path}")
    
    # For now, use the universal parser as fallback
    try:
        from universal_parser import parse_universal_pdf
        return parse_universal_pdf(pdf_path)
    except:
        # Return empty DataFrame if parser not available
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Balance'])

def parse(pdf_path: str) -> pd.DataFrame:
    return parse_becu(pdf_path)
