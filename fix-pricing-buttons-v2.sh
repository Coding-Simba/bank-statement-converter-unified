#!/bin/bash

# Fix Pricing Buttons V2
echo "🔧 Fixing Pricing Buttons (V2)"
echo "============================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Creating Python script to fix buttons..."
cat > fix_pricing_buttons.py << 'EOF'
#!/usr/bin/env python3
import re

# Read the file
with open('pricing.html', 'r') as f:
    content = f.read()

# Pattern to match pricing-cta buttons
pattern = r'<a class="pricing-cta primary" href="#">Buy</a>'

# Counter for replacements
replacements = 0

# Split content by pricing cards to identify which plan each button belongs to
cards = content.split('<div class="pricing-card')

# Process each card
result_parts = [cards[0]]  # Keep everything before first card

for i, card in enumerate(cards[1:], 1):
    # Determine which plan this is
    if 'Starter' in card:
        plan = 'starter'
    elif 'Professional' in card:
        plan = 'professional'
    elif 'Business' in card:
        plan = 'business'
    else:
        plan = None
    
    # Replace the buy button if plan was identified
    if plan:
        new_button = f'<a class="pricing-cta primary" href="#" data-plan="{plan}">Buy</a>'
        card = card.replace('<a class="pricing-cta primary" href="#">Buy</a>', new_button, 1)
        if new_button in card:
            replacements += 1
            print(f"✓ Added data-plan='{plan}' to button {i}")
    
    result_parts.append('<div class="pricing-card' + card)

# Join back together
result = ''.join(result_parts)

# Write the result
with open('pricing.html', 'w') as f:
    f.write(result)

print(f"\nTotal replacements made: {replacements}")

# Verify the changes
import re
matches = re.findall(r'data-plan="[^"]*"', result)
print(f"\nFound {len(matches)} data-plan attributes:")
for match in matches:
    print(f"  {match}")
EOF

echo -e "\n2. Running the fix script..."
python3 fix_pricing_buttons.py

echo -e "\n3. Verifying the changes in the file..."
grep -B 2 -A 2 'data-plan' pricing.html | head -20

echo -e "\n4. Checking the final structure..."
grep -E 'pricing-cta.*Buy' pricing.html | head -10

echo -e "\n5. Cleaning up..."
rm fix_pricing_buttons.py

ENDSSH

echo ""
echo -e "${GREEN}✓ Pricing buttons fixed!${NC}"
echo ""
echo "The buy buttons now have data-plan attributes."
echo "Clear your browser cache and try purchasing a plan at: https://bankcsvconverter.com/pricing.html"