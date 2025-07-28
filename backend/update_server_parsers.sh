#!/bin/bash
# Script to update server parsers and remove dummy references

echo "Updating server parsers..."

# Remove lines containing dummy parser imports from universal_parser.py
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "cd /home/ubuntu/bank-statement-converter-unified/backend && sed -i '/from dummy_pdf_parser/d' universal_parser.py"
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "cd /home/ubuntu/bank-statement-converter-unified/backend && sed -i '/DUMMY_PARSER_AVAILABLE = True/d' universal_parser.py"
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "cd /home/ubuntu/bank-statement-converter-unified/backend && sed -i 's/DUMMY_PARSER_AVAILABLE = False/DUMMY_PARSER_AVAILABLE = False/' universal_parser.py"

# Update universal_parser_enhanced.py
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "cd /home/ubuntu/bank-statement-converter-unified/backend && sed -i '/from dummy_pdf_parser/d' universal_parser_enhanced.py"
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "cd /home/ubuntu/bank-statement-converter-unified/backend && sed -i '/parse_dummy_pdf/d' universal_parser_enhanced.py"

# Update universal_parser_with_custom_banks.py
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "cd /home/ubuntu/bank-statement-converter-unified/backend && sed -i '/from dummy_pdf_parser/d' universal_parser_with_custom_banks.py"
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "cd /home/ubuntu/bank-statement-converter-unified/backend && sed -i \"/dummy.*{/,/}/d\" universal_parser_with_custom_banks.py"

# Restart the backend service
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "sudo systemctl restart bank-statement-backend"

echo "Server parsers updated and backend restarted"