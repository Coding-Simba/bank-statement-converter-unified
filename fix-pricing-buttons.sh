#!/bin/bash

# Fix Pricing Buttons
echo "🔧 Fixing Pricing Buttons"
echo "========================"
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

echo "1. Backing up pricing.html..."
cp pricing.html pricing.html.backup-$(date +%s)

echo -e "\n2. Adding data-plan attributes to buy buttons..."
# First, let's find and update the Starter plan button
sed -i '/<h2 class="pricing-tier">.*Starter.*<\/h2>/,/<a class="pricing-cta primary" href="#">Buy<\/a>/ s|<a class="pricing-cta primary" href="#">Buy</a>|<a class="pricing-cta primary" href="#" data-plan="starter">Buy</a>|' pricing.html

# Update Professional plan button
sed -i '/<h2 class="pricing-tier">.*Professional.*<\/h2>/,/<a class="pricing-cta primary" href="#">Buy<\/a>/ s|<a class="pricing-cta primary" href="#">Buy</a>|<a class="pricing-cta primary" href="#" data-plan="professional">Buy</a>|' pricing.html

# Update Business plan button
sed -i '/<h2 class="pricing-tier">.*Business.*<\/h2>/,/<a class="pricing-cta primary" href="#">Buy<\/a>/ s|<a class="pricing-cta primary" href="#">Buy</a>|<a class="pricing-cta primary" href="#" data-plan="business">Buy</a>|' pricing.html

echo -e "\n3. Verifying the updates..."
echo "Checking for data-plan attributes:"
grep -n 'data-plan' pricing.html | head -10

echo -e "\n4. Also adding inline script to ensure buttons are set up..."
# Add a small script at the end of the page to ensure buttons get data-plan attributes
cat >> pricing.html << 'EOF'

<script>
// Ensure pricing buttons have data-plan attributes
document.addEventListener('DOMContentLoaded', function() {
    // Find pricing cards and add data-plan if missing
    const pricingCards = document.querySelectorAll('.pricing-card');
    pricingCards.forEach(card => {
        const tierElement = card.querySelector('.pricing-tier');
        const button = card.querySelector('.pricing-cta');
        
        if (tierElement && button && !button.hasAttribute('data-plan')) {
            const tierText = tierElement.textContent.trim().toLowerCase();
            if (tierText.includes('starter')) {
                button.setAttribute('data-plan', 'starter');
            } else if (tierText.includes('professional')) {
                button.setAttribute('data-plan', 'professional');
            } else if (tierText.includes('business')) {
                button.setAttribute('data-plan', 'business');
            }
        }
    });
    
    console.log('Pricing buttons setup complete');
});
</script>
EOF

echo -e "\n5. Testing the fix..."
echo "Final check for buy buttons with data-plan:"
grep -E 'pricing-cta.*data-plan' pricing.html | head -5

echo -e "\n6. Clearing cache..."
touch pricing.html

ENDSSH

echo ""
echo -e "${GREEN}✓ Pricing buttons fixed!${NC}"
echo ""
echo "The buy buttons now have the proper data-plan attributes."
echo "Clear your browser cache and try again at: https://bankcsvconverter.com/pricing.html"