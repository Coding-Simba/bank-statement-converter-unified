"""Database model updates for validation feature"""

# Add these fields to the Statement model in models.py:

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

# Add to Statement model:
class StatementUpdate:
    """Additional fields for Statement model"""
    
    # Validation fields
    validated = Column(Boolean, default=False)
    validation_date = Column(DateTime, nullable=True)
    validated_data = Column(Text, nullable=True)  # JSON string of validated transactions
    
    # Add method to check if validated
    def is_validated(self):
        return self.validated and self.validated_data is not None