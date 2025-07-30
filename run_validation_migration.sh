#!/bin/bash

# Run validation database migration on server

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Running database migration for validation feature..."

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

# Create migration script
cat > temp_migration.py << 'SCRIPT'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import create_engine, text
    import config
    
    print("Connecting to database...")
    engine = create_engine(config.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check and add columns
        try:
            conn.execute(text("ALTER TABLE statements ADD COLUMN validated BOOLEAN DEFAULT FALSE"))
            print("✓ Added validated column")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("- validated column already exists")
            else:
                print(f"Error with validated column: {e}")
        
        try:
            conn.execute(text("ALTER TABLE statements ADD COLUMN validation_date TIMESTAMP NULL"))
            print("✓ Added validation_date column")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("- validation_date column already exists")
            else:
                print(f"Error with validation_date column: {e}")
        
        try:
            conn.execute(text("ALTER TABLE statements ADD COLUMN validated_data TEXT NULL"))
            print("✓ Added validated_data column")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("- validated_data column already exists")
            else:
                print(f"Error with validated_data column: {e}")
        
        conn.commit()
        print("\n✅ Migration complete!")
        
except Exception as e:
    print(f"Migration error: {e}")
    exit(1)
SCRIPT

# Run migration
python3 temp_migration.py

# Clean up
rm temp_migration.py

# Update models.py to include validation fields
if ! grep -q "validated = Column" models.py; then
    echo "Adding validation fields to Statement model..."
    sed -i '/class Statement(Base):/,/^class/ s/user = relationship.*/&\n    validated = Column(Boolean, default=False)\n    validation_date = Column(DateTime, nullable=True)\n    validated_data = Column(Text, nullable=True)/' models.py
    echo "✓ Updated Statement model"
fi

# Ensure validation router is imported and included
if ! grep -q "from .api import validation" main.py; then
    echo "Adding validation router to main.py..."
    sed -i '/from .api import statements/a from .api import validation' main.py
    sed -i '/app.include_router(statements.router/a app.include_router(validation.router, prefix="/api", tags=["validation"])' main.py
    echo "✓ Updated main.py"
fi

# Restart service
echo "Restarting service..."
sudo systemctl restart bankconverter

echo "✅ All done!"
EOF

echo "Migration script execution complete!"