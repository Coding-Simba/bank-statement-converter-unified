"""Standalone green_dot parser"""
import re
from datetime import datetime
import pandas as pd
import pdfplumber
import logging

logger = logging.getLogger(__name__)

def parse_green_dot(pdf_path: str) -> pd.DataFrame:
    """Parse green_dot PDF"""
    logger.info(f"Parsing green_dot PDF: {pdf_path}")
    
    # For now, use the universal parser as fallback
    try:
        from universal_parser import parse_universal_pdf
        return parse_universal_pdf(pdf_path)
    except:
        # Return empty DataFrame if parser not available
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Balance'])

def parse(pdf_path: str) -> pd.DataFrame:
    return parse_green_dot(pdf_path)
