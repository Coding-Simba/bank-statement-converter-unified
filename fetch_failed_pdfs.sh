#!/bin/bash

# Configuration
SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
REMOTE_DIR="/home/ubuntu/bank-statement-converter-unified/backend/failed_pdfs"
LOCAL_DIR="./retrieved_failed_pdfs_$(date +%Y%m%d_%H%M%S)"

echo "Fetching failed PDFs from the last 24 hours..."
echo "=============================================="

# Create local directory
mkdir -p "$LOCAL_DIR"

# Check if server is accessible
if ssh -o ConnectTimeout=5 -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "echo 'Server accessible'" 2>/dev/null; then
    echo "✓ Connected to server"
    
    # Check if failed_pdfs directory exists
    if ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "test -d $REMOTE_DIR" 2>/dev/null; then
        echo "✓ Found failed_pdfs directory on server"
        
        # Fetch metadata file
        echo -n "Downloading metadata file... "
        scp -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/failed_pdfs_metadata.json" "$LOCAL_DIR/" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✓"
        else
            echo "✗ (No metadata file found)"
        fi
        
        # Find and list PDFs from last 24 hours
        echo -e "\nPDFs modified in the last 24 hours:"
        echo "-----------------------------------"
        ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "find $REMOTE_DIR -name '*.pdf' -mtime -1 -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort -r"
        
        # Count PDFs
        PDF_COUNT=$(ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "find $REMOTE_DIR -name '*.pdf' -mtime -1 | wc -l")
        echo -e "\nTotal PDFs found: $PDF_COUNT"
        
        if [ "$PDF_COUNT" -gt 0 ]; then
            echo -e "\nDownloading PDFs..."
            
            # Create a tar archive of PDFs from last 24 hours and extract locally
            ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "cd $REMOTE_DIR && find . -name '*.pdf' -mtime -1 -print0 | tar -czf - --null -T -" | tar -xzf - -C "$LOCAL_DIR/"
            
            if [ $? -eq 0 ]; then
                echo "✓ Successfully downloaded $PDF_COUNT PDFs"
                
                # List downloaded files
                echo -e "\nDownloaded files:"
                ls -la "$LOCAL_DIR"/*.pdf 2>/dev/null | awk '{print "  - " $9 " (" $5 " bytes)"}'
                
                # Create summary
                echo -e "\nCreating summary report..."
                cat > "$LOCAL_DIR/summary.txt" << EOF
Failed PDFs Retrieved from Server
=================================
Date: $(date)
Server: $SERVER_IP
Remote Directory: $REMOTE_DIR
PDFs from last 24 hours: $PDF_COUNT

Files:
$(ls -la "$LOCAL_DIR"/*.pdf 2>/dev/null | awk '{print $9 " - " $5 " bytes - Modified: " $6 " " $7 " " $8}')
EOF
                echo "✓ Summary saved to: $LOCAL_DIR/summary.txt"
            else
                echo "✗ Error downloading PDFs"
            fi
        else
            echo "No PDFs found from the last 24 hours"
        fi
        
    else
        echo "✗ No failed_pdfs directory found on server"
        echo "  The directory should be at: $REMOTE_DIR"
    fi
else
    echo "✗ Cannot connect to server at $SERVER_IP"
    echo ""
    echo "Please check:"
    echo "1. Server is running and accessible"
    echo "2. SSH key is correct at: $KEY_PATH"
    echo "3. Network connection is working"
    echo ""
    echo "You can also manually run these commands when the server is accessible:"
    echo ""
    echo "# Create local directory"
    echo "mkdir -p retrieved_failed_pdfs"
    echo ""
    echo "# Download all failed PDFs from last 24 hours"
    echo "scp -r -i $KEY_PATH $SERVER_USER@$SERVER_IP:$REMOTE_DIR retrieved_failed_pdfs/"
fi

echo -e "\nDone!"