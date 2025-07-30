"""Add validation fields to Statement table"""

import sys
sys.path.append('/home/ubuntu/bank-statement-converter/backend')

from sqlalchemy import create_engine, text
from database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add validation fields to statements table"""
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'statements' 
                AND column_name IN ('validated', 'validation_date', 'validated_data')
            """))
            
            existing_columns = [row[0] for row in result]
            
            # Add validated column if not exists
            if 'validated' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE statements 
                    ADD COLUMN validated BOOLEAN DEFAULT FALSE
                """))
                logger.info("Added 'validated' column")
            
            # Add validation_date column if not exists
            if 'validation_date' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE statements 
                    ADD COLUMN validation_date TIMESTAMP NULL
                """))
                logger.info("Added 'validation_date' column")
            
            # Add validated_data column if not exists
            if 'validated_data' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE statements 
                    ADD COLUMN validated_data TEXT NULL
                """))
                logger.info("Added 'validated_data' column")
            
            conn.commit()
            logger.info("Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate()